# -*- coding: utf-8 -*-
"""
统一的数据模型定义
兼容 news_crawler 中的 Pydantic 模型
"""
from typing import Dict, Any, List, Optional
from enum import Enum


class ContentType(str, Enum):
    """内容类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ContentItem:
    """内容项"""
    def __init__(self, type: str, content: str, desc: str = ""):
        self.type = type
        self.content = content
        self.desc = desc

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "desc": self.desc
        }


class NewsMetaInfo:
    """新闻元信息"""
    def __init__(
        self,
        author_name: str = "",
        author_url: str = "",
        publish_time: str = "",
        **kwargs
    ):
        self.author_name = author_name
        self.author_url = author_url
        self.publish_time = publish_time
        # 支持额外字段
        self.extra = kwargs

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "author_name": self.author_name,
            "author_url": self.author_url,
            "publish_time": self.publish_time,
        }
        data.update(self.extra)
        return data


class NewsItem:
    """统一的新闻数据模型"""

    def __init__(self, data: Dict[str, Any]):
        self.title = data.get("title", "")
        self.news_url = data.get("news_url", "")
        self.news_id = data.get("news_id", "")

        # 元信息处理
        meta_info = data.get("meta_info", {})
        if isinstance(meta_info, dict):
            self.meta_info = meta_info
        else:
            # 如果是对象,转为字典
            self.meta_info = getattr(meta_info, "model_dump", lambda: meta_info)() if hasattr(meta_info, "model_dump") else {}

        self.contents = data.get("contents", [])
        self.texts = data.get("texts", [])
        self.images = data.get("images", [])
        self.videos = data.get("videos", [])

    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return {
            "title": self.title,
            "news_url": self.news_url,
            "news_id": self.news_id,
            "meta_info": self.meta_info,
            "contents": self.contents,
            "texts": self.texts,
            "images": self.images,
            "videos": self.videos
        }

    @classmethod
    def from_pydantic(cls, pydantic_model) -> "NewsItem":
        """从 Pydantic 模型创建"""
        if hasattr(pydantic_model, "model_dump"):
            data = pydantic_model.model_dump()
        elif hasattr(pydantic_model, "dict"):
            data = pydantic_model.dict()
        else:
            raise ValueError("Invalid pydantic model")
        return cls(data)

    def __repr__(self) -> str:
        return f"<NewsItem title='{self.title[:30]}...' platform='{self.news_url[:50]}...'>"
