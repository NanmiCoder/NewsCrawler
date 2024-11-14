# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-15
# description: lennysnewsletter新闻详情爬虫

import json
import logging
import os
import pathlib
from enum import Enum
from typing import List, Optional

import requests
from parsel import Selector
from pydantic import BaseModel, Field
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

FIXED_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
FIXED_COOKIE = "ab_experiment_sampled=%22false%22; ab_testing_id=%22a5afcd47-8198-4089-bb2a-ba8628b6da67%22; _ga=GA1.1.462650913.1731604007; ajs_anonymous_id=%22f28ff03f-6d49-40d4-8b92-7a9e0e0f7d21%22; ajs_anonymous_id=%22f28ff03f-6d49-40d4-8b92-7a9e0e0f7d21%22; cookie_storage_key=f6fcf3b9-e78e-4632-a1d3-619ddf37f24a; __cf_bm=ZwuFiT7hXwcGTacEb2.nrvynAmW2CQRRCNGZuxDVwKI-1731625491-1.0.1.1-ynp_03wP9EFEDiUBZZsjvUb6GSWyCLp31QV3BxSnQ8mKa9ZYLmkeTbbLFYJWguPdsJcmvpxtwJvfUreruASOXg; visit_id=%7B%22id%22%3A%224d9a1e8c-6a1e-4ede-a2bc-e7423c481253%22%2C%22timestamp%22%3A%222024-11-14T23%3A04%3A54.150Z%22%7D; _gcl_au=1.1.2085925695.1731625495; _ga_0V8B24EKGY=GS1.1.1731625493.2.1.1731625631.0.0.0; AWSALBTG=HOU6d99orSPuxcqgmTXGKJ84//TsxR11Uc12QiUerjTqWhnVzPX96psvfS2R1PnRCn/yvLnHE3yKmiguuwwSkLIg66lQy0edam8QRtR+yMuS1wmXZcUwe2/LuqBgzh6FHAnkPDIW8erxGQGSXZjBji2k+/ksAXLwEteoi5ORzH2+; AWSALBTGCORS=HOU6d99orSPuxcqgmTXGKJ84//TsxR11Uc12QiUerjTqWhnVzPX96psvfS2R1PnRCn/yvLnHE3yKmiguuwwSkLIg66lQy0edam8QRtR+yMuS1wmXZcUwe2/LuqBgzh6FHAnkPDIW8erxGQGSXZjBji2k+/ksAXLwEteoi5ORzH2+; _dd_s=rum=0&expire=1731626983227"

logger = logging.getLogger("LennysNewsletterCrawler")


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
    subtitle: str = Field(default="", title="新闻副标题")
    news_url: str = Field(default="", title="新闻链接")
    news_id: str = Field(default="", title="新闻ID")
    meta_info: NewsMetaInfo = Field(default=NewsMetaInfo(), title="新闻元信息")
    contents: List[ContentItem] = Field(default=[], title="新闻内容")
    texts: List[str] = Field(default=[], title="新闻正文")
    images: List[str] = Field(default=[], title="新闻图片")
    videos: Optional[List[str]] = Field(default=[], title="新闻视频")


