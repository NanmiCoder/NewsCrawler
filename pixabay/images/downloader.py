import json
import logging
import os
import time
from typing import Generator, Optional

import requests
from common.base import PixabayBaseAPI

from .schemas import Image, ImageSearchResponse

logger = logging.getLogger("PixabayDownloader")


class PixabayAPI(PixabayBaseAPI):
    """处理Pixabay图片API的类"""

    BASE_URL = "https://pixabay.com/api"

    def search_resources(
        self, query: str, per_page: int, page: int
    ) -> ImageSearchResponse:
        """搜索图片"""
        params = {
            "q": query,
            "per_page": per_page,
            "page": page,
            "key": self.api_key_pool.get_key(),
        }

        logger.info(f"开始搜索关键词: {query}, 页码: {page}, 每页数量: {per_page}")

        for attempt in range(self.retry_times):
            try:
                response = requests.get(
                    self.BASE_URL, params=params, proxies=self._get_proxies()
                )
                response.raise_for_status()
                self._update_rate_limit(params["key"], response)
                search_response = ImageSearchResponse(**response.json())
                logger.info(f"搜索成功, 共找到 {search_response.total} 张图片")
                return search_response
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_times - 1:
                    logger.error(f"搜索失败: {str(e)}")
                    raise
                logger.warning(f"搜索失败，正在进行第{attempt + 1}次重试")
                time.sleep(self.retry_delay)

    def search_all_images(
        self,
        query: str,
        max_images: Optional[int] = None,
        per_page: int = 80,
    ) -> Generator[Image, None, None]:
        """搜索所有图片的生成器"""
        page = 1
        total_yielded = 0

        while True:
            if max_images is not None:
                remaining = max_images - total_yielded
                if remaining <= 0:
                    break
                current_per_page = min(remaining, per_page)
            else:
                current_per_page = per_page

            response = self.search_resources(query, current_per_page, page)

            for image in response.hits:
                yield image
                total_yielded += 1
                if max_images is not None and total_yielded >= max_images:
                    return

            if not response.has_next_page:
                break
            page += 1


class ImageDownloader:
    """处理图片下载的类"""

    def __init__(self, save_dir: str = "downloads"):
        self.save_dir = save_dir
        self._create_dirs()
        logger.info(f"初始化图片下载器，保存目录: {save_dir}")

    def _create_dirs(self):
        os.makedirs(os.path.join(self.save_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.save_dir, "images_metadata"), exist_ok=True)

    def download_image(self, image: Image) -> bool:
        """下载单张图片和保存元数据"""
        image_id = str(image.id)
        image_url = image.large_image_url

        image_path = os.path.join(self.save_dir, "images", f"{image_id}.jpg")
        metadata_path = os.path.join(
            self.save_dir, "images_metadata", f"{image_id}.json"
        )

        try:
            logger.info(f"开始下载图片: {image_id}")
            response = requests.get(image_url)
            response.raise_for_status()

            with open(image_path, "wb") as f:
                f.write(response.content)

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(image.model_dump(), f, ensure_ascii=False, indent=2)

            logger.info(f"图片 {image_id} 下载成功")
            return True

        except Exception as e:
            logger.error(f"下载图片 {image_id} 失败: {str(e)}")
            return False
