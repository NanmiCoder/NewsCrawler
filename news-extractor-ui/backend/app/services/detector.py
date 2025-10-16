# -*- coding: utf-8 -*-
"""
平台检测服务
"""
import re
from typing import Optional


PLATFORM_PATTERNS = {
    "toutiao": r"https?://www\.toutiao\.com/article/",
    "wechat": r"https?://mp\.weixin\.qq\.com/s/",
    "netease": r"https?://www\.163\.com/news/article/",
    "detik": r"https?://news\.detik\.com/",
    "naver": r"https?://.*\.naver\.com/",
    "lenny": r"https?://www\.lennysnewsletter\.com/",
    "quora": r"https?://.*\.quora\.com/"
}


def detect_platform(url: str) -> Optional[str]:
    """
    根据 URL 检测平台类型

    Args:
        url: 新闻链接

    Returns:
        平台名称，如果无法识别则返回 None
    """
    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.match(pattern, url):
            return platform
    return None


def get_supported_platforms() -> list[dict]:
    """获取支持的平台列表"""
    return [
        {"id": "toutiao", "name": "今日头条", "icon": "📰"},
        {"id": "wechat", "name": "微信公众号", "icon": "💬"},
        {"id": "netease", "name": "网易新闻", "icon": "📰"},
        {"id": "detik", "name": "Detik News", "icon": "🌏"},
        {"id": "naver", "name": "Naver News", "icon": "🇰🇷"},
        {"id": "lenny", "name": "Lenny's Newsletter", "icon": "📮"},
        {"id": "quora", "name": "Quora", "icon": "❓"}
    ]
