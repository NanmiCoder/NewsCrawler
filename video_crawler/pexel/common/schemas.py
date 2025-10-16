from typing import Any, List, Optional

from pydantic import BaseModel, Field

# 常量配置
MAX_RESOURCES_PER_KEYWORD = 10  # 每个关键词最大下载数量
DEFAULT_PER_PAGE = 80  # 每页返回的资源数量
DEFAULT_RETRY_TIMES = 3  # 默认重试次数
DEFAULT_RETRY_DELAY = 1  # 默认重试延迟(秒)
DEFAULT_MAX_REQUESTS = 25000  # 默认每个API KEY的最大请求次数


class BaseResource(BaseModel):
    """基础资源模型"""

    id: int
    width: int
    height: int
    url: str


class BaseSearchResponse(BaseModel):
    """基础搜索响应"""

    page: int
    per_page: int
    total_results: int
    next_page: Optional[str] = None

    @property
    def has_next_page(self) -> bool:
        return self.next_page is not None

    @property
    def total_pages(self) -> int:
        return (self.total_results + self.per_page - 1) // self.per_page

    def get_resources(self) -> List[BaseResource]:
        """获取资源列表"""
        raise NotImplementedError


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
