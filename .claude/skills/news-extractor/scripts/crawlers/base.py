# -*- coding: utf-8 -*-
"""
爬虫基类
"""
from __future__ import annotations

import json
import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Type

from tenacity import Retrying, stop_after_attempt, wait_fixed

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parents[1]))

from models import ContentItem, NewsItem, NewsMetaInfo, RequestHeaders
from crawlers.fetchers import CurlCffiFetcher, FetchRequest, FetchStrategy, RequestsFetcher


class BaseNewsCrawler(ABC):
    """
    Template for news crawlers.

    Subclasses implement platform-specific parsing while reusing the shared
    fetching, validation, and persistence logic.
    """

    headers_model: Type[RequestHeaders] = RequestHeaders
    fetch_strategy: Type[FetchStrategy] = RequestsFetcher
    fetch_attempts: int = 3
    fetch_wait_seconds: float = 1.0
    fetch_timeout: float = 15.0
    persist_by_default: bool = True

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
        fetcher: Optional[FetchStrategy] = None,
    ):
        self.new_url = new_url
        self.url = new_url
        self.save_path = Path(save_path)
        self.headers_model_instance = headers or self.headers_model()
        self.headers = self.headers_model_instance.to_http_headers()
        self.fetcher = fetcher or self.create_fetcher()
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def create_fetcher(self) -> FetchStrategy:
        """Instantiate the fetch strategy used for this crawler."""
        return self.fetch_strategy()

    def build_fetch_request(self) -> FetchRequest:
        """Produce the request parameters for the fetcher."""
        return FetchRequest(
            url=self.new_url,
            headers=self.headers,
            timeout=self.fetch_timeout,
        )

    def fetch_content(self) -> str:
        """Fetch remote HTML with retry semantics."""
        request = self.build_fetch_request()
        retryer = Retrying(
            stop=stop_after_attempt(self.fetch_attempts),
            wait=wait_fixed(self.fetch_wait_seconds),
            reraise=True,
        )
        return retryer(self._fetch_once, request)

    def _fetch_once(self, request: FetchRequest) -> str:
        self.logger.info("Start to fetch content from %s", request.url)
        return self.fetcher.fetch(request)

    @abstractmethod
    def parse_content(self, html: str) -> NewsItem:
        """Convert raw HTML into a NewsItem."""

    def validate_item(self, news_item: NewsItem) -> None:
        """Ensure crawled content is non-empty."""
        if not news_item.contents and not news_item.texts:
            raise ValueError(f"Empty content for article: {news_item.title}")

    def save_as_json(self, news_item: NewsItem) -> Path:
        """Persist the NewsItem as JSON."""
        self.save_path.mkdir(parents=True, exist_ok=True)
        path = self.save_path / f"{self.get_article_id()}.json"
        path.write_text(
            json.dumps(news_item.to_dict(), ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        return path

    def run(self, persist: Optional[bool] = None) -> NewsItem:
        """Full crawling pipeline."""
        should_persist = self.persist_by_default if persist is None else persist
        html = self.fetch_content()
        news_item = self.parse_content(html)
        self.validate_item(news_item)
        if should_persist:
            self.save_as_json(news_item)
        self.logger.info("Success to get content from %s", self.new_url)
        return news_item

    @abstractmethod
    def get_article_id(self) -> str:
        """Return the unique identifier used for persistence."""

    def get_save_json_path(self) -> str:
        """Compute the output path for the JSON artifact."""
        return str(self.save_path / f"{self.get_article_id()}.json")

    def compose_news_item(
        self,
        *,
        title: str,
        meta_info: NewsMetaInfo,
        contents: list[ContentItem],
        subtitle: Optional[str] = None,
        news_id: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> NewsItem:
        """Utility for composing a NewsItem with derived fields."""
        return NewsItem(
            title=title,
            subtitle=subtitle,
            news_url=self.new_url,
            news_id=news_id or self.get_article_id(),
            meta_info=meta_info,
            contents=contents,
            extra=extra or {},
        )

    def init_logger(self) -> None:
        """Legacy no-op kept for backwards compatibility."""
        return None
