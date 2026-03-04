# -*- coding: utf-8 -*-
"""
数据模型定义
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class RequestHeaders(BaseModel):
    """Standardized HTTP headers used by crawlers."""

    model_config = ConfigDict(populate_by_name=True)

    user_agent: str = Field(default=DEFAULT_USER_AGENT, alias="User-Agent")
    cookie: Optional[str] = Field(default=None, alias="Cookie")
    referer: Optional[str] = Field(default=None, alias="Referer")
    accept_language: Optional[str] = Field(default=None, alias="Accept-Language")
    extra: Dict[str, str] = Field(default_factory=dict, alias="extra")

    def to_http_headers(self) -> Dict[str, str]:
        """Convert model fields to a plain HTTP headers dictionary."""
        headers = self.model_dump(
            by_alias=True, exclude_none=True, exclude={"extra"}
        )
        if self.extra:
            headers.update(self.extra)
        return headers


class ContentType(str, Enum):
    """Supported content fragments."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ContentItem(BaseModel):
    """Normalized content fragment."""

    type: ContentType = Field(default=ContentType.TEXT)
    content: str = Field(default="")
    desc: str = Field(default="")


class NewsMetaInfo(BaseModel):
    """Light-weight metadata describing an article."""

    author_name: str = Field(default="")
    author_url: str = Field(default="")
    publish_time: str = Field(default="")
    extra: Dict[str, Any] = Field(default_factory=dict)


class NewsItem(BaseModel):
    """Canonical representation of a news article."""

    title: str = Field(default="")
    subtitle: Optional[str] = Field(default=None)
    news_url: str = Field(default="")
    news_id: str = Field(default="")
    meta_info: NewsMetaInfo = Field(default_factory=NewsMetaInfo)
    contents: List[ContentItem] = Field(default_factory=list)
    texts: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Derive media fields from the content list when they are missing."""
        if not self.contents:
            return

        if not self.texts:
            self.texts = [
                item.content for item in self.contents if item.type == ContentType.TEXT
            ]
        if not self.images:
            self.images = [
                item.content for item in self.contents if item.type == ContentType.IMAGE
            ]
        if not self.videos:
            self.videos = [
                item.content for item in self.contents if item.type == ContentType.VIDEO
            ]

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dictionary representation."""
        return self.model_dump(exclude_none=True)
