# -*- coding: utf-8 -*-
from __future__ import annotations

# author: relakkes@gmail.com
# date: 2025-10-17
# description: 采集网易新闻详情

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

## 网易的cookies不需要登录态，随便打开一个网易新闻提取cookies即可
FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = ''


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class NeteaseNewsCrawler(BaseNewsCrawler):
    fetch_strategy = CurlCffiFetcher

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
        fetcher: Optional[CurlCffiFetcher] = None,
    ):
        """初始化网易新闻详情爬虫

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
        return "https://www.163.com"

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
        selector = Selector(text=html)

        # Get title from h1.post_title
        title = selector.xpath('//h1[@class="post_title"]/text()').get("")
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
    article_url = "https://www.163.com/news/article/KC12OUHK000189FH.html"
    crawler = NeteaseNewsCrawler(article_url, save_path="data/")
    result = crawler.run()
    print(f"Successfully crawled: {result.title}")
    print(f"Text paragraphs: {len(result.texts)}")
    print(f"Images: {len(result.images)}")
