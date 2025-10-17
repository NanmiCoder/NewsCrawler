# -*- coding: utf-8 -*-
from __future__ import annotations

# author: relakkes@gmail.com
# date: 2025-10-18
# description: 采集腾讯新闻详情

import json
import re
from typing import List, Optional

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

# 腾讯新闻的cookies不需要登录态，随便打开一个腾讯新闻提取cookies即可
FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = ''


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class TencentNewsCrawler(BaseNewsCrawler):
    fetch_strategy = CurlCffiFetcher

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
        fetcher: Optional[CurlCffiFetcher] = None,
    ):
        """初始化腾讯新闻详情爬虫

        Args:
            new_url (str): 新闻详情页url
            save_path (str, optional): 保存路径. Defaults to "data/".
            headers (RequestHeaders, optional): 请求头. Defaults to RequestHeaders().
        """
        super().__init__(new_url, save_path, headers=headers, fetcher=fetcher)

    @property
    def get_base_url(self) -> str:
        """获取新闻详情页基础url

        Returns:
            str: 新闻详情页基础url
        """
        return "https://news.qq.com"

    def get_article_id(self) -> str:
        """获取新闻详情页文章id
            eg: https://news.qq.com/rain/a/20251016A07W8J00
                return: 20251016A07W8J00
        Returns:
            str: 新闻详情页文章id
        """
        try:
            # Extract ID from URL pattern: /a/[ID]
            news_id = self.new_url.split("/a/")[1].split("?")[0].strip("/")
            return news_id
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"解析文章ID失败，请检查URL是否正确: {exc}") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.impersonate = "chrome"
        return request

    def _extract_window_data(self, html_content: str) -> dict:
        """从HTML中提取window.DATA对象

        腾讯新闻将元信息存储在window.DATA JavaScript变量中

        Args:
            html_content (str): HTML内容

        Returns:
            dict: window.DATA对象，如果提取失败则返回空字典
        """
        try:
            # 查找 window.DATA = {...} 模式
            pattern = r'window\.DATA\s*=\s*(\{[\s\S]*?\});'
            match = re.search(pattern, html_content)

            if match:
                data_json = match.group(1)
                return json.loads(data_json)
        except (json.JSONDecodeError, AttributeError) as e:
            self.logger.warning(f"Failed to extract window.DATA: {e}")

        return {}

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        """解析新闻详情页元信息

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            NewsMetaInfo: 新闻元信息
        """
        self.logger.info(
            "Start to parse html to news meta, news_url: %s", self.new_url
        )

        # 从window.DATA中提取元信息
        window_data = self._extract_window_data(html_content)

        author_name = window_data.get("media", "")
        publish_time = window_data.get("pubtime", "")

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
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

        # Tencent news content is in div.rich_media_content
        elements = selector.xpath('//div[@class="rich_media_content"]/*')
        for element in elements:
            # Handle paragraph text
            if element.root.tag == 'p':
                # Check if paragraph contains an image
                has_img = element.xpath('.//img').get() is not None

                if has_img:
                    # Extract image URL
                    img_url = element.xpath('.//img/@src').get('')
                    if img_url:
                        contents.append(ContentItem(type=ContentType.IMAGE, content=img_url, desc=img_url))
                else:
                    # Extract text content
                    text = element.xpath('string()').get('').strip()
                    if text:
                        contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

            # Handle standalone images
            elif element.root.tag == 'img':
                img_url = element.xpath('./@src').get('')
                if img_url:
                    contents.append(ContentItem(type=ContentType.IMAGE, content=img_url, desc=img_url))

            # Handle videos
            elif element.root.tag == 'video':
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
        selector = Selector(text=html)

        # Get title from h1
        title = selector.xpath('//h1/text()').get("")
        if not title:
            raise ValueError("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)

        return self.compose_news_item(
            title=title.strip(),
            meta_info=meta_info,
            contents=contents,
        )


if __name__ == "__main__":
    # Test URL
    article_url = "https://news.qq.com/rain/a/20251016A07W8J00"
    crawler = TencentNewsCrawler(article_url, save_path="data/")
    result = crawler.run()
    print(f"Successfully crawled: {result.title}")
    print(f"Author: {result.meta_info.author_name}")
    print(f"Publish time: {result.meta_info.publish_time}")
    print(f"Text paragraphs: {len(result.texts)}")
    print(f"Images: {len(result.images)}")
