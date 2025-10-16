# -*- coding: utf-8 -*-
"""
爬虫适配器基类
"""
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到 sys.path，以便导入爬虫模块
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class NewsItem:
    """统一的新闻数据模型"""
    def __init__(self, data: Dict[str, Any]):
        self.title = data.get("title", "")
        self.news_url = data.get("news_url", "")
        self.news_id = data.get("news_id", "")
        self.meta_info = data.get("meta_info", {})
        self.contents = data.get("contents", [])
        self.texts = data.get("texts", [])
        self.images = data.get("images", [])
        self.videos = data.get("videos", [])

    def to_dict(self) -> Dict[str, Any]:
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


class CrawlerAdapter(ABC):
    """爬虫适配器抽象基类"""

    @abstractmethod
    def extract(self, url: str) -> NewsItem:
        """
        提取新闻内容

        Args:
            url: 新闻链接

        Returns:
            NewsItem: 提取的新闻数据
        """
        pass

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台名称"""
        pass
