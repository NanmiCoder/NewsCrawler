# -*- coding: utf-8 -*-
"""
网易新闻爬虫
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from parsel import Selector
from pydantic import Field

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parents[1]))

from models import ContentItem, ContentType, NewsItem, NewsMetaInfo, RequestHeaders as BaseRequestHeaders
from crawlers.base import BaseNewsCrawler
from crawlers.fetchers import CurlCffiFetcher, FetchRequest


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
        super().__init__(new_url, save_path, headers=headers, fetcher=fetcher)

    @property
    def get_base_url(self) -> str:
        return "https://www.163.com"

    def get_article_id(self) -> str:
        try:
            news_id = self.new_url.split("/article/")[1].split(".html")[0].split("?")[0]
            return news_id
        except Exception as exc:
            raise ValueError(f"解析文章ID失败，请检查URL是否正确: {exc}") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.impersonate = "chrome"
        return request

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        self.logger.info("Start to parse html to news meta, news_url: %s", self.new_url)
        sel = Selector(text=html_content)

        publish_time = sel.xpath("//html/@data-publishtime").get() or ""

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
        contents = []
        selector = Selector(text=html_content)

        elements = selector.xpath('//div[@class="post_body"]/*')
        for element in elements:
            if element.root.tag == 'p':
                text = element.xpath('string()').get('').strip()
                if text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

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

            if element.root.tag == 'video':
                video_url = element.xpath('./@src').get('')
                if video_url:
                    contents.append(ContentItem(type=ContentType.VIDEO, content=video_url, desc=video_url))

        return contents

    def parse_content(self, html: str) -> NewsItem:
        selector = Selector(text=html)

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
