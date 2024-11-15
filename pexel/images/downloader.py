# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-15
# description: Pexels API图片下载器

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Generator
import random
import time
from .schemas import (
    SearchResponse,
    Photo,
    DEFAULT_PER_PAGE,
    DEFAULT_RETRY_TIMES,
    DEFAULT_RETRY_DELAY,
    DEFAULT_MAX_REQUESTS,
)
from .proxy import ProxyProvider

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


class PexelsAPI:
    """处理Pexels API的类"""

    BASE_URL = "https://api.pexels.com/v1"

    def __init__(
        self,
        api_key_pool: APIKeyPool,
        proxy_provider: Optional[ProxyProvider] = None,
        retry_times: int = DEFAULT_RETRY_TIMES,
        retry_delay: int = DEFAULT_RETRY_DELAY,
    ):
        """初始化Pexels API客户端。

        Args:
            api_key_pool: API密钥池。
            proxy_provider: 代理提供者,默认为None。
            retry_times: 重试次数,默认3次。
            retry_delay: 重试延迟时间(秒),默认1秒。
        """
        self.api_key_pool = api_key_pool
        self.proxy_provider = proxy_provider
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        logger.info("初始化Pexels API客户端完成")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头。

        Returns:
            dict: 包含Authorization的请求头。
        """
        return {"Authorization": self.api_key_pool.get_key()}

    def _get_proxies(self) -> Optional[Dict[str, str]]:
        """获取代理配置。

        Returns:
            dict | None: 代理配置字典,如果没有配置代理则返回None。
        """
        if not self.proxy_provider:
            return None
        proxy_config = self.proxy_provider.get_proxy()
        return proxy_config.to_proxy_dict()

    def _update_rate_limit(self, response):
        """更新API限制信息。

        Args:
            response: requests响应对象。
        """
        current_key = response.request.headers["Authorization"]
        remaining = int(response.headers.get("X-Ratelimit-Remaining", 0))
        self.api_key_pool.update_remaining_requests(current_key, remaining)

    def search_photos(
        self, query: str, per_page: int = DEFAULT_PER_PAGE, page: int = 1
    ) -> SearchResponse:
        """搜索图片。

        Args:
            query: 搜索关键词。
            per_page: 每页返回的图片数量,默认80。
            page: 页码,默认1。

        Returns:
            SearchResponse: 搜索响应对象。

        Raises:
            requests.exceptions.RequestException: 当请求失败且重试次数用完时抛出异常。
        """
        endpoint = f"{self.BASE_URL}/search"
        params = {"query": query, "per_page": per_page, "page": page}

        logger.info(f"开始搜索关键词: {query}, 页码: {page}, 每页数量: {per_page}")

        for attempt in range(self.retry_times):
            try:
                response = requests.get(
                    endpoint,
                    headers=self._get_headers(),
                    params=params,
                    proxies=self._get_proxies(),
                )
                response.raise_for_status()
                self._update_rate_limit(response)
                search_response = SearchResponse(**response.json())
                logger.info(f"搜索成功, 共找到 {search_response.total_results} 张图片")
                return search_response
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_times - 1:
                    logger.error(f"搜索失败: {str(e)}")
                    raise
                logger.warning(f"搜索失败，正在进行第{attempt + 1}次重试")
                time.sleep(self.retry_delay)
                continue

    def search_all_photos(
        self,
        query: str,
        max_photos: Optional[int] = None,
        per_page: int = DEFAULT_PER_PAGE,
    ) -> Generator[Photo, None, None]:
        """搜索所有图片的生成器。

        Args:
            query: 搜索关键词。
            max_photos: 最大返回图片数量，None表示返回所有结果。
            per_page: 每页返回的图片数量,默认80。

        Yields:
            Photo: 图片对象。
        """
        page = 1
        total_yielded = 0

        while True:
            if max_photos is not None:
                remaining = max_photos - total_yielded
                if remaining <= 0:
                    logger.info(f"已达到最大图片数量限制: {max_photos}")
                    break
                current_per_page = min(remaining, per_page)
            else:
                current_per_page = per_page

            response = self.search_photos(query, per_page=current_per_page, page=page)

            for photo in response.photos:
                yield photo
                total_yielded += 1
                if max_photos is not None and total_yielded >= max_photos:
                    return

            if not response.has_next_page:
                logger.info(f"已获取所有图片，共 {total_yielded} 张")
                break
            page += 1


class ImageDownloader:
    """处理图片下载的类"""

    def __init__(self, save_dir: str = "downloads"):
        """初始化图片下载器。

        Args:
            save_dir: 保存目录路径,默认为"downloads"。
        """
        self.save_dir = save_dir
        self._create_dirs()
        logger.info(f"初始化图片下载器，保存目录: {save_dir}")

    def _create_dirs(self):
        """创建保存图片和元数据的目录。"""
        os.makedirs(os.path.join(self.save_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.save_dir, "metadata"), exist_ok=True)

    def download_image(self, photo: Photo) -> bool:
        """下载单张图片和保存元数据。

        Args:
            photo: Photo模型实例。

        Returns:
            bool: 下载是否成功。
        """
        photo_id = str(photo.id)
        image_url = str(photo.src.original)

        image_path = os.path.join(self.save_dir, "images", f"{photo_id}.jpg")
        metadata_path = os.path.join(self.save_dir, "metadata", f"{photo_id}.json")

        try:
            logger.info(f"开始下载图片: {photo_id}")
            response = requests.get(image_url)
            response.raise_for_status()

            with open(image_path, "wb") as f:
                f.write(response.content)

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(photo.model_dump(), f, ensure_ascii=False, indent=2)

            logger.info(f"图片 {photo_id} 下载成功")
            return True

        except Exception as e:
            logger.error(f"下载图片 {photo_id} 失败: {str(e)}")
            return False
