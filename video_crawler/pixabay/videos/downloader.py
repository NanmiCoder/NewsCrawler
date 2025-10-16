import json
import logging
import os
import time
from typing import Generator, Optional
from datetime import datetime
import pytz

import requests
from common.base import PixabayBaseAPI

from .schemas import Video, VideoSearchResponse

logger = logging.getLogger("PixabayDownloader")


class PixabayVideoAPI(PixabayBaseAPI):
    """处理Pixabay视频API的类"""

    BASE_URL = "https://pixabay.com/api/videos"

    def search_resources(
        self, query: str, per_page: int, page: int
    ) -> VideoSearchResponse:
        """搜索视频

        Args:
            query: 关键词
            per_page: 每页数量
            page: 页码

        Returns:
            VideoSearchResponse: 视频搜索响应
        """
        params = {
            "q": query,
            "per_page": per_page,
            "page": page,
            "key": self.api_key_pool.get_key(),
        }

        logger.info(f"开始搜索视频关键词: {query}, 页码: {page}, 每页数量: {per_page}")

        for attempt in range(self.retry_times):
            try:
                response = requests.get(
                    self.BASE_URL, params=params, proxies=self._get_proxies()
                )
                response.raise_for_status()
                self._update_rate_limit(params["key"], response)
                search_response = VideoSearchResponse(**response.json())
                logger.info(f"搜索成功, 共找到 {search_response.total} 个视频")
                return search_response
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_times - 1:
                    logger.error(f"搜索失败: {str(e)}")
                    raise
                logger.warning(f"搜索失败，正在进行第{attempt + 1}次重试")
                time.sleep(self.retry_delay)

    def search_all_videos(
        self,
        query: str,
        max_videos: Optional[int] = None,
        per_page: int = 80,
    ) -> Generator[Video, None, None]:
        """搜索所有视频的生成器

        Args:
            query: 关键词
            max_videos: 最大视频数量
            per_page: 每页数量

        Returns:
            Generator[Video, None, None]: 视频生成器
        """
        page = 1
        total_yielded = 0

        while True:
            if max_videos is not None:
                remaining = max_videos - total_yielded
                if remaining <= 0:
                    break
                current_per_page = min(remaining, per_page)
            else:
                current_per_page = per_page

            response = self.search_resources(query, current_per_page, page)

            for video in response.hits:
                yield video
                total_yielded += 1
                if max_videos is not None and total_yielded >= max_videos:
                    return

            if not response.has_next_page:
                break
            page += 1


class VideoDownloader:
    """处理视频下载的类"""

    def __init__(self, save_dir: str = "downloads"):
        self.save_dir = save_dir
        self._create_dirs()
        logger.info(f"初始化视频下载器，保存目录: {save_dir}")

    def _create_dirs(self):
        os.makedirs(os.path.join(self.save_dir, "videos"), exist_ok=True)

    def _get_formatted_filename(self, text: str) -> str:
        """格式化文件名，将空格替换为横线"""
        return text.replace(" ", "-")

    def download_video(self, keyword: str, video: Video) -> bool:
        """下载所有质量的视频和保存元数据"""
        video_id = str(video.id)
        formatted_keyword = self._get_formatted_filename(keyword)

        # 添加创建时间
        cst = pytz.timezone("Asia/Shanghai")
        create_at = datetime.now(cst).strftime("%Y-%m-%d-%H:%M:%S")

        # 保存元数据
        metadata_path = os.path.join(
            self.save_dir,
            "videos",
            f"{formatted_keyword}_{video_id}.json",
        )

        try:
            # 保存元数据
            with open(metadata_path, "w", encoding="utf-8") as f:
                meta_data = video.model_dump()
                meta_data["search_source_keyword"] = keyword
                meta_data["create_at"] = create_at
                json.dump(meta_data, f, ensure_ascii=False, indent=2)

            # 下载所有质量的视频
            success_count = 0
            for quality, video_file in video.videos.items():
                width = video_file.width
                height = video_file.height

                video_path = os.path.join(
                    self.save_dir,
                    "videos",
                    f"{formatted_keyword}_{video_id}_{width}_{height}.mp4",
                )

                logger.info(
                    f"开始下载视频: {video_id} ({width}x{height})，关键词: {keyword}"
                )
                response = requests.get(video_file.url)
                response.raise_for_status()

                with open(video_path, "wb") as f:
                    f.write(response.content)
                success_count += 1

            return success_count > 0

        except Exception as e:
            logger.error(f"下载视频 {video_id} 失败: {str(e)}")
            return False
