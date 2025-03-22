# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-09
# description: 采集公众号文章详情

import json
import logging
import os
import pathlib
import re
from enum import Enum
from typing import List, Optional

import requests
import demjson3
from parsel import Selector
from pydantic import BaseModel, Field
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed


FIXED_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
# 微信公众号不带cookie也可以访问，但是不确定是否爬取多了会有影响，这里可以填写自用cookie
FIXED_COOKIE = "RK=KfsE+4gSss;rewardsn=;ptcz=13cd54e3b6207f8e605c9a70630509394ef82a923e405fcf0c7c562de1b6e986;wxtokenkey=777"

logger = logging.getLogger("WeChatNewsCrawler")


def init_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class RequestHeaders(BaseModel):
    user_agent: str = Field(
        default=FIXED_USER_AGENT, title="User-Agent", alias="User-Agent"
    )
    cookie: str = Field(default=FIXED_COOKIE, title="Cookie", alias="Cookie")


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ContentItem(BaseModel):
    type: ContentType = Field(default=ContentType.TEXT, title="内容类型")
    content: str = Field(default="", title="内容")
    desc: str = Field(default="", title="描述")


class NewsMetaInfo(BaseModel):
    author_name: str = Field(default="", title="作者")
    author_url: str = Field(default="", title="作者链接")
    publish_time: str = Field(default="", title="发布时间")


class NewsItem(BaseModel):
    title: str = Field(default="", title="新闻标题")
    news_url: str = Field(default="", title="新闻链接")
    news_id: str = Field(default="", title="新闻ID")
    meta_info: NewsMetaInfo = Field(default=NewsMetaInfo(), title="新闻元信息")
    contents: List[ContentItem] = Field(default=[], title="新闻内容")
    texts: List[str] = Field(default=[], title="新闻正文")
    images: List[str] = Field(default=[], title="新闻图片")
    videos: Optional[List[str]] = Field(default=[], title="新闻视频")


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


class WeChatNewsCrawler:
    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: RequestHeaders = RequestHeaders(),
    ):
        """初始化公众号文章详情爬虫

        Args:
            new_url (str): 公众号章详情页url
            save_path (str, optional): 保存路径. Defaults to "".
            headers (RequestHeaders, optional): 请求头. Defaults to RequestHeaders().
        """
        init_logger()
        self.new_url = new_url
        self.save_path = save_path
        self.save_file_name = self.get_save_json_path()
        self.headers = headers.model_dump()
        self._content_parser = WechatContentParser()

    @property
    def get_base_url(self) -> str:
        """获取公众号详情页基础url

        Returns:
            str: 公众号详情页基础url
        """
        return "https://mp.weixin.qq.com"

    @property
    def get_article_id(self) -> str:
        """获取公众号详情页文章id
            eg: https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw?may_be_params=test
                return: 3Sr6nYjE1RF05siTblD2mw
        Returns:
            str: 公众号详情页文章id
        """
        try:
            news_id = self.new_url.split("/s/")[1].split("?")[0]
            return news_id
        except Exception as e:
            raise Exception(f"解析文章ID失败，请检查URL是否正确")

    def get_save_json_path(self) -> str:
        """获取公众号文章详情页保存的json文件路径

        Returns:
            str: 众号文章详情页保存的json文件路径
        """
        return os.path.join(self.save_path, f"{self.get_article_id}.json")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def fetch_content(self) -> str:
        """获取公众号文章详情页内容
           该方法会有重试机制，如果状态码不是200，则重试3次每次等1秒
        Raises:
            Exception: 获取内容失败

        Returns:
            str: 公众号文章详情页内容
        """
        logger.info(f"Start to fetch content from {self.new_url}")
        # 使用curl_cffi库请求 模拟chrome的ssl指纹
        from curl_cffi import requests

        response = requests.get(
            self.new_url, headers=self.headers, impersonate="chrome"
        )
        # response = requests.get(self.new_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch content: {response.status_code}")
        response.encoding = "utf-8"
        return response.text

    @staticmethod
    def _parse_publish_time(html_content: str) -> str:
        """解析公众号文章详情页发布时间

        Args:
            html_content (str): 公众号文章详情页内容

        Returns:
            str: 公众号文章详情发布时间
        """
        js_re_pattern = r"var createTime = '(\d{4}-\d{2}-\d{2} \d{2}:\d{2})';"
        match = re.search(js_re_pattern, html_content)
        if match:
            return match.group(1)
        return ""

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        """解析公众号文章详情页元信息"""
        logger.info(f"Start to parse html to news meta, news_url: {self.new_url}")

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
                author_url="",  # SSR页面中没有作者链接
            )

        # 原有的解析逻辑
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
        author_name = f"{wechat_name} - {wechat_author_url}"

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url="",
        )

    def parse_content(self, html: str) -> NewsItem:
        """解析公众号文章内容"""
        result = NewsItem()
        title = ""  # 初始化title变量

        ssr_data = _parse_ssr_data(html)
        if ssr_data:
            title = ssr_data.get("title", "")
        else:
            # 原有的解析逻辑
            selector = Selector(text=html)
            title = selector.xpath('//h1[@id="activity-name"]/text()').get("")

        if not title:
            raise Exception("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = self._content_parser.parse_html_to_news_content(html)

        result.title = title.strip()
        result.news_url = self.new_url
        result.news_id = self.get_article_id
        result.meta_info = meta_info
        result.contents = contents

        # 提取文本、图片、视频放到列表中，备用
        result.texts = [
            content.content for content in contents if content.type == ContentType.TEXT
        ]
        result.images = [
            content.content for content in contents if content.type == ContentType.IMAGE
        ]
        result.videos = [
            content.content for content in contents if content.type == ContentType.VIDEO
        ]

        return result

    def save_as_json(self, news_item: NewsItem):
        """保存公众号文章详情为json文件

        Args:
            news_item (NewsItem): 公众号文章详情
        """
        pathlib.Path(self.save_path).mkdir(parents=True, exist_ok=True)
        with open(self.save_file_name, "w", encoding="utf-8") as f:
            json.dump(news_item.model_dump(), f, ensure_ascii=False, indent=4)

    def run(self):
        """运行爬虫"""

        @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
        def retry_fetch_content():
            html = self.fetch_content()
            news_item = self.parse_content(html)
            logger.info(
                f"parse content from {self.new_url}, result: {news_item}, we will check if the content is empty."
            )
            if len(news_item.texts) == 0 and len(news_item.contents) == 0:
                logger.error(
                    f"Failed to get content: {news_item.title}, and we will retry get content ..."
                )
                raise Exception("Failed to get content")
            self.save_as_json(news_item)
            logger.info(f"Success to get content from {self.new_url}")

        try:
            retry_fetch_content()
        except RetryError as e:
            logger.error(
                f"Failed to get content from {self.new_url}, error: {e}, retry times: {e.last_attempt.attempt_number}"
            )
            raise e


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
