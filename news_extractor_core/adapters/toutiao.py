# -*- coding: utf-8 -*-
"""
今日头条爬虫适配器
"""
from .base import CrawlerAdapter
from ..models import NewsItem
from news_crawler.toutiao_news import ToutiaoNewsCrawler, RequestHeaders


class ToutiaoAdapter(CrawlerAdapter):
    """今日头条适配器"""

    @property
    def platform_name(self) -> str:
        return "toutiao"

    def extract(self, url: str) -> NewsItem:
        """提取今日头条文章"""
        # 创建爬虫实例（使用临时路径，不实际保存文件）
        import tempfile
        temp_dir = tempfile.mkdtemp()

        crawler = ToutiaoNewsCrawler(url, save_path=temp_dir, headers=RequestHeaders())

        # 直接调用内部方法获取数据
        html = crawler.fetch_content()
        news_item = crawler.parse_content(html)

        # 转换为统一格式
        return NewsItem(news_item.model_dump())
