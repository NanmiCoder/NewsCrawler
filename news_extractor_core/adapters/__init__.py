# -*- coding: utf-8 -*-
"""
爬虫适配器模块
"""
from .base import CrawlerAdapter
from .wechat import WeChatAdapter
from .toutiao import ToutiaoAdapter
from .netease import NeteaseAdapter
from .sohu import SohuAdapter
from .tencent import TencentAdapter
from .detik import DetikAdapter
from .lenny import LennyAdapter
from .naver import NaverAdapter
from .quora import QuoraAdapter
from .bbc import BBCAdapter

__all__ = [
    "CrawlerAdapter",
    "WeChatAdapter",
    "ToutiaoAdapter",
    "NeteaseAdapter",
    "SohuAdapter",
    "TencentAdapter",
    "DetikAdapter",
    "LennyAdapter",
    "NaverAdapter",
    "QuoraAdapter",
    "BBCAdapter",
]
