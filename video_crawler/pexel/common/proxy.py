# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-15
# description: IP代理提供者， 具体的IP代理上实现等到真正下载图片时IP被封了再来实现

import random
from abc import ABC, abstractmethod
from typing import Dict, List

from .schemas import ProxyConfig


class ProxyProvider(ABC):
    """代理提供者的抽象基类"""

    @abstractmethod
    def get_proxy(self) -> ProxyConfig:
        """获取一个代理配置。

        Returns:
            ProxyConfig: 代理配置对象。
        """
        pass


class SimpleProxyProvider(ProxyProvider):
    """简单的代理提供者实现"""

    def __init__(self, proxies: List[ProxyConfig]):
        """初始化简单代理提供者。

        Args:
            proxies: 代理配置列表。
        """
        self.proxies = proxies

    def get_proxy(self) -> ProxyConfig:
        """随机获取一个代理配置。

        Returns:
            ProxyConfig: 随机选择的代理配置。
        """
        return random.choice(self.proxies)


class RotatingProxyProvider(ProxyProvider):
    """轮转的代理提供者实现"""

    def __init__(self, proxies: List[ProxyConfig]):
        """初始化轮转代理提供者。

        Args:
            proxies: 代理配置列表。
        """
        self.proxies = proxies
        self.current_index = 0

    def get_proxy(self) -> ProxyConfig:
        """按顺序轮转获取代理配置。

        Returns:
            ProxyConfig: 当前轮转到的代理配置。
        """
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