class LennysNewsletterContentParser:
    """
    新闻详情页内容解析器
    """

    def __init__(self):
        """初始化新闻详情页内容解析器"""
        self._contents: List[ContentItem] = []

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        """解析新闻详情页内容，保持段落结构

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            List[ContentItem]: 新闻详情页内容，每个段落作为独立的ContentItem
        """
        selector = Selector(text=html_content)

        content_node = selector.xpath("//div[@class='available-content']")
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
            # 有些图片是懒加载的，所以使用优先data-lazy-src
            img_url = node.attrib.get("data-lazy-src", "") or node.attrib.get("src", "")
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
        # 处理前端的 &ZeroWidthSpace; 字符 &nbsp;
        return text.replace("\u200b", "")

    def _process_list_item(self, node: Selector) -> Optional[str]:
        """处理列表项，添加适当的前缀

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
        if node.root.tag in ["section", "div", "blockquote", "figure"]:
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


class LennysNewsletterCrawler:
    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: RequestHeaders = RequestHeaders(),
    ):
        """初始化LennysNewsletter新闻详情爬虫

        Args:
            new_url (str): 新闻详情页url
            save_path (str, optional): 保存路径. Defaults to "".
            headers (RequestHeaders, optional): 请求头. Defaults to RequestHeaders().
        """
        init_logger()
        self.new_url = new_url
        self.save_path = save_path
        self.save_file_name = self.get_save_json_path()
        self.headers = headers.model_dump()
        self._content_parser = LennysNewsletterContentParser()

    @property
    def get_base_url(self) -> str:
        """获取新闻详情页基础url

        Returns:
            str: 新闻详情页基础url
        """
        return "https://www.lennysnewsletter.com/"

    @property
    def get_article_id(self) -> str:
        """获取新闻详情页文章id
            eg: https://www.lennysnewsletter.com/p/how-duolingo-reignited-user-growth

        Returns:
            str: 新闻详情页文章id: how-duolingo-reignited-user-growth
        """
        try:
            news_id = self.new_url.split("?")[0].split("/")[-1]
            if news_id.endswith("/"):
                news_id = news_id[:-1]
            return news_id
        except Exception as e:
            raise Exception(f"解析文章ID失败，请检查URL是否正确")

    def get_save_json_path(self) -> str:
        """获取新闻详情页保存的json文件路径

        Returns:
            str: 新闻详情页保存的json文件路径
        """
        return os.path.join(self.save_path, f"{self.get_article_id}.json")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def fetch_content(self) -> str:
        """获取新闻详情页内容
           该方法会有重试机制，如果状态码不是200，则重试3次每次等待1秒
        Raises:
            Exception: 获取内容失败

        Returns:
            str: 新闻详情页内容
        """
        logger.info(f"Start to fetch content from {self.new_url}")
        response = requests.get(self.new_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch content: {response.status_code}")
        response.encoding = "utf-8"
        return response.text

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        """解析新闻详情页元信息

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            NewsMetaInfo: 新闻元信息
        """
        logger.info(f"Start to parse html to news meta, news_url: {self.new_url}")
        sel = Selector(text=html_content)

        author_xpath = "//div[@class='post-header']//div[contains(@class, 'profile-hover-card-target')]/a"
        publish_time = (
            sel.xpath(
                "//div[@class='post-header']//div[@class='pencraft pc-display-flex pc-gap-4 pc-reset']/div/text()"
            ).get()
            or ""
        )
        author_name = sel.xpath(author_xpath + "/text()").get() or ""
        author_url = sel.xpath(author_xpath + "/@href").get() or ""

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url=author_url.strip(),
        )

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        """解析新闻详情页内容

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            List[ContentItem]: 新闻内容
        """
        return self._content_parser.parse_html_to_news_content(html_content)

    def parse_content(self, html: str) -> NewsItem:
        """解析新闻详情页内容

        Args:
            html (str): 新闻详情页内容

        Returns:
            NewsItem: 新闻详情
        """
        result = NewsItem()
        selector = Selector(text=html)

        # 获取标题
        title = selector.xpath("//h1/text()").get()
        if not title:
            raise Exception("Failed to get title")

        # 获取副标题
        subtitle = selector.xpath("//h3/text()").get() or ""

        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)

        result.title = title
        result.subtitle = subtitle
        result.news_url = self.new_url
        result.news_id = self.get_article_id
        result.meta_info = meta_info
        result.contents = contents

        # 提取文本、图片、视频放到单独的列表中，备用
        result.texts = [
            content.content
            for content in contents
            if content.type == ContentType.TEXT and content.content != ""
        ]
        result.images = [
            content.content
            for content in contents
            if content.type == ContentType.IMAGE and content.content != ""
        ]
        result.videos = [
            content.content
            for content in contents
            if content.type == ContentType.VIDEO and content.content != ""
        ]

        return result

    def save_as_json(self, news_item: NewsItem):
        """保存新闻详情为json文件

        Args:
            news_item (NewsItem): 新闻详情
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
    article_url1 = (
        "https://www.lennysnewsletter.com/p/how-duolingo-reignited-user-growth"
    )
    article_url2 = "https://www.lennysnewsletter.com/p/on-being-funny-at-work"
    for article_url in [article_url1, article_url2]:
        crawler = LennysNewsletterCrawler(article_url, save_path="data/")
        crawler.run()
