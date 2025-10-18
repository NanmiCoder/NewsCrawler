# -*- coding: utf-8 -*-
"""
Lenny's Newsletter 爬虫适配器
"""
from .base import CrawlerAdapter
from ..models import NewsItem
from news_crawler.lennysnewsletter import LennysNewsletterCrawler, RequestHeaders


class LennyAdapter(CrawlerAdapter):
    """Lenny's Newsletter 适配器"""

    @property
    def platform_name(self) -> str:
        return "lenny"

    def extract(self, url: str) -> NewsItem:
        """提取 Lenny's Newsletter 文章"""
        # 创建爬虫实例（使用临时路径，不实际保存文件）
        import tempfile
        temp_dir = tempfile.mkdtemp()

        crawler = LennysNewsletterCrawler(url, save_path=temp_dir, headers=RequestHeaders())

        # 直接调用内部方法获取数据
        html = crawler.fetch_content()
        news_item = crawler.parse_content(html)

        # 转换为统一格式
        return NewsItem(news_item.model_dump())
