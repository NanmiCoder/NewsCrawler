# -*- coding: utf-8 -*-
"""
News Extractor Core Package
共享的核心业务逻辑、数据模型和适配器
"""
__version__ = "0.1.0"

from .models import NewsItem, NewsMetaInfo, ContentItem, ContentType

__all__ = [
    "NewsItem",
    "NewsMetaInfo",
    "ContentItem",
    "ContentType",
]
