import logging
import random
import time
from typing import Dict, List, Optional

import requests

from .proxy import ProxyProvider

logger = logging.getLogger("PixabayDownloader")


class APIKeyPool:
    """API密钥池管理类"""

    def __init__(self, api_keys: List[str], max_requests: int = 100):
        """初始化API密钥池。

        Args:
            api_keys: API密钥列表。
            max_requests: 每60秒的最大请求次数,默认100。
        """
        self.api_keys = {
            key: {"remaining": max_requests, "reset": 0} for key in api_keys
        }
        self.current_key = api_keys[0] if api_keys else None
        logger.info(f"初始化API密钥池，共{len(api_keys)}个密钥")

    def get_key(self) -> Optional[str]:
        """获取一个可用的API密钥。

        Returns:
            str | None: 可用的API密钥,如果没有可用密钥则返回None。

        Raises:
            Exception: 当没有可用的API密钥时抛出异常。
        """
        current_time = time.time()
        available_keys = [
            k
            for k, v in self.api_keys.items()
            if v["remaining"] > 0 or current_time >= v["reset"]
        ]

        if not available_keys:
            min_wait_time = (
                min(v["reset"] for v in self.api_keys.values()) - current_time
            )
            if min_wait_time > 0:
                logger.warning(f"所有密钥都达到限制，需要等待 {min_wait_time:.1f} 秒")
                time.sleep(min_wait_time)
                return self.get_key()

            logger.error("没有可用的API密钥")
            raise Exception("没有可用的API密钥")

        if self.current_key not in available_keys:
            self.current_key = random.choice(available_keys)
            if current_time >= self.api_keys[self.current_key]["reset"]:
                self.api_keys[self.current_key]["remaining"] = 100  # 重置配额
            logger.info(f"切换到新的API密钥: {self.current_key[:8]}...")
        return self.current_key

    def update_rate_limit(self, key: str, remaining: int, reset: int):
        """更新密钥的速率限制信息。

        Args:
            key: API密钥。
            remaining: X-RateLimit-Remaining 值。
            reset: X-RateLimit-Reset 值(秒)。
        """
        current_time = time.time()
        self.api_keys[key] = {"remaining": remaining, "reset": current_time + reset}

        if remaining <= 0:
            logger.warning(f"API密钥 {key[:8]}... 已达到限制，将在 {reset} 秒后重置")
            if key == self.current_key:
                self.current_key = self.get_key()


class PixabayBaseAPI:
    """Pixabay API基类"""

    def __init__(
        self,
        api_key_pool: APIKeyPool,
        proxy_provider: Optional[ProxyProvider] = None,
        retry_times: int = 3,
        retry_delay: int = 1,
    ):
        """初始化Pixabay API基类

        Args:
            api_key_pool: API密钥池
            proxy_provider: 代理提供者
            retry_times: 重试次数
            retry_delay: 重试延迟
        """
        self.api_key_pool = api_key_pool
        self.proxy_provider = proxy_provider
        self.retry_times = retry_times
        self.retry_delay = retry_delay

    def _get_proxies(self) -> Optional[Dict[str, str]]:
        """获取代理配置

        Returns:
            Dict[str, str] | None: 代理配置, 如果没有代理则返回None
        """
        if not self.proxy_provider:
            return None
        proxy_config = self.proxy_provider.get_proxy()
        return proxy_config.to_proxy_dict()

    def _update_rate_limit(self, current_key: str, response: requests.Response):
        """更新API密钥的速率限制信息

        Args:
            current_key: 当前使用的API密钥
            response: 响应

        Raises:
            Exception: 当响应状态码不是200时抛出异常
        """
        remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        reset = int(response.headers.get("X-RateLimit-Reset", 60))
        self.api_key_pool.update_rate_limit(current_key, remaining, reset)
