# -*- coding: utf-8 -*-
from __future__ import annotations

# author: AI Assistant
# date: 2025-10-27
# description: 采集CNN新闻详情

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

# CNN不需要登录态，使用标准User-Agent即可
FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = ''


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class CNNNewsCrawler(BaseNewsCrawler):
    fetch_strategy = CurlCffiFetcher

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
        fetcher: Optional[CurlCffiFetcher] = None,
    ):
        """初始化CNN新闻详情爬虫

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
        return "https://edition.cnn.com"

    def get_article_id(self) -> str:
        """获取新闻详情页文章id
            eg: https://edition.cnn.com/2025/10/27/uk/sami-hamdi-detained-ice-intl
                return: sami-hamdi-detained-ice-intl
        Returns:
            str: 新闻详情页文章id
        """
        try:
            # Extract ID from URL pattern: /YYYY/MM/DD/section/article-slug
            # Get the last part of the URL
            parts = self.new_url.rstrip('/').split('/')
            news_id = parts[-1].split('?')[0]
            return news_id
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"解析文章ID失败，请检查URL是否正确: {exc}") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.impersonate = "chrome"
        return request

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
        sel = Selector(text=html_content)

        # Extract publish time from time tag with datetime attribute
        publish_time = sel.xpath('//time/@datetime').get() or ""

        # Extract author from byline
        # CNN usually has author in format: "By Author Name"
        author_name = sel.xpath('//a[contains(@href, "profiles")]/text()').get() or \
                     sel.xpath('//div[contains(@class, "byline")]//text()').get() or ""

        # Clean author name
        author_name = author_name.strip()
        if author_name.startswith('By '):
            author_name = author_name[3:].strip()

        # CNN doesn't have direct author URLs in simple format
        author_url = self.get_base_url if author_name else ""

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name if author_name else "CNN News",
            author_url=author_url,
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

        # CNN content is in main tag
        main = selector.xpath('//main')

        if not main:
            self.logger.warning("No main content found")
            return contents

        # Extract content - CNN uses p, h2, and picture tags
        # We need to extract them in order to maintain the article structure
        content_elements = main.xpath('.//p | .//h2 | .//picture')

        for element in content_elements:
            tag_name = element.root.tag

            if tag_name == 'p':
                # Get text content
                text = element.xpath('string()').get('').strip()
                if text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

            elif tag_name == 'h2':
                # H2 as section headers - also treat as text
                text = element.xpath('string()').get('').strip()
                if text:
                    # Add a special marker for headers
                    contents.append(ContentItem(type=ContentType.TEXT, content=f"## {text}", desc=text))

            elif tag_name == 'picture':
                # Extract image from picture tag
                img = element.xpath('.//img')
                if img:
                    img_src = img.xpath('./@src').get()
                    img_alt = img.xpath('./@alt').get('').strip()

                    if img_src:
                        # Normalize URL
                        if img_src.startswith('//'):
                            img_src = 'https:' + img_src
                        elif img_src.startswith('/'):
                            img_src = self.get_base_url + img_src
                        contents.append(ContentItem(type=ContentType.IMAGE, content=img_src, desc=img_alt or img_src))

        return contents

    def parse_content(self, html: str) -> NewsItem:
        """解析新闻详情页内容

        Args:
            html (str): 新闻详情页内容

        Returns:
            NewsItem: 新闻详情
        """
        selector = Selector(text=html)

        # Get title from h1 tag
        title = selector.xpath('//h1/text()').get("")
        if not title:
            # Try alternative selector
            title = selector.xpath('//h1//text()').get("")

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
    article_url = "https://edition.cnn.com/2025/10/27/uk/sami-hamdi-detained-ice-intl"
    crawler = CNNNewsCrawler(article_url, save_path="data/")
    result = crawler.run()
    print(f"Successfully crawled: {result.title}")
    print(f"Author: {result.meta_info.author_name}")
    print(f"Publish time: {result.meta_info.publish_time}")
    print(f"Text paragraphs: {len(result.texts)}")
    print(f"Images: {len(result.images)}")
    print(f"Videos: {len(result.videos)}")
