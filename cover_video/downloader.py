import json
import logging
import os
import random
import time
from typing import Dict, Generator, Optional

import requests
from schemas import Video, VideoSearchResponse
from user_agent import UA_LIST

logger = logging.getLogger("CoverVideoDownloader")


class CoverAPI:
    """处理Cover视频API的类"""

    BASE_URL = "https://coverr.co/api/videos"

    def __init__(
        self,
        retry_times: int = 3,
        retry_delay: int = 1,
    ):
        """初始化视频下载器

        Args:
            retry_times: 重试次数
            retry_delay: 重试延迟
        """
        self.retry_times = retry_times
        self.retry_delay = retry_delay

    @property
    def get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            Dict[str, str]: 请求头
        """

        return {"User-Agent": random.choice(UA_LIST)}

    def search_resources(
        self, query: str, page: int, page_size: int = 100
    ) -> VideoSearchResponse:
        """搜索视频

        Args:
            query: 关键词
            page: 页码
            page_size: 每页数量

        Returns:
            VideoSearchResponse: 视频搜索响应
        """
        params = {
            "query": query,
            "page": page,
            "page_size": page_size,
            "lang": "en",
            "camel_case": "true",
            "sort": "date",
            "urls": "true",
            "extends": ["keywords", "variant"],
            "userId": "guest",
        }

        logger.info(f"开始搜索视频关键词: {query}, 页码: {page}, 每页数量: {page_size}")

        for attempt in range(self.retry_times):
            try:
                response = requests.get(
                    self.BASE_URL, params=params, headers=self.get_headers
                )
                response.raise_for_status()
                search_response = VideoSearchResponse(**response.json())
                logger.info(f"搜索成功, 共找到 {search_response.total} 个视频")
                return search_response
            except Exception as e:
                if attempt == self.retry_times - 1:
                    logger.error(
                        f"搜索失败: {str(e)}， 关键词: {query}， 响应: {response.text}"
                    )
                    raise
                logger.warning(f"搜索失败，正在进行第{attempt + 1}次重试")
                time.sleep(self.retry_delay)

    def search_all_videos(
        self,
        query: str,
        max_videos: Optional[int] = None,
        page_size: int = 100,
    ) -> Generator[Video, None, None]:
        """搜索所有视频的生成器

        Args:
            query: 关键词
            max_videos: 最大视频数量
            page_size: 每页数量

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
                current_page_size = min(remaining, page_size)
            else:
                current_page_size = page_size

            response = self.search_resources(query, page, current_page_size)

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

    @property
    def get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            Dict[str, str]: 请求头
        """

        return {"User-Agent": random.choice(UA_LIST)}

    def download_video(self, video: Video, quality: str = "fhd") -> bool:
        """下载单个视频和保存元数据

        Args:
            video: 视频
            quality: 视频质量

        Returns:
            bool: 是否下载成功
        """
        video_id = str(video.id)

        if video.urls and video.urls.mp4_download:
            video_url = video.urls.mp4_download
        else:
            logger.error(f"视频 {video_id} 没有下载链接")
            return False

        video_path = os.path.join(self.save_dir, "videos", f"{video_id}.mp4")
        metadata_path = os.path.join(
            self.save_dir, "videos_metadata", f"{video_id}.json"
        )

        try:
            logger.info(f"开始下载视频: {video_id}")
            response = requests.get(video_url, headers=self.get_headers)
            response.raise_for_status()

            with open(video_path, "wb") as f:
                f.write(response.content)

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(video.model_dump(), f, ensure_ascii=False, indent=2)
            return True

        except Exception as e:
            logger.error(f"下载视频 {video_id} 失败: {str(e)}")
            return False
