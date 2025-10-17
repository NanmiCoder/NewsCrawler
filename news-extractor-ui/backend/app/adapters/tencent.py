"""Tencent News adapter for backend API integration."""

import tempfile
from typing import Optional

from news_crawler.tencent_news import TencentNewsCrawler, RequestHeaders
from .base import CrawlerAdapter, NewsItem


class TencentAdapter(CrawlerAdapter):
    """Adapter for Tencent News crawler."""

    @property
    def platform_name(self) -> str:
        """Return platform name."""
        return "tencent"

    def extract(self, url: str, headers: Optional[RequestHeaders] = None) -> NewsItem:
        """Extract news content from Tencent News URL.

        Args:
            url: Tencent News article URL
            headers: Optional custom headers

        Returns:
            NewsItem: Extracted news data

        Raises:
            ValueError: If URL is invalid or extraction fails
        """
        # Create temporary directory for file output
        temp_dir = tempfile.mkdtemp()

        # Use provided headers or default
        request_headers = headers or RequestHeaders()

        # Create crawler instance
        crawler = TencentNewsCrawler(
            new_url=url,
            save_path=temp_dir,
            headers=request_headers
        )

        # Fetch and parse content
        html = crawler.fetch_content()
        news_item = crawler.parse_content(html)

        # Convert to API NewsItem model
        return NewsItem(news_item.model_dump())
