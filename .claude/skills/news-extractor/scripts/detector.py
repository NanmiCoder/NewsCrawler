# -*- coding: utf-8 -*-
"""
平台检测服务
"""
import re
from typing import Optional


# 新闻平台 URL 模式
PLATFORM_PATTERNS = {
    # 中文平台
    "wechat": r"https?://mp\.weixin\.qq\.com/s/",
    "toutiao": r"https?://www\.toutiao\.com/article/",
    "netease": r"https?://www\.163\.com/(news|dy)/article/",
    "sohu": r"https?://www\.sohu\.com/a/",
    "tencent": r"https?://news\.qq\.com/rain/a/",
    # 国际平台
    "bbc": r"https?://www\.bbc\.com/news/articles/",
    "cnn": r"https?://edition\.cnn\.com/.+",
    "twitter": r"https?://(x\.com|twitter\.com)/.+/status/",
    "lenny": r"https?://www\.lennysnewsletter\.com/p/",
    "naver": r"https?://blog\.naver\.com/",
    "detik": r"https?://news\.detik\.com/",
    "quora": r"https?://www\.quora\.com/",
}

# 平台名称映射
PLATFORM_NAMES = {
    # 中文平台
    "wechat": "微信公众号",
    "toutiao": "今日头条",
    "netease": "网易新闻",
    "sohu": "搜狐新闻",
    "tencent": "腾讯新闻",
    # 国际平台
    "bbc": "BBC News",
    "cnn": "CNN News",
    "twitter": "Twitter/X",
    "lenny": "Lenny's Newsletter",
    "naver": "Naver Blog",
    "detik": "Detik News",
    "quora": "Quora",
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


def get_platform_name(platform_id: str) -> str:
    """获取平台名称"""
    return PLATFORM_NAMES.get(platform_id, platform_id)


def get_supported_platforms() -> list[dict]:
    """获取支持的平台列表"""
    return [
        {"id": pid, "name": pname}
        for pid, pname in PLATFORM_NAMES.items()
    ]
