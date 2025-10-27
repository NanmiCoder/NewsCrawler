# -*- coding: utf-8 -*-
from __future__ import annotations

# author: AI Assistant
# date: 2025-10-27
# description: 采集BBC新闻详情

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

# BBC不需要登录态，使用标准User-Agent即可
FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = ''


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class BBCNewsCrawler(BaseNewsCrawler):
    fetch_strategy = CurlCffiFetcher

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
        fetcher: Optional[CurlCffiFetcher] = None,
    ):
        """初始化BBC新闻详情爬虫

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
        return "https://www.bbc.com"

    def get_article_id(self) -> str:
        """获取新闻详情页文章id
            eg: https://www.bbc.com/news/articles/c797qlx93j0o
                return: c797qlx93j0o
        Returns:
            str: 新闻详情页文章id
        """
        try:
            # Extract ID from URL pattern: /articles/[ID]
            path_part = self.new_url.split("/articles/")[1]
            news_id = path_part.split("?")[0].strip("/")
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
        publish_time = sel.xpath('//time/@datetime').get() or \
                      sel.xpath('//time/text()').get() or ""

        # Extract author from byline block
        author_parts = sel.xpath('//div[@data-component="byline-block"]//p/text()').getall()
        author_name = " ".join([part.strip() for part in author_parts if part.strip()]) if author_parts else ""

        # BBC doesn't have direct author URLs, use BBC as default
        author_url = self.get_base_url

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip() if author_name else "BBC News",
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

        # BBC content is structured in article tag
        article = selector.xpath('//article')

        if not article:
            self.logger.warning("No article content found")
            return contents

        # Extract cover image from first figure in article
        # BBC has multiple img tags per figure - skip placeholder, get the real image
        cover_figure = article.xpath('.//figure[.//img][1]')
        if cover_figure:
            # Get all img src from this figure and filter out placeholders
            img_srcs = cover_figure.xpath('.//img/@src').getall()
            img_src = None
            for src in img_srcs:
                if src and not src.endswith('grey-placeholder.png'):
                    img_src = src
                    break

            if img_src:
                img_caption = cover_figure.xpath('.//figcaption//text()').get('').strip()
                # Normalize URL
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = self.get_base_url + img_src
                contents.append(ContentItem(type=ContentType.IMAGE, content=img_src, desc=img_caption or img_src))

        # Extract text content from text-block
        text_blocks = article.xpath('.//div[@data-component="text-block"]')
        for text_block in text_blocks:
            paragraphs = text_block.xpath('.//p')
            for para in paragraphs:
                text = para.xpath('string()').get('').strip()
                if text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

        # Extract additional images from the content (not cover)
        content_figures = article.xpath('.//figure[.//img][position()>1]')
        for figure in content_figures:
            # Get all img src and filter out placeholders
            img_srcs = figure.xpath('.//img/@src').getall()
            img_src = None
            for src in img_srcs:
                if src and not src.endswith('grey-placeholder.png'):
                    img_src = src
                    break

            if img_src:
                img_caption = figure.xpath('.//figcaption//text()').get('').strip()
                # Normalize URL
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = self.get_base_url + img_src
                contents.append(ContentItem(type=ContentType.IMAGE, content=img_src, desc=img_caption or img_src))

        # Extract videos if present
        video_blocks = article.xpath('.//div[@data-component="video-block"]')
        for video_block in video_blocks:
            # BBC videos are typically embedded, try to get video URL from various sources
            video_src = video_block.xpath('.//video/@src').get() or \
                       video_block.xpath('.//source/@src').get() or \
                       video_block.xpath('.//@data-video-src').get()

            if video_src:
                # Normalize URL
                if video_src.startswith('//'):
                    video_src = 'https:' + video_src
                elif video_src.startswith('/'):
                    video_src = self.get_base_url + video_src
                contents.append(ContentItem(type=ContentType.VIDEO, content=video_src, desc=video_src))

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
            title = selector.xpath('//article//h1/text()').get("")

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
    article_url = "https://www.bbc.com/news/articles/c797qlx93j0o"
    crawler = BBCNewsCrawler(article_url, save_path="data/")
    result = crawler.run()
    print(f"Successfully crawled: {result.title}")
    print(f"Author: {result.meta_info.author_name}")
    print(f"Publish time: {result.meta_info.publish_time}")
    print(f"Text paragraphs: {len(result.texts)}")
    print(f"Images: {len(result.images)}")
    print(f"Videos: {len(result.videos)}")
