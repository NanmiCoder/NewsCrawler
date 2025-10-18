# -*- coding: utf-8 -*-
"""
微信公众号爬虫适配器
"""
from .base import CrawlerAdapter
from ..models import NewsItem
from news_crawler.wechat_news import WeChatNewsCrawler, RequestHeaders


class WeChatAdapter(CrawlerAdapter):
    """微信公众号适配器"""

    @property
    def platform_name(self) -> str:
        return "wechat"

    def extract(self, url: str) -> NewsItem:
        """提取微信公众号文章"""
        # 创建爬虫实例（使用临时路径，不实际保存文件）
        import tempfile
        temp_dir = tempfile.mkdtemp()

        crawler = WeChatNewsCrawler(url, save_path=temp_dir, headers=RequestHeaders())

        # 直接调用内部方法获取数据
        html = crawler.fetch_content()
        news_item = crawler.parse_content(html)

        # 转换为统一格式
        return NewsItem(news_item.model_dump())
