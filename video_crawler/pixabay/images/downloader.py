import json
import logging
import os
import time
from typing import Generator, Optional
from datetime import datetime
import pytz

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
        """搜索图片

        Args:
            query: 关键词
            per_page: 每页数量
            page: 页码

        Returns:
            ImageSearchResponse: 图片搜索响应
        """
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
        """搜索所有图片的生成器

        Args:
            query: 关键词
            max_images: 最大图片数量
            per_page: 每页数量

        Returns:
            Generator[Image, None, None]: 图片生成器
        """
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

    def _get_formatted_filename(self, text: str) -> str:
        """格式化文件名，将空格替换为横线"""
        return text.replace(" ", "-")

    def download_image(self, keyword: str, image: Image) -> bool:
        """下载所有质量的图片和保存元数据"""
        image_id = str(image.id)
        formatted_keyword = self._get_formatted_filename(keyword)
        formatted_tags = self._get_formatted_filename(image.tags)

        # 添加创建时间
        cst = pytz.timezone("Asia/Shanghai")
        create_at = datetime.now(cst).strftime("%Y-%m-%d-%H:%M:%S")

        # 保存元数据
        metadata_path = os.path.join(
            self.save_dir,
            "images",
            f"{formatted_keyword}_{image_id}_{formatted_tags}.json",
        )

        try:
            # 保存元数据
            with open(metadata_path, "w", encoding="utf-8") as f:
                meta_data = image.model_dump()
                meta_data["search_source_keyword"] = keyword
                meta_data["create_at"] = create_at
                json.dump(meta_data, f, ensure_ascii=False, indent=2)

            # 下载所有质量的图片
            success_count = 0

            # webformatURL: 640px 的图片
            # largeImageURL: 1280px 的图片
            # fullHDURL: 1920px 的图片（如果有）
            # imageURL: 原始分辨率（如果有）
            quality_urls = [
                (
                    image.preview_url,
                    f"{image.preview_width}x{image.preview_height}",
                ),  # 150px 预览图
                (
                    image.webformat_url,
                    f"{image.webformat_width}x{image.webformat_height}",
                ),  # 640px
                (
                    image.large_image_url,
                    f"{image.image_width}x{image.image_height}_large",
                ),  # 1280px
            ]

            # 添加可选的更高质量版本
            if image.full_hd_url:
                quality_urls.append((image.full_hd_url, "1920x1080"))  # fullHD 1920px
            if image.image_url:
                quality_urls.append(
                    (
                        image.image_url,
                        f"{image.image_width}x{image.image_height}",
                    )  # 原始分辨率
                )

            for url, resolution in quality_urls:
                if not url:
                    continue

                image_path = os.path.join(
                    self.save_dir,
                    "images",
                    f"{formatted_keyword}_{image_id}_{formatted_tags}_{resolution}.jpg",
                )

                logger.info(
                    f"开始下载图片: {image_id} ({resolution})，关键词: {keyword}"
                )
                response = requests.get(url)
                response.raise_for_status()

                with open(image_path, "wb") as f:
                    f.write(response.content)
                success_count += 1

            return success_count > 0

        except Exception as e:
            logger.error(f"下载图片 {image_id} 失败: {str(e)}")
            return False
