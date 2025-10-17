# -*- coding: utf-8 -*-
from __future__ import annotations

# author: relakkes@gmail.com
# date: 2024-11-15
# description: naver news 采集器

from typing import List, Optional

import requests
from parsel import Selector
from pydantic import Field
from tenacity import retry, stop_after_attempt, wait_fixed

from news_crawler.core import (
    BaseNewsCrawler,
    ContentItem,
    ContentType,
    NewsItem,
    NewsMetaInfo,
    RequestHeaders as BaseRequestHeaders,
)
from news_crawler.core.fetchers import FetchRequest


FIXED_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)
FIXED_COOKIE = (
    "NAC=rpJDBYQa8Mxu; NACT=1; BA_DEVICE=105bf8f8-2a73-4b2f-bcbe-caf69282df11; "
    "NNB=D3M67LB7FQ3GO; BUC=Jabp6uagPvoJOfK-0YiUWPlEPu939nX6xkrTwVxttog=; "
    "JSESSIONID=05B14546153BE5D2B669A54AA439F9E7.jvm1"
)


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class NaverNewsContentParser:
    """负责解析 Naver 博客正文结构。"""

    def __init__(self) -> None:
        self._contents: List[ContentItem] = []

    def parse(self, html_content: str) -> List[ContentItem]:
        self._contents = []
        selector = Selector(text=html_content)
        content_node = selector.xpath("//div[@class='se-main-container']")
        if not content_node:
            return []

        for node in content_node.xpath("./*"):
            self._process_content_node(node)

        contents = [item for item in self._contents if item.content.strip()]
        return self._remove_duplicate_contents(contents)

    def _remove_duplicate_contents(
        self, contents: List[ContentItem]
    ) -> List[ContentItem]:
        unique_contents: List[ContentItem] = []
        seen_contents = set()
        for item in contents:
            content_key = f"{item.type}:{item.content}"
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique_contents.append(item)
        return unique_contents

    @staticmethod
    def _process_media(node: Selector) -> Optional[ContentItem]:
        if node.root.tag == "img":
            img_url = node.attrib.get("data-lazy-src", "") or node.attrib.get("src", "")
            if img_url:
                return ContentItem(type=ContentType.IMAGE, content=img_url)
        elif node.root.tag in ["video", "iframe"]:
            video_url = node.attrib.get("src", "")
            if video_url:
                return ContentItem(type=ContentType.VIDEO, content=video_url)
        return None

    @staticmethod
    def _process_text_block(node: Selector) -> Optional[str]:
        if node.root.tag in ["script", "style"]:
            return None

        text = node.xpath("string(.)").get("").strip()
        if not text:
            return None
        return text.replace("\u200b", "")

    def _process_list_item(self, node: Selector) -> Optional[str]:
        text = self._process_text_block(node)
        if not text:
            return None

        if node.xpath("./ancestor::ol"):
            position = len(node.xpath("./preceding-sibling::li")) + 1
            return f"{position}. {text}"
        return f"• {text}"

    def _process_content_node(self, node: Selector) -> None:
        if node.root.tag in ["section", "div", "blockquote", "figure"]:
            for child in node.xpath("./*"):
                self._process_content_node(child)
            return

        if node.root.tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        if node.root.tag in ["ul", "ol"]:
            list_items = []
            for li in node.xpath(".//li"):
                item_text = self._process_list_item(li)
                if item_text:
                    list_items.append(item_text)
            for item in list_items:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=item))
            return

        if node.root.tag == "li":
            text = self._process_list_item(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        media_content = self._process_media(node)
        if media_content:
            self._contents.append(media_content)
            return

        if node.root.tag == "p":
            if node.xpath(".//img") or node.xpath(".//video") or node.xpath(".//iframe"):
                for media_node in node.xpath(".//img | .//video | .//iframe"):
                    media_content = self._process_media(media_node)
                    if media_content:
                        self._contents.append(media_content)

            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        if node.root.tag in ["span", "strong"]:
            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))


class NaverNewsCrawler(BaseNewsCrawler):
    headers_model = RequestHeaders

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
    ):
        super().__init__(new_url, save_path, headers=headers)
        self._content_parser = NaverNewsContentParser()
        self.iframe_url = self.get_iframe_url_path()

    @property
    def get_base_url(self) -> str:
        return "https://blog.naver.com"

    def get_article_id(self) -> str:
        try:
            return self.new_url.split("?")[0].split("/")[-1].rstrip("/")
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ValueError("解析文章ID失败，请检查URL是否正确") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.url = self.iframe_url
        return request

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def get_iframe_url_path(self) -> str:
        response = requests.get(self.new_url, headers=self.headers)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch content: {response.status_code}")
        response.encoding = "utf-8"
        selector = Selector(text=response.text)
        iframe_url = selector.xpath("//iframe[@id='mainFrame']/@src").get("")
        if not iframe_url:
            raise RuntimeError("Failed to get iframe url")
        self.logger.info("Success to get iframe url: %s", iframe_url)
        return self.get_base_url + iframe_url

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        self.logger.info(
            "Start to parse html to news meta, news_url: %s", self.new_url
        )
        sel = Selector(text=html_content)

        publish_time = (
            sel.xpath("//span[@class='se_publishDate pcol2']/text()").get() or ""
        )
        author_name = sel.xpath("//span[@class='nick']/a/text()").get() or ""
        author_url = sel.xpath("//span[@class='nick']/a/@href").get() or ""

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url=author_url.strip(),
        )

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        return self._content_parser.parse(html_content)

    def parse_content(self, html: str) -> NewsItem:
        selector = Selector(text=html)
        title = (
            selector.xpath(
                "string(//div[@class='se-module se-module-text se-title-text']//span)"
            ).get("")
            or ""
        ).strip()
        if not title:
            raise ValueError("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)

        return self.compose_news_item(
            title=title,
            meta_info=meta_info,
            contents=contents,
        )


if __name__ == "__main__":
    article_url1 = "https://blog.naver.com/orangememories/223618759620"
    article_url2 = "https://blog.naver.com/hyobin_mo/223660806667"
    for article_url in [article_url1, article_url2]:
        crawler = NaverNewsCrawler(article_url, save_path="data/")
        crawler.run()
