# -*- coding: utf-8 -*-
"""
搜狐新闻爬虫
"""
from __future__ import annotations

import json
import re
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


class SohuNewsCrawler(BaseNewsCrawler):
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
        return "https://www.sohu.com"

    def get_article_id(self) -> str:
        try:
            path_part = self.new_url.split("/a/")[1]
            news_id = path_part.split("_")[0].split("?")[0]
            return news_id
        except Exception as exc:
            raise ValueError(f"解析文章ID失败，请检查URL是否正确: {exc}") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.impersonate = "chrome"
        return request

    def _is_valid_image_url(self, url: str) -> bool:
        if not url:
            return False
        if url.startswith(('http://', 'https://', '//')):
            return '.' in url or '/' in url
        return False

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        self.logger.info("Start to parse html to news meta, news_url: %s", self.new_url)
        sel = Selector(text=html_content)

        publish_time = sel.xpath('//span[@id="news-time"]/text()').get() or \
                      sel.xpath('//span[@class="time"]/text()').get() or ""

        author_name = sel.xpath('//meta[@name="mediaid"]/@content').get() or \
                     sel.xpath('//h4/a/text()').get() or ""
        author_url = sel.xpath('//h4/a/@href').get() or ""

        if author_url.startswith('//'):
            author_url = 'https:' + author_url

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url=author_url,
        )

    def _extract_images_from_json(self, html_content: str) -> List[str]:
        pattern = r'imgsList:\s*(\[[\s\S]*?\])\s*,'
        match = re.search(pattern, html_content)

        if match:
            try:
                imgs_json = match.group(1)
                imgs_json = re.sub(r',(\s*[}\]])', r'\1', imgs_json)
                imgs_list = json.loads(imgs_json)
                return [img.get('url', '') for img in imgs_list if isinstance(img, dict) and img.get('url')]
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse imgsList JSON: {e}")

        return []

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        contents = []
        selector = Selector(text=html_content)

        image_urls = self._extract_images_from_json(html_content)
        image_index = 0

        elements = selector.xpath('//article[@id="mp-editor"]/*')
        for element in elements:
            if element.root.tag == 'p':
                has_img = element.xpath('.//img').get() is not None

                if has_img and image_index < len(image_urls):
                    img_src = image_urls[image_index]
                    image_index += 1

                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    contents.append(ContentItem(type=ContentType.IMAGE, content=img_src, desc=img_src))

                text = element.xpath('string()').get('').strip()
                if text and not has_img:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

            elif element.root.tag == 'img':
                if image_index < len(image_urls):
                    img_url = image_urls[image_index]
                    image_index += 1

                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    contents.append(ContentItem(type=ContentType.IMAGE, content=img_url, desc=img_url))

            elif element.root.tag == 'video':
                video_url = element.xpath('./@src').get() or \
                           element.xpath('.//source/@src').get()
                if video_url:
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    contents.append(ContentItem(type=ContentType.VIDEO, content=video_url, desc=video_url))

        return contents

    def parse_content(self, html: str) -> NewsItem:
        selector = Selector(text=html)

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
