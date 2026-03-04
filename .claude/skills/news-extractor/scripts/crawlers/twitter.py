# -*- coding: utf-8 -*-
"""
Twitter/X 推文内容提取爬虫
"""
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import Field

sys.path.insert(0, str(Path(__file__).parents[1]))

from models import ContentItem, ContentType, NewsItem, NewsMetaInfo, RequestHeaders as BaseRequestHeaders
from crawlers.base import BaseNewsCrawler
from crawlers.fetchers import FetchStrategy
from crawlers.twitter_client import TwitterClient, TwitterCredentials, extract_tweet_id
from crawlers.twitter_types import TweetData, TweetMedia

logger = logging.getLogger(__name__)


class TwitterRequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        alias="User-Agent",
    )


class TwitterApiFetcher(FetchStrategy):
    """Twitter API 数据获取策略"""

    def __init__(self, credentials: Optional[TwitterCredentials] = None):
        self.credentials = credentials
        self.client = TwitterClient(credentials)

    def fetch(self, request) -> str:
        tweet_id = extract_tweet_id(request.url)
        tweet_data = self.client.get_tweet(tweet_id)
        import json
        return json.dumps({
            "tweet_id": tweet_id,
            "tweet_data": tweet_data.__dict__ if tweet_data else None,
        })


class TwitterNewsCrawler(BaseNewsCrawler):
    """Twitter/X 推文爬虫"""

    headers_model = TwitterRequestHeaders
    fetch_strategy = TwitterApiFetcher
    persist_by_default = True

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[TwitterRequestHeaders] = None,
        fetcher: Optional[FetchStrategy] = None,
        cookie: Optional[str] = None,
        credentials: Optional[TwitterCredentials] = None,
    ):
        if credentials:
            self._credentials = credentials
        elif cookie:
            try:
                self._credentials = TwitterCredentials.from_cookie_string(cookie)
            except ValueError:
                logger.warning("Cookie 解析失败，将使用 Guest Token 模式")
                self._credentials = None
        else:
            self._credentials = TwitterCredentials.from_env()

        if fetcher is None:
            fetcher = TwitterApiFetcher(self._credentials)

        super().__init__(new_url, save_path, headers=headers, fetcher=fetcher)
        self._tweet_data: Optional[TweetData] = None

    def create_fetcher(self) -> FetchStrategy:
        return TwitterApiFetcher(self._credentials)

    def get_article_id(self) -> str:
        return extract_tweet_id(self.new_url)

    def fetch_content(self) -> str:
        tweet_id = self.get_article_id()
        self.logger.info("Fetching tweet %s", tweet_id)
        client = TwitterClient(self._credentials)
        self._tweet_data = client.get_tweet(tweet_id)
        return ""

    def parse_content(self, html: str) -> NewsItem:
        if self._tweet_data is None:
            raise ValueError("推文数据未获取")

        tweet = self._tweet_data
        contents: List[ContentItem] = []

        text = tweet.full_text or tweet.text
        if text:
            text = self._clean_text(text)
            for paragraph in text.split("\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    contents.append(ContentItem(type=ContentType.TEXT, content=paragraph))

        for media in tweet.media:
            if media.type == "photo":
                contents.append(ContentItem(type=ContentType.IMAGE, content=media.media_url, desc=media.alt_text))
            elif media.type in ("video", "animated_gif"):
                if media.video_url:
                    contents.append(ContentItem(type=ContentType.VIDEO, content=media.video_url, desc=f"{media.type}: {media.width}x{media.height}"))

        if tweet.quoted_tweet:
            quoted = tweet.quoted_tweet
            quoted_author = f"@{quoted.author.screen_name}" if quoted.author.screen_name else "Unknown"
            contents.append(ContentItem(type=ContentType.TEXT, content=f"[引用 {quoted_author}]: {self._clean_text(quoted.full_text or quoted.text)}"))

        meta_info = NewsMetaInfo(
            author_name=f"{tweet.author.name} (@{tweet.author.screen_name})",
            author_url=f"https://x.com/{tweet.author.screen_name}" if tweet.author.screen_name else "",
            publish_time=self._parse_publish_time(tweet.created_at),
            extra={
                "retweet_count": tweet.retweet_count,
                "like_count": tweet.like_count,
                "reply_count": tweet.reply_count,
                "view_count": tweet.view_count,
            },
        )

        title_text = tweet.full_text or tweet.text
        title = self._clean_text(title_text)[:100] if title_text else f"Tweet {tweet.id}"

        return self.compose_news_item(
            title=title,
            meta_info=meta_info,
            contents=contents,
            news_id=tweet.id,
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"\s*https://t\.co/\w+\s*$", "", text)
        text = re.sub(r"https://t\.co/\w+", "", text)
        return text.strip()

    @staticmethod
    def _parse_publish_time(created_at: str) -> str:
        if not created_at:
            return ""
        try:
            dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return created_at
