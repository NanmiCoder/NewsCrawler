# -*- coding: utf-8 -*-
"""
爬虫适配器基类
"""
from abc import ABC, abstractmethod
from ..models import NewsItem


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
