import json
import logging
import os
import time
from typing import Generator, Optional

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
        os.makedirs(os.path.join(self.save_dir, "videos_metadata"), exist_ok=True)

    def download_video(self, video: Video, quality: str = "large") -> bool:
        """下载单个视频和保存元数据

        Args:
            video: 视频
            quality: 视频质量

        Returns:
            bool: 是否下载成功
        """
        video_id = str(video.id)
        video_file = video.get_video_by_quality(quality)
        if not video_file:
            logger.error(f"视频 {video_id} 没有 {quality} 质量的文件")
            return False

        video_path = os.path.join(self.save_dir, "videos", f"{video_id}.mp4")
        metadata_path = os.path.join(
            self.save_dir, "videos_metadata", f"{video_id}.json"
        )

        try:
            logger.info(f"开始下载视频: {video_id}")
            response = requests.get(video_file.url)
            response.raise_for_status()

            with open(video_path, "wb") as f:
                f.write(response.content)

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(video.model_dump(), f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"下载视频 {video_id} 失败: {str(e)}")
            return False
