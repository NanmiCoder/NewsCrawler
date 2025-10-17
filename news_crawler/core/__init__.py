# -*- coding: utf-8 -*-
"""
Core primitives shared by all news crawler implementations.
"""

from .base import BaseNewsCrawler
from .fetchers import CurlCffiFetcher, FetchRequest, FetchStrategy, RequestsFetcher
from .models import (
    DEFAULT_USER_AGENT,
    ContentItem,
    ContentType,
    NewsItem,
    NewsMetaInfo,
    RequestHeaders,
)
from .protocols import ContentParser

__all__ = [
    "BaseNewsCrawler",
    "ContentItem",
    "ContentParser",
    "ContentType",
    "CurlCffiFetcher",
    "DEFAULT_USER_AGENT",
    "FetchRequest",
    "FetchStrategy",
    "NewsItem",
    "NewsMetaInfo",
    "RequestHeaders",
    "RequestsFetcher",
]
