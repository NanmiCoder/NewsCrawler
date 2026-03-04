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

FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = ''


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class DetikNewsCrawler(BaseNewsCrawler):
    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
    ):
        super().__init__(new_url, save_path, headers=headers)

    @property
    def get_base_url(self) -> str:
        return "https://news.detik.com"

    def get_article_id(self) -> str:
        try:
            route_path = self.new_url.replace(self.get_base_url, "")
            news_id = route_path.split("/")[2].split("?")[0]
            if news_id.endswith("/"):
                news_id = news_id[:-1]
            return news_id
        except Exception as exc:
            raise ValueError("解析文章ID失败，请检查URL是否正确") from exc

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        sel = Selector(text=html_content)
        publish_time = sel.xpath("//article[@class='detail']//div[@class='detail__date']/text()").get() or ""
        author_name = sel.xpath("string(//article[@class='detail']//div[@class='detail__author'])").get() or ""
        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url="",
        )

    def parse_html_to_news_media(self, html_content: str) -> List[ContentItem]:
        res = []
        selector = Selector(text=html_content)
        poster_img = selector.xpath("//div[@class='detail__media']/figure[@class='detail__media-image']/img/@src").get()
        poster_video = selector.xpath("//div[@class='detail__media']/iframe/@src").get()
        poster_desc = selector.xpath("string(//div[@class='detail__media']//figcaption[@class='detail__media-caption'])").get() or ""
        if poster_img:
            res.append(ContentItem(type=ContentType.IMAGE, content=poster_img, desc=poster_desc or poster_img))
        if poster_video:
            res.append(ContentItem(type=ContentType.VIDEO, content=poster_video, desc=poster_desc or poster_video))
        return res

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        contents = []
        media_contents = self.parse_html_to_news_media(html_content)
        contents.extend(media_contents)

        selector = Selector(text=html_content)
        elements = selector.xpath('//div[@class="detail__body-text itp_bodycontent"]/*')
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

            if element.root.tag in ['table', 'strong']:
                other_tag_content = element.xpath('string()').get('').strip()
                if other_tag_content:
                    contents.append(ContentItem(type=ContentType.TEXT, content=other_tag_content, desc=other_tag_content))

        return contents

    def parse_content(self, html: str) -> NewsItem:
        selector = Selector(text=html)
        title = selector.xpath("//h1/text()").get("").strip()
        if not title:
            raise ValueError("Failed to get title")
        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)
        return self.compose_news_item(title=title, meta_info=meta_info, contents=contents)
