# -*- coding: utf-8 -*-
"""
Quora 爬虫适配器
"""
from .base import CrawlerAdapter
from ..models import NewsItem
from news_crawler.quora import QuoraAnswerCrawler, RequestHeaders


class QuoraAdapter(CrawlerAdapter):
    """Quora 适配器"""

    @property
    def platform_name(self) -> str:
        return "quora"

    def extract(self, url: str) -> NewsItem:
        """提取 Quora 回答"""
        # 创建爬虫实例（使用临时路径，不实际保存文件）
        import tempfile
        temp_dir = tempfile.mkdtemp()

        crawler = QuoraAnswerCrawler(url, save_path=temp_dir, headers=RequestHeaders())

        html = crawler.fetch_content()
        answer_item = crawler.parse_content(html)

        return NewsItem(answer_item.to_dict())
