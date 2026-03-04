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


class BBCNewsCrawler(BaseNewsCrawler):
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
        return "https://www.bbc.com"

    def get_article_id(self) -> str:
        try:
            path_part = self.new_url.split("/articles/")[1]
            news_id = path_part.split("?")[0].strip("/")
            return news_id
        except Exception as exc:
            raise ValueError(f"解析文章ID失败，请检查URL是否正确: {exc}") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.impersonate = "chrome"
        return request

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        sel = Selector(text=html_content)
        publish_time = sel.xpath('//time/@datetime').get() or \
                      sel.xpath('//time/text()').get() or ""
        author_parts = sel.xpath('//div[@data-component="byline-block"]//p/text()').getall()
        author_name = " ".join([part.strip() for part in author_parts if part.strip()]) if author_parts else ""
        author_url = self.get_base_url
        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip() if author_name else "BBC News",
            author_url=author_url,
        )

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        contents = []
        selector = Selector(text=html_content)
        article = selector.xpath('//article')
        if not article:
            return contents

        cover_figure = article.xpath('.//figure[.//img][1]')
        if cover_figure:
            img_srcs = cover_figure.xpath('.//img/@src').getall()
            img_src = None
            for src in img_srcs:
                if src and not src.endswith('grey-placeholder.png'):
                    img_src = src
                    break
            if img_src:
                img_caption = cover_figure.xpath('.//figcaption//text()').get('').strip()
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = self.get_base_url + img_src
                contents.append(ContentItem(type=ContentType.IMAGE, content=img_src, desc=img_caption or img_src))

        text_blocks = article.xpath('.//div[@data-component="text-block"]')
        for text_block in text_blocks:
            paragraphs = text_block.xpath('.//p')
            for para in paragraphs:
                text = para.xpath('string()').get('').strip()
                if text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

        content_figures = article.xpath('.//figure[.//img][position()>1]')
        for figure in content_figures:
            img_srcs = figure.xpath('.//img/@src').getall()
            img_src = None
            for src in img_srcs:
                if src and not src.endswith('grey-placeholder.png'):
                    img_src = src
                    break
            if img_src:
                img_caption = figure.xpath('.//figcaption//text()').get('').strip()
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = self.get_base_url + img_src
                contents.append(ContentItem(type=ContentType.IMAGE, content=img_src, desc=img_caption or img_src))

        video_blocks = article.xpath('.//div[@data-component="video-block"]')
        for video_block in video_blocks:
            video_src = video_block.xpath('.//video/@src').get() or \
                       video_block.xpath('.//source/@src').get() or \
                       video_block.xpath('.//@data-video-src').get()
            if video_src:
                if video_src.startswith('//'):
                    video_src = 'https:' + video_src
                elif video_src.startswith('/'):
                    video_src = self.get_base_url + video_src
                contents.append(ContentItem(type=ContentType.VIDEO, content=video_src, desc=video_src))

        return contents

    def parse_content(self, html: str) -> NewsItem:
        selector = Selector(text=html)
        title = selector.xpath('//h1/text()').get("")
        if not title:
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
