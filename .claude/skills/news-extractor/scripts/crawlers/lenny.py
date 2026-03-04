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

FIXED_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
FIXED_COOKIE = "ab_experiment_sampled=%22false%22; ab_testing_id=%22a5afcd47-8198-4089-bb2a-ba8628b6da67%22; _ga=GA1.1.462650913.1731604007; ajs_anonymous_id=%22f28ff03f-6d49-40d4-8b92-7a9e0e0f7d21%22"


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class LennysNewsletterContentParser:
    def __init__(self):
        self._contents: List[ContentItem] = []

    def parse(self, html_content: str) -> List[ContentItem]:
        self._contents = []
        selector = Selector(text=html_content)
        content_node = selector.xpath("//div[@class='available-content']")
        if not content_node:
            return self._contents
        for node in content_node.xpath("./*"):
            self._process_content_node(node)
        contents = [item for item in self._contents if item.content.strip()]
        return self._remove_duplicate_contents(contents)

    def _remove_duplicate_contents(self, contents: List[ContentItem]) -> List[ContentItem]:
        unique_contents = []
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

    def _process_content_node(self, node: Selector):
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
            for li in node.xpath(".//li"):
                item_text = self._process_list_item(li)
                if item_text:
                    self._contents.append(ContentItem(type=ContentType.TEXT, content=item_text))
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
                for maybe_exist_node in node.xpath(".//img | .//video | .//iframe"):
                    media_content = self._process_media(maybe_exist_node)
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
            return

        if node.root.tag == "a":
            if node.xpath(".//img"):
                for img_node in node.xpath(".//img"):
                    media_content = self._process_media(img_node)
                    if media_content:
                        self._contents.append(media_content)
            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return


class LennysNewsletterCrawler(BaseNewsCrawler):
    headers_model = RequestHeaders

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
    ):
        super().__init__(new_url, save_path, headers=headers)
        self._content_parser = LennysNewsletterContentParser()

    @property
    def get_base_url(self) -> str:
        return "https://www.lennysnewsletter.com/"

    def get_article_id(self) -> str:
        try:
            news_id = self.new_url.split("?")[0].split("/")[-1]
            if news_id.endswith("/"):
                news_id = news_id[:-1]
            return news_id
        except Exception as exc:
            raise ValueError("解析文章ID失败，请检查URL是否正确") from exc

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        sel = Selector(text=html_content)
        author_xpath = "//div[@class='post-header']//div[contains(@class, 'profile-hover-card-target')]/a"
        publish_time = sel.xpath(
            "//div[@class='post-header']//div[@class='pencraft pc-display-flex pc-gap-4 pc-reset']/div/text()"
        ).get() or ""
        author_name = sel.xpath(author_xpath + "/text()").get() or ""
        author_url = sel.xpath(author_xpath + "/@href").get() or ""
        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url=author_url.strip(),
        )

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        return self._content_parser.parse(html_content)

    def parse_content(self, html: str) -> NewsItem:
        selector = Selector(text=html)
        title = selector.xpath("//h1/text()").get()
        if not title:
            raise ValueError("Failed to get title")
        subtitle = selector.xpath("//h3/text()").get() or ""
        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)
        return self.compose_news_item(
            title=title,
            subtitle=subtitle,
            meta_info=meta_info,
            contents=contents,
        )
