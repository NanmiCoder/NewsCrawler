import json
import logging
import os
import random
import time
from typing import Dict, Generator, Optional

import requests
from parsel import Selector
from schemas import MixkitVideo, VideoSearchResponse
from user_agent import UA_LIST

logger = logging.getLogger("MixkitVideoDownloader")


class MixkitAPI:
    """处理Mixkit视频API的类"""

    BASE_URL = "https://mixkit.co/free-stock-video"

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
        """获取请求头"""
        return {"User-Agent": random.choice(UA_LIST)}

    def parse_html_to_response(self, html: str, page: int) -> VideoSearchResponse:
        """解析HTML为视频搜索响应

        Args:
            html: HTML内容
            page: 当前页码

        Returns:
            VideoSearchResponse: 视频搜索响应
        """
        selector = Selector(text=html)

        # xpath表达式
        video_items_xpath = '//div[contains(@class, "item-grid__items")]/div[contains(@class, "item-grid__item")]'
        title_xpath = (
            './/a[contains(@class, "item-grid-video-player__overlay-link")]/text()'
        )
        detail_url_xpath = (
            './/a[contains(@class, "item-grid-video-player__overlay-link")]/@href'
        )
        video_src_xpath = ".//video/@src"
        pagination_xpath = '//div[contains(@class, "pagination__wrapper")]/a'

        # 解析视频列表
        videos = []
        video_items = selector.xpath(video_items_xpath)

        for item in video_items:
            video_src = item.xpath(video_src_xpath).get("")
            if not video_src:
                continue

            # 从视频源地址中提取ID和构建下载URL 例如: https://assets.mixkit.co/videos/50881/50881-360.mp4
            video_id = video_src.split("/")[-2]
            base_url = video_src.rsplit("-", 1)[0]
            title = item.xpath(title_xpath).get("")
            title = title.strip()
            detail_url = item.xpath(detail_url_xpath).get("")
            detail_url = f"https://mixkit.co{detail_url}" if detail_url else ""

            # 构建视频对象
            video = MixkitVideo(
                id=video_id,
                title=title,
                video_detail_url=detail_url,
                download_360_video_url=f"{base_url}-360.mp4",
                download_1080_video_url=f"{base_url}-1080.mp4",
            )
            videos.append(video)

        # 解析总页数
        total_pages = 10  # 默认10页
        paginations = selector.xpath(pagination_xpath)
        if len(paginations) > 0:
            try:
                last_pagination = paginations[-2]
                max_page = last_pagination.xpath("./text()").get("")
                if max_page:
                    total_pages = int(max_page.strip())
            except ValueError:
                logger.warning("无法解析总页数，使用默认值1")

        return VideoSearchResponse(page=page, total_pages=total_pages, hits=videos)

    def search_resources(self, query: str, page: int) -> VideoSearchResponse:
        """搜索视频

        Args:
            query: 关键词
            page: 页码

        Returns:
            VideoSearchResponse: 视频搜索响应
        """
        url = f"{self.BASE_URL}/{query}"
        if page > 1:
            url = f"{url}/?page={page}"

        logger.info(f"开始搜索视频关键词: {query}, 页码: {page}")

        for attempt in range(self.retry_times):
            try:
                response = requests.get(url, headers=self.get_headers)
                response.raise_for_status()
                search_response = self.parse_html_to_response(response.text, page)
                logger.info(
                    f"搜索成功, 当前页: {page}, 总页数: {search_response.total_pages}, "
                    f"当前页视频数: {len(search_response.hits)}"
                )
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
    ) -> Generator[MixkitVideo, None, None]:
        """搜索所有视频的生成器

        Args:
            query: 关键词
            max_videos: 最大视频数量

        Returns:
            Generator[MixkitVideo, None, None]: 视频生成器
        """
        page = 1
        total_yielded = 0

        while True:
            response = self.search_resources(query, page)
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
        return {"User-Agent": random.choice(UA_LIST)}

    def download_video(
        self, keyword: str, video: MixkitVideo, quality: str = "1080"
    ) -> bool:
        """下载单个视频和保存元数据

        Args:
            keyword: 关键词
            video: 视频
            quality: 视频质量 (360/1080)

        Returns:
            bool: 是否下载成功
        """
        video_id = video.id
        video_url = (
            video.download_1080_video_url
            if quality == "1080"
            else video.download_360_video_url
        )

        if not video_url:
            logger.error(f"视频 {video_id} 没有下载链接")
            return False

        video_path = os.path.join(self.save_dir, "videos", keyword, f"{video_id}.mp4")
        metadata_path = os.path.join(
            self.save_dir, "videos_metadata", keyword, f"{video_id}.json"
        )

        # for video keyword
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

        try:
            logger.info(f"开始下载视频: {video_id}，关键词: {keyword}")
            response = requests.get(video_url, headers=self.get_headers)
            response.raise_for_status()

            with open(video_path, "wb") as f:
                f.write(response.content)

            with open(metadata_path, "w", encoding="utf-8") as f:
                meta_data = video.model_dump()
                meta_data["search_source_keyword"] = keyword
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
            return True

        except Exception as e:
            logger.error(f"下载视频 {video_id} 失败: {str(e)}")
            return False
