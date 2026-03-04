# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from parsel import Selector
from pydantic import Field

sys.path.insert(0, str(Path(__file__).parents[1]))

from models import ContentItem, ContentType, NewsItem, NewsMetaInfo, RequestHeaders as BaseRequestHeaders
from crawlers.base import BaseNewsCrawler
from crawlers.fetchers import CurlCffiFetcher, FetchRequest

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
        super().__init__(new_url, save_path, headers=headers, fetcher=fetcher)

    @property
    def get_base_url(self) -> str:
        return "https://edition.cnn.com"

    def get_article_id(self) -> str:
        try:
            parts = self.new_url.rstrip('/').split('/')
            news_id = parts[-1].split('?')[0]
            return news_id
        except Exception as exc:
            raise ValueError(f"解析文章ID失败，请检查URL是否正确: {exc}") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.impersonate = "chrome"
        return request

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        sel = Selector(text=html_content)
        publish_time = sel.xpath('//time/@datetime').get() or ""
        author_name = sel.xpath('//a[contains(@href, "profiles")]/text()').get() or \
                     sel.xpath('//div[contains(@class, "byline")]//text()').get() or ""
        author_name = author_name.strip()
        if author_name.startswith('By '):
            author_name = author_name[3:].strip()
        author_url = self.get_base_url if author_name else ""
        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name if author_name else "CNN News",
            author_url=author_url,
        )

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        contents = []
        selector = Selector(text=html_content)
        main = selector.xpath('//main')
        if not main:
            return contents

        content_elements = main.xpath('.//p | .//h2 | .//picture')
        for element in content_elements:
            tag_name = element.root.tag
            if tag_name == 'p':
                text = element.xpath('string()').get('').strip()
                if text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))
            elif tag_name == 'h2':
                text = element.xpath('string()').get('').strip()
                if text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=f"## {text}", desc=text))
            elif tag_name == 'picture':
                img = element.xpath('.//img')
                if img:
                    img_src = img.xpath('./@src').get()
                    img_alt = img.xpath('./@alt').get('').strip()
                    if img_src:
                        if img_src.startswith('//'):
                            img_src = 'https:' + img_src
                        elif img_src.startswith('/'):
                            img_src = self.get_base_url + img_src
                        contents.append(ContentItem(type=ContentType.IMAGE, content=img_src, desc=img_alt or img_src))
        return contents

    def parse_content(self, html: str) -> NewsItem:
        selector = Selector(text=html)
        title = selector.xpath('//h1/text()').get("")
        if not title:
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
