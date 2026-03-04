# -*- coding: utf-8 -*-
"""
爬虫模块
"""
from .wechat import WeChatNewsCrawler
from .toutiao import ToutiaoNewsCrawler
from .netease import NeteaseNewsCrawler
from .sohu import SohuNewsCrawler
from .tencent import TencentNewsCrawler
from .bbc import BBCNewsCrawler
from .cnn import CNNNewsCrawler
from .twitter import TwitterNewsCrawler
from .lenny import LennysNewsletterCrawler
from .naver import NaverNewsCrawler
from .detik import DetikNewsCrawler
from .quora import QuoraAnswerCrawler

__all__ = [
    "WeChatNewsCrawler",
    "ToutiaoNewsCrawler",
    "NeteaseNewsCrawler",
    "SohuNewsCrawler",
    "TencentNewsCrawler",
    "BBCNewsCrawler",
    "CNNNewsCrawler",
    "TwitterNewsCrawler",
    "LennysNewsletterCrawler",
    "NaverNewsCrawler",
    "DetikNewsCrawler",
    "QuoraAnswerCrawler",
]
