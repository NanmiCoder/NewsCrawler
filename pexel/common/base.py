import logging
import random
from typing import Dict, List, Optional

from .proxy import ProxyProvider
from .schemas import DEFAULT_MAX_REQUESTS

logger = logging.getLogger("PexelsDownloader")


class APIKeyPool:
    """API密钥池管理类"""

    def __init__(self, api_keys: List[str], max_requests: int = DEFAULT_MAX_REQUESTS):
        """初始化API密钥池。

        Args:
            api_keys: API密钥列表。
            max_requests: 每个密钥的最大请求次数,默认25000。
        """
        self.api_keys = {key: max_requests for key in api_keys}
        self.current_key = api_keys[0] if api_keys else None
        logger.info(f"初始化API密钥池，共{len(api_keys)}个密钥")

    def get_key(self) -> Optional[str]:
        """获取一个可用的API密钥。

        Returns:
            str | None: 可用的API密钥,如果没有可用密钥则返回None。

        Raises:
            Exception: 当没有可用的API密钥时抛出异常。
        """
        available_keys = [k for k, v in self.api_keys.items() if v > 0]
        if not available_keys:
            logger.error("没有可用的API密钥")
            raise Exception("没有可用的API密钥")

        if self.current_key not in available_keys:
            self.current_key = random.choice(available_keys)
            logger.info(f"切换到新的API密钥: {self.current_key[:8]}...")
        return self.current_key

    def update_remaining_requests(self, key: str, remaining: int):
        """更新密钥的剩余请求次数。

        Args:
            key: API密钥。
            remaining: 剩余的请求次数。
        """
        self.api_keys[key] = remaining
        if remaining <= 0:
            logger.warning(f"API密钥 {key[:8]}... 已达到限制")
            if key == self.current_key:
                self.current_key = self.get_key()


class PexelsBaseAPI:
    """Pexels API基类"""

    BASE_URL = "https://api.pexels.com/v1"

    def __init__(
        self,
        api_key_pool: "APIKeyPool",
        proxy_provider: Optional[ProxyProvider] = None,
        retry_times: int = 3,
        retry_delay: int = 1,
    ):
        self.api_key_pool = api_key_pool
        self.proxy_provider = proxy_provider
        self.retry_times = retry_times
        self.retry_delay = retry_delay

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": self.api_key_pool.get_key()}

    def _get_proxies(self) -> Optional[Dict[str, str]]:
        if not self.proxy_provider:
            return None
        proxy_config = self.proxy_provider.get_proxy()
        return proxy_config.to_proxy_dict()

    def _update_rate_limit(self, response):
        current_key = response.request.headers["Authorization"]
        remaining = int(response.headers.get("X-Ratelimit-Remaining", 0))
        self.api_key_pool.update_remaining_requests(current_key, remaining)
