# -*- coding: utf-8 -*-
"""
共享配置
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据保存目录
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# 临时文件目录
TEMP_DIR = PROJECT_ROOT / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 支持的平台列表
SUPPORTED_PLATFORMS = [
    {"id": "wechat", "name": "微信公众号", "icon": "💬"},
    {"id": "toutiao", "name": "今日头条", "icon": "📰"},
    {"id": "netease", "name": "网易新闻", "icon": "📰"},
    {"id": "sohu", "name": "搜狐新闻", "icon": "📰"},
    {"id": "tencent", "name": "腾讯新闻", "icon": "📰"},
    {"id": "detik", "name": "Detik News", "icon": "🌏"},
    {"id": "naver", "name": "Naver News", "icon": "🇰🇷"},
    {"id": "lenny", "name": "Lenny's Newsletter", "icon": "📮"},
    {"id": "quora", "name": "Quora", "icon": "❓"},
]
