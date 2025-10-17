# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-09
# description: 采集公众号文章详情

import json
import logging
import re
from typing import List, Optional

import demjson3
from parsel import Selector
from pydantic import Field

from news_crawler.core import (
    BaseNewsCrawler,
    ContentItem,
    ContentType,
    NewsItem,
    NewsMetaInfo,
    RequestHeaders as BaseRequestHeaders,
)
from news_crawler.core.fetchers import CurlCffiFetcher, FetchRequest


FIXED_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
# 微信公众号不带cookie也可以访问，但是不确定是否爬取多了会有影响，这里可以填写自用cookie
FIXED_COOKIE = "RK=KfsE+4gSss;rewardsn=;ptcz=13cd54e3b6207f8e605c9a70630509394ef82a923e405fcf0c7c562de1b6e986;wxtokenkey=777"

logger = logging.getLogger(__name__)


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(
        default=FIXED_USER_AGENT, alias="User-Agent"
    )
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


def _convert_js_obj_to_json(js_obj_str: str) -> str:
    """将JavaScript对象字符量转换为标准JSON格式

    Args:
        js_obj_str (str): JavaScript对象字面量字符串

    Returns:
        str: 标准JSON格式字符串
    """
    try:
        # 首先尝试直接解析JSON
        json.loads(js_obj_str)
        return js_obj_str
    except json.JSONDecodeError:
        try:
            # 如果直接解析失败，则使用demjson3进行转换
            js_obj_str = js_obj_str.replace(" * 1", "")
            parsed_data = demjson3.decode(js_obj_str)
            print(parsed_data)
            return json.dumps(parsed_data, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to convert JS object to JSON: {str(e)}")
            # 如果转换失败，返回原始字符串
            return js_obj_str


def _parse_ssr_data(html: str) -> Optional[dict]:
    """解析SSR数据

    Args:
        html (str): 页面HTML内容

    Returns:
        Optional[dict]: 解析后的SSR数据，解析失败返回None
    """
    if "window.__QMTPL_SSR_DATA__" not in html:
        return None

    ssr_data_match = re.search(r"window\.__QMTPL_SSR_DATA__=(.+);</script>", html)
    if not ssr_data_match:
        return None

    try:
        ssr_data_str = _convert_js_obj_to_json(ssr_data_match.group(1).strip())
        return json.loads(ssr_data_str)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to parse SSR data: {str(e)}")
        return None


def _parse_ssr_image_list(html: str) -> List[ContentItem]:
    """解析SSR渲染的图片列表

    Args:
        html (str): 页面HTML内容

    Returns:
        List[ContentItem]: 图片列表
    """
    contents: List[ContentItem] = []
    regex_compile = re.compile(
        r"window\.picture_page_info_list = (\[[\s\S]*?\])\.slice\(0,\s*20\);", re.DOTALL
    )
    picture_list_match = regex_compile.search(html)
    if not picture_list_match:
        return []
    try:
        js_image_list_str = picture_list_match.group(1)
        # 直接用正则提取cdn_url
        cdn_urls = re.findall(r"cdn_url:\s*'([^']+)'", js_image_list_str)
        for url in cdn_urls:
            # 替换转义字符
            url = url.replace("\\x26amp;", "&")
            contents.append(ContentItem(type=ContentType.IMAGE, content=url))
        return contents
    except Exception as e:
        logger.error(f"Failed to parse SSR image list: {str(e)}")
        return []


class WechatContentParser:
    """
    微信公众号文章正文内容解析器
    """

    def __init__(self):
        """初始化微信公众号文章正文内容解析器"""
        self._contents: List[ContentItem] = []

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        """解析公众号文章详情页内容，保持段落结构
           微信公众号的由于出在多编辑器的情况，所以解析比较复杂

        Args:
            html_content (str): 公众号文章内容

        Returns:
            List[ContentItem]: 公众号章内容，每个段落作为独立的ContentItem
        """
        self._contents = []
        # 检查是否是SSR渲染的页面
        if "window.__QMTPL_SSR_DATA__" in html_content:
            return self.parse_ssr_content(html_content)

        selector = Selector(text=html_content)

        content_node = selector.xpath('//div[@id="js_content"]')
        if not content_node:
            return self._contents

        # 处理所有直接子节点
        for node in content_node.xpath("./*"):
            self._process_content_node(node)

        contents = [item for item in self._contents if item.content.strip()]
        return self._remove_duplicate_contents(contents)

    def parse(self, html_content: str) -> List[ContentItem]:
        """兼容 ContentParser 协议。"""
        return self.parse_html_to_news_content(html_content)

    def _remove_duplicate_contents(
        self, contents: List[ContentItem]
    ) -> List[ContentItem]:
        """移除重复内容

        Args:
            contents (List[ContentItem]): 内容列表

        Returns:
            List[ContentItem]: 去重后的内容列表
        """
        # 判个重
        unique_contents = []
        seen_contents = set()
        for item in contents:
            content_key = f"{item.type}:{item.content}"
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique_contents.append(item)

        return unique_contents

    @staticmethod
    def _process_media(node: Selector) -> Optional[ContentItem]:
        """处理媒体内容(图片和视频)

        Args:
            node (Selector): 节点

        Returns:
            Optional[ContentItem]: 媒体内容
        """
        if node.root.tag == "img":
            img_url = node.attrib.get("src", "") or node.attrib.get("data-src", "")
            if img_url:
                return ContentItem(type=ContentType.IMAGE, content=img_url)
        elif node.root.tag in ["video", "iframe"]:
            video_url = node.attrib.get("src", "")
            if video_url:
                return ContentItem(type=ContentType.VIDEO, content=video_url)

        return None

    @staticmethod
    def _process_text_block(node: Selector) -> Optional[str]:
        """处理文本块，返回处理后的文本

        Args:
            node (Selector): 节点

        Returns:
            Optional[str]: 处理后的文本
        """
        # 跳过不需要的标签
        if node.root.tag in ["script", "style"]:
            return None

        # 获取当前节点的文本
        text = node.xpath("string(.)").get("").strip()
        if not text:
            return None

        return text

    def _process_list_item(self, node: Selector) -> Optional[str]:
        """处列表项，添加适当的前缀

        Args:
            node (Selector): 节点

        Returns:
            Optional[str]: 处理后的文本
        """
        text = self._process_text_block(node)
        if not text:
            return None

        # 如果是有序列表项，尝试获取序号
        if node.xpath("./ancestor::ol"):
            # 计算当前li是ol中的第几个
            position = len(node.xpath("./preceding-sibling::li")) + 1
            return f"{position}. {text}"
        else:
            # 无序列表项添加符号
            return f"• {text}"

    def _process_content_node(self, node: Selector):
        """处理内容节点

        Args:
            node (Selector): 节点
        """
        # 对于section等容器标签，处理其子元素
        if node.root.tag in ["section", "div", "article", "blockquote"]:
            # 如果section、div、article中有直接文本，则直接添加
            if node.xpath("./text()").get("").strip():
                self._contents.append(
                    ContentItem(
                        type=ContentType.TEXT,
                        content=node.xpath("./text()").get("").strip(),
                    )
                )

            # 递归处理子元素
            for child in node.xpath("./*"):
                self._process_content_node(child)
            return

        # 处理标题内容
        if node.root.tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        # 尽可能的还原段落中的罗列陈述（通常是在富文本中编辑器的表现为ul、ol）
        if node.root.tag in ["ul", "ol"]:
            list_items = []
            for li in node.xpath(".//li"):
                item_text = self._process_list_item(li)
                if item_text:
                    list_items.append(item_text)
            if len(list_items) > 0:
                for item in list_items:
                    self._contents.append(
                        ContentItem(type=ContentType.TEXT, content=item)
                    )
            return

        # 另外也有可能li这种标签它不再ul/ol中，而是单独的列表项，也补偿一下吧
        if node.root.tag == "li":
            text = self._process_list_item(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        # 检查是否是媒体内容
        media_content = self._process_media(node)
        if media_content:
            self._contents.append(media_content)
            return

        # 处理段落内容
        if node.root.tag == "p":
            # 有一些富文本编辑的设定会在将img标签包括在p标签中，这里做一个补偿。
            if (
                node.xpath(".//img")
                or node.xpath(".//video")
                or node.xpath(".//iframe")
            ):
                maybe_exist_nodes = node.xpath(".//img | .//video | .//iframe")
                for maybe_exist_node in maybe_exist_nodes:
                    media_content = self._process_media(maybe_exist_node)
                    if media_content:
                        self._contents.append(media_content)

            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

            # 处理span标签
        if node.root.tag in ["span", "strong"]:
            if (
                node.xpath(".//img")
                or node.xpath(".//video")
                or node.xpath(".//iframe")
            ):
                maybe_exist_nodes = node.xpath(".//img | .//video | .//iframe")
                for maybe_exist_node in maybe_exist_nodes:
                    media_content = self._process_media(maybe_exist_node)
                    if media_content:
                        self._contents.append(media_content)

            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        # 处理a标签
        if node.root.tag == "a":
            # 有些a标签中包含图片，这里做一个补偿
            if node.xpath(".//img"):
                for img_node in node.xpath(".//img"):
                    media_content = self._process_media(img_node)
                    if media_content:
                        self._contents.append(media_content)

            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

    def parse_ssr_content(self, html_content: str) -> List[ContentItem]:
        """解析SSR渲染的页面内容

        Args:
            html_content (str): 页面HTML内容

        Returns:
            List[ContentItem]: 解析后的内容列表
        """
        # 提取SSR数据
        contents = []
        contents.extend(_parse_ssr_image_list(html_content))
        ssr_data_dict = _parse_ssr_data(html_content)

        if ssr_data_dict:
            try:
                # 有的xhs风格的公众号页面，没有desc，只有title，要兼容一下。
                desc = ssr_data_dict.get("desc")
                title = ssr_data_dict.get("title")
                final_desc = desc or title
                if final_desc:
                    desc_list = final_desc.split("\n")
                    for desc_item in desc_list:
                        if not desc_item:
                            continue
                        contents.append(
                            ContentItem(
                                type=ContentType.TEXT, content=desc_item.strip()
                            )
                        )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse SSR data: {str(e)}")

        return contents


class WeChatNewsCrawler(BaseNewsCrawler):
    """微信公众平台文章爬虫实现。"""

    headers_model = RequestHeaders
    fetch_strategy = CurlCffiFetcher

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
        fetcher: Optional[CurlCffiFetcher] = None,
    ):
        super().__init__(new_url, save_path, headers=headers, fetcher=fetcher)
        self._content_parser = WechatContentParser()

    @property
    def get_base_url(self) -> str:
        """保留与旧版本兼容的基础 URL 属性。"""
        return "https://mp.weixin.qq.com"

    def get_article_id(self) -> str:
        try:
            return self.new_url.split("/s/")[1].split("?")[0]
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ValueError("解析文章ID失败，请检查URL是否正确") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.impersonate = "chrome"
        return request

    @staticmethod
    def _parse_publish_time(html_content: str) -> str:
        pattern = r"var createTime = '(\d{4}-\d{2}-\d{2} \d{2}:\d{2})';"
        match = re.search(pattern, html_content)
        return match.group(1) if match else ""

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        self.logger.info("Start to parse html to news meta, news_url: %s", self.new_url)

        ssr_data = _parse_ssr_data(html_content)
        if ssr_data:
            author_name = ssr_data.get("nick_name", "")
            create_time_match = re.search(
                r"var\s+createTime\s*=\s*'([^']+)'\s*;", html_content
            )
            publish_time = create_time_match.group(1) if create_time_match else ""

            return NewsMetaInfo(
                publish_time=publish_time.strip(),
                author_name=author_name.strip(),
                author_url="",
            )

        sel = Selector(text=html_content)
        publish_time = self._parse_publish_time(html_content)
        wechat_name = sel.xpath("string(//span[@id='profileBt'])").get("").strip() or ""
        wechat_author_url = (
            sel.xpath(
                "string(//div[@id='meta_content']/span[@class='rich_media_meta rich_media_meta_text'])"
            )
            .get("")
            .strip()
            or ""
        )
        author_name = f"{wechat_name} - {wechat_author_url}".strip("- ")

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url="",
        )

    def parse_content(self, html: str) -> NewsItem:
        ssr_data = _parse_ssr_data(html)
        if ssr_data:
            title = (ssr_data.get("title") or "").strip()
        else:
            selector = Selector(text=html)
            title = (
                selector.xpath('//h1[@id="activity-name"]/text()').get("") or ""
            ).strip()

        if not title:
            raise ValueError("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = list(self._content_parser.parse(html))

        return self.compose_news_item(
            title=title,
            meta_info=meta_info,
            contents=contents,
        )

    def validate_item(self, news_item: NewsItem) -> None:
        super().validate_item(news_item)
        if not news_item.title:
            raise ValueError("Failed to get title")


if __name__ == "__main__":
    article_url1 = "https://mp.weixin.qq.com/s/ebMzDPu2zMT_mRgYgtL6eQ"
    article_url2 = "https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw"
    article_url3 = "https://mp.weixin.qq.com/s/zCNL9Rgoj25cWgQo7HPupw"
    article_url4 = "https://mp.weixin.qq.com/s/Ig44D56c11qOcZxlRWdo1w"
    article_url5 = "https://mp.weixin.qq.com/s/ZzWDIt3WZGMmxoC4M1Fo6w"
    article_url6 = "https://mp.weixin.qq.com/s/1M_H0Q83z73LumchZ03zwA"
    article_url7 = "https://mp.weixin.qq.com/s/q2ibCgE9Pr3jeRTtTNLOjQ"
    article_url8 = "https://mp.weixin.qq.com/s/GFcXLkqMvyuTpNWhrSPq6g"

    # 小红书风格的新公众号页面（页面结构完全不一样，使用的是vue的ssr渲染的page，需要单独解析）
    article_url9 = "https://mp.weixin.qq.com/s/RUHJpS9w3RhuhEm94z-1Kw"
    article_url10 = "https://mp.weixin.qq.com/s/deS-7QqTWyat-l5Ex39ZDA"
    for article_url in [
        article_url1,
        article_url2,
        article_url3,
        article_url4,
        article_url5,
        article_url6,
        article_url7,
        article_url8,
        article_url9,
    ]:
        crawler = WeChatNewsCrawler(article_url, save_path="data/")
        crawler.run()
