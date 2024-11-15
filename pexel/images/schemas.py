# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-15
# description: Pexels API返回的数据模型

from typing import Optional, List
from pydantic import BaseModel, Field

# 常量配置
MAX_IMAGES_PER_KEYWORD = 20  # 每个关键词最大下载数量
DEFAULT_PER_PAGE = 80  # 每页返回的图片数量
DEFAULT_RETRY_TIMES = 3  # 默认重试次数
DEFAULT_RETRY_DELAY = 1  # 默认重试延迟(秒)
DEFAULT_MAX_REQUESTS = 25000  # 默认每个API KEY的最大请求次数


class PhotoSource(BaseModel):
    original: str
    large2x: str
    large: str
    medium: str
    small: str
    portrait: str
    landscape: str
    tiny: str


class Photo(BaseModel):
    id: int
    width: int
    height: int
    url: str
    photographer: str
    photographer_url: str
    photographer_id: int
    avg_color: str
    src: PhotoSource
    liked: bool
    alt: str


class SearchResponse(BaseModel):
    page: int
    per_page: int
    photos: List[Photo]
    total_results: int
    next_page: Optional[str] = None

    @property
    def has_next_page(self) -> bool:
        """检查是否有下一页结果。

        Returns:
            bool: 如果有下一页返回True,否则返回False。
        """
        return self.next_page is not None

    @property
    def total_pages(self) -> int:
        """计算搜索结果的总页数。

        Returns:
            int: 总页数。
        """
        return (self.total_results + self.per_page - 1) // self.per_page


class ProxyAuth(BaseModel):
    """代理认证信息"""

    username: str
    password: str


class ProxyConfig(BaseModel):
    """代理配置"""

    host: str
    port: int
    auth: Optional[ProxyAuth] = None
    protocol: str = "http"

    def to_proxy_dict(self) -> dict:
        """转换为requests库使用的代理格式。

        Returns:
            dict: 包含http和https代理配置的字典,格式如:
                {
                    "http": "http://user:pass@host:port",
                    "https": "https://user:pass@host:port"
                }
        """
        auth_str = f"{self.auth.username}:{self.auth.password}@" if self.auth else ""
        proxy_str = f"{self.protocol}://{auth_str}{self.host}:{self.port}"
        return {"http": proxy_str, "https": proxy_str}
