# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2025-10-17
# description: 采集网易新闻详情

import json
import logging
import os
import pathlib
from enum import Enum
from typing import List, Optional

from parsel import Selector
from pydantic import BaseModel, Field
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

## 网易的cookies不需要登录态，随便打开一个网易新闻提取cookies即可
FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = ''

logger = logging.getLogger("NeteaseNewsCrawler")


def init_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class RequestHeaders(BaseModel):
    user_agent: str = Field(default=FIXED_USER_AGENT, title="User-Agent", alias="User-Agent")
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


class NeteaseNewsCrawler:
    def __init__(self, new_url: str, save_path: str = "data/", headers: RequestHeaders = RequestHeaders()):
        """初始化网易新闻详情爬虫

        Args:
            new_url (str): 新闻详情页url
            save_path (str, optional): 保存路径. Defaults to "data/".
            headers (RequestHeaders, optional): 请求头. Defaults to RequestHeaders().
        """
        init_logger()
        self.new_url = new_url
        self.save_path = save_path
        self.save_file_name = self.get_save_json_path()
        self.headers = headers.model_dump()

    @property
    def get_base_url(self) -> str:
        """获取新闻详情页基础url

        Returns:
            str: 新闻详情页基础url
        """
        return "https://www.163.com"

    @property
    def get_article_id(self) -> str:
        """获取新闻详情页文章id
            eg: https://www.163.com/news/article/KC12OUHK000189FH.html
                return: KC12OUHK000189FH
        Returns:
            str: 新闻详情页文章id
        """
        try:
            # Extract ID from URL pattern: /article/[ID].html
            news_id = self.new_url.split("/article/")[1].split(".html")[0].split("?")[0]
            return news_id
        except Exception as e:
            raise Exception(f"解析文章ID失败，请检查URL是否正确: {e}")

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
        # 使用curl_cffi库请求 模拟chrome的ssl指纹
        from curl_cffi import requests as cffi_requests

        response = cffi_requests.get(
            self.new_url, headers=self.headers, impersonate="chrome"
        )
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

        # Extract publish time from meta tag or post_info
        publish_time = sel.xpath("//html/@data-publishtime").get() or ""

        # Extract author from post_author section
        author_text = sel.xpath("//div[@class='post_author']/text()").getall()
        author_name = ""
        for text in author_text:
            text = text.strip()
            if "责任编辑：" in text:
                author_name = text.replace("责任编辑：", "").strip()
                break

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name,
            author_url="",
        )

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        """解析新闻详情页内容

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            List[ContentItem]: 新闻内容
        """
        contents = []
        selector = Selector(text=html_content)

        # NetEase news content is in div.post_body
        elements = selector.xpath('//div[@class="post_body"]/*')
        for element in elements:
            # Handle paragraph text
            if element.root.tag == 'p':
                text = element.xpath('string()').get('').strip()
                if text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

            # Handle images - they can be in p, div, or standalone img tags
            if element.root.tag in ['img', 'div', 'p']:
                if element.root.tag == 'img':
                    img_url = element.xpath('./@src').get('')
                    if img_url:
                        contents.append(ContentItem(type=ContentType.IMAGE, content=img_url, desc=img_url))
                else:
                    img_urls = element.xpath(".//img/@src").getall()
                    for img_url in img_urls:
                        if img_url:
                            contents.append(ContentItem(type=ContentType.IMAGE, content=img_url, desc=img_url))

            # Handle videos
            if element.root.tag == 'video':
                video_url = element.xpath('./@src').get('')
                if video_url:
                    contents.append(ContentItem(type=ContentType.VIDEO, content=video_url, desc=video_url))

        return contents

    def parse_content(self, html: str) -> NewsItem:
        """解析新闻详情页内容

        Args:
            html (str): 新闻详情页内容

        Returns:
            NewsItem: 新闻详情
        """
        result = NewsItem()
        selector = Selector(text=html)

        # Get title from h1.post_title
        title = selector.xpath('//h1[@class="post_title"]/text()').get('')
        if not title:
            raise Exception("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)

        result.title = title.strip()
        result.news_url = self.new_url
        result.news_id = self.get_article_id
        result.meta_info = meta_info
        result.contents = contents

        # 提取文本、图片、视频放到单独的列表中，备用
        result.texts = [content.content for content in contents if content.type == ContentType.TEXT]
        result.images = [content.content for content in contents if content.type == ContentType.IMAGE]
        result.videos = [content.content for content in contents if content.type == ContentType.VIDEO]

        return result

    def save_as_json(self, news_item: NewsItem):
        """保存新闻详情为json文件

        Args:
            news_item (NewsItem): 新闻详情
        """
        pathlib.Path(self.save_path).mkdir(parents=True, exist_ok=True)
        with open(self.save_file_name, 'w', encoding='utf-8') as f:
            json.dump(news_item.model_dump(), f, ensure_ascii=False, indent=4)

    def run(self) -> NewsItem:
        """运行爬虫

        Returns:
            NewsItem: 新闻详情
        """

        @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
        def retry_fetch_content():
            html = self.fetch_content()
            news_item = self.parse_content(html)
            if len(news_item.texts) == 0 and len(news_item.contents) == 0:
                logger.error(f"Failed to get content: {news_item.title}, and we will retry get content ...")
                raise Exception("Failed to get content")
            self.save_as_json(news_item)
            logger.info(f"Success to get content from {self.new_url}")
            return news_item

        try:
            return retry_fetch_content()
        except RetryError as e:
            logger.error(
                f"Failed to get content from {self.new_url}, error: {e}, retry times: {e.last_attempt.attempt_number}")
            raise e


if __name__ == "__main__":
    # Test URL
    article_url = "https://www.163.com/news/article/KC12OUHK000189FH.html"
    crawler = NeteaseNewsCrawler(article_url, save_path="data/")
    result = crawler.run()
    print(f"Successfully crawled: {result.title}")
    print(f"Text paragraphs: {len(result.texts)}")
    print(f"Images: {len(result.images)}")
