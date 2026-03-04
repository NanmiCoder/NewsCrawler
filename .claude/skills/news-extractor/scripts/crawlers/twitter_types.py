# -*- coding: utf-8 -*-
"""
Twitter/X 数据类型定义
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TweetAuthor:
    """推文作者信息"""
    id: str = ""
    name: str = ""
    screen_name: str = ""
    profile_image_url: str = ""
    verified: bool = False

    @classmethod
    def from_user_result(cls, user_data: Dict[str, Any]) -> "TweetAuthor":
        if not user_data:
            return cls()
        result = user_data.get("result", {})
        legacy = result.get("legacy", {})
        return cls(
            id=result.get("rest_id", ""),
            name=legacy.get("name", ""),
            screen_name=legacy.get("screen_name", ""),
            profile_image_url=legacy.get("profile_image_url_https", ""),
            verified=legacy.get("verified", False),
        )


@dataclass
class TweetMedia:
    """推文媒体附件"""
    type: str = ""
    url: str = ""
    media_url: str = ""
    video_url: str = ""
    alt_text: str = ""
    width: int = 0
    height: int = 0

    @classmethod
    def from_media_entity(cls, media: Dict[str, Any]) -> "TweetMedia":
        media_type = media.get("type", "")
        media_url = media.get("media_url_https", "")
        video_url = ""
        if media_type in ("video", "animated_gif"):
            video_info = media.get("video_info", {})
            variants = video_info.get("variants", [])
            mp4_variants = [v for v in variants if v.get("content_type") == "video/mp4"]
            if mp4_variants:
                best_variant = max(mp4_variants, key=lambda v: v.get("bitrate", 0))
                video_url = best_variant.get("url", "")
        original_info = media.get("original_info", {})
        return cls(
            type=media_type,
            url=media.get("expanded_url", ""),
            media_url=media_url,
            video_url=video_url,
            alt_text=media.get("ext_alt_text", ""),
            width=original_info.get("width", 0),
            height=original_info.get("height", 0),
        )


@dataclass
class TweetData:
    """推文数据"""
    id: str = ""
    text: str = ""
    full_text: str = ""
    created_at: str = ""
    author: TweetAuthor = field(default_factory=TweetAuthor)
    media: List[TweetMedia] = field(default_factory=list)
    quoted_tweet: Optional["TweetData"] = None
    retweet_count: int = 0
    like_count: int = 0
    reply_count: int = 0
    view_count: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_tweet_result(cls, tweet_result: Dict[str, Any]) -> "TweetData":
        if not tweet_result:
            return cls()
        result = tweet_result.get("result", {})
        typename = result.get("__typename", "")
        if typename == "TweetWithVisibilityResults":
            result = result.get("tweet", {})
        elif typename == "TweetUnavailable":
            return cls()

        legacy = result.get("legacy", {})
        core = result.get("core", {})
        full_text = legacy.get("full_text", "")

        note_tweet = result.get("note_tweet", {})
        if note_tweet:
            note_results = note_tweet.get("note_tweet_results", {})
            note_result = note_results.get("result", {})
            note_text = note_result.get("text", "")
            if note_text:
                full_text = note_text

        article = result.get("article", {})
        if article:
            article_results = article.get("article_results", {})
            article_result = article_results.get("result", {})
            article_text = article_result.get("text", "")
            if article_text:
                full_text = article_text

        author = TweetAuthor.from_user_result(core.get("user_results", {}))
        media_list = []
        extended_entities = legacy.get("extended_entities", {})
        for media_entity in extended_entities.get("media", []):
            media_list.append(TweetMedia.from_media_entity(media_entity))

        quoted_tweet = None
        quoted_status_result = result.get("quoted_status_result", {})
        if quoted_status_result:
            quoted_tweet = cls.from_tweet_result(quoted_status_result)

        view_count_info = result.get("views", {})
        view_count = int(view_count_info.get("count", 0) or 0)

        return cls(
            id=legacy.get("id_str", "") or result.get("rest_id", ""),
            text=legacy.get("full_text", ""),
            full_text=full_text,
            created_at=legacy.get("created_at", ""),
            author=author,
            media=media_list,
            quoted_tweet=quoted_tweet,
            retweet_count=legacy.get("retweet_count", 0),
            like_count=legacy.get("favorite_count", 0),
            reply_count=legacy.get("reply_count", 0),
            view_count=view_count,
            raw_data=result,
        )
