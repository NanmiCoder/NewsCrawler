# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-15
# description: Pexels API图片下载器

import json
import logging
import os
import time
from typing import Generator, Optional

import requests
from common.base import PexelsBaseAPI

from .schemas import Photo, PhotoSearchResponse

logger = logging.getLogger("PexelsDownloader")


class PexelsAPI(PexelsBaseAPI):
    """处理Pexels图片API的类"""

    def search_resources(
        self, query: str, per_page: int, page: int
    ) -> PhotoSearchResponse:
        """搜索图片。

        Args:
            query: 搜索关键词。
            per_page: 每页返回的图片数量。
            page: 页码。

        Returns:
            PhotoSearchResponse: 搜索响应对象。

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
                search_response = PhotoSearchResponse(**response.json())
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
        per_page: int = 80,
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

            response = self.search_resources(
                query, per_page=current_per_page, page=page
            )

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
        os.makedirs(os.path.join(self.save_dir, "images_metadata"), exist_ok=True)

    def download_image(self, keyword: str, photo: Photo) -> bool:
        """下载单张图片和保存元数据。

        Args:
            keyword: 关键词
            photo: Photo模型实例。

        Returns:
            bool: 下载是否成功。
        """
        photo_id = str(photo.id)
        image_url = str(photo.src.original)

        image_path = os.path.join(self.save_dir, "images", keyword, f"{photo_id}.jpg")
        metadata_path = os.path.join(
            self.save_dir, "images_metadata", keyword, f"{photo_id}.json"
        )

        # for image keyword
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

        try:
            logger.info(f"开始下载图片: {photo_id}，关键词: {keyword}")
            response = requests.get(image_url)
            response.raise_for_status()

            with open(image_path, "wb") as f:
                f.write(response.content)

            with open(metadata_path, "w", encoding="utf-8") as f:
                meta_data = photo.model_dump()
                meta_data["search_source_keyword"] = keyword
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
            return True

        except Exception as e:
            logger.error(f"下载图片 {photo_id} 失败: {str(e)}")
            return False
