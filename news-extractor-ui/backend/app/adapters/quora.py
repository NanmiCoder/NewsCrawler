# -*- coding: utf-8 -*-
"""
Quora 爬虫适配器
"""
from .base import CrawlerAdapter, NewsItem
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

        # 直接调用内部方法获取数据
        html = crawler.fetch_content()
        answer_item = crawler.parse_content(html)

        # Quora 使用 AnwserItem，需要转换字段名以适配统一的 NewsItem
        answer_dict = answer_item.model_dump()

        # 将 anwser_url 转换为 news_url，anwser_id 转换为 news_id
        news_dict = {
            "title": answer_dict.get("title", ""),
            "news_url": answer_dict.get("anwser_url", ""),
            "news_id": answer_dict.get("anwser_id", ""),
            "meta_info": answer_dict.get("meta_info", {}),
            "contents": answer_dict.get("contents", []),
            "texts": answer_dict.get("texts", []),
            "images": answer_dict.get("images", []),
            "videos": answer_dict.get("videos", [])
        }

        # 转换为统一格式
        return NewsItem(news_dict)
