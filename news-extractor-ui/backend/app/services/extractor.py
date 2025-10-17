# -*- coding: utf-8 -*-
"""
新闻提取服务
"""
from typing import Optional
from ..adapters.base import CrawlerAdapter, NewsItem
from ..adapters.wechat import WeChatAdapter
from ..adapters.toutiao import ToutiaoAdapter
from ..adapters.netease import NeteaseAdapter
from ..adapters.sohu import SohuAdapter
from ..adapters.tencent import TencentAdapter
from ..adapters.detik import DetikAdapter
from ..adapters.lenny import LennyAdapter
from ..adapters.naver import NaverAdapter
from ..adapters.quora import QuoraAdapter
from .detector import detect_platform


# 适配器注册表
ADAPTERS = {
    "wechat": WeChatAdapter(),
    "toutiao": ToutiaoAdapter(),
    "netease": NeteaseAdapter(),
    "sohu": SohuAdapter(),
    "tencent": TencentAdapter(),
    "detik": DetikAdapter(),
    "lenny": LennyAdapter(),
    "naver": NaverAdapter(),
    "quora": QuoraAdapter(),
}


class ExtractorService:
    """新闻提取服务"""

    @staticmethod
    def extract_news(url: str, platform: Optional[str] = None) -> tuple[NewsItem, str]:
        """
        提取新闻内容

        Args:
            url: 新闻链接
            platform: 指定平台（可选，如果不指定则自动检测）

        Returns:
            (NewsItem, platform_name): 提取的新闻数据和平台名称

        Raises:
            ValueError: 如果平台不支持或 URL 无效
        """
        # 自动检测平台
        if platform is None:
            platform = detect_platform(url)

        if platform is None:
            raise ValueError("无法识别该平台，请检查 URL 是否正确")

        # 获取适配器
        adapter = ADAPTERS.get(platform)
        if adapter is None:
            raise ValueError(f"平台 '{platform}' 暂不支持")

        # 提取数据
        try:
            news_item = adapter.extract(url)
            return news_item, platform
        except Exception as e:
            raise ValueError(f"提取失败: {str(e)}")
