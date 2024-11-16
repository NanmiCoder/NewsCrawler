# -*- coding: utf-8 -*-
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

from common.base import APIKeyPool
from common.proxy import SimpleProxyProvider
from common.schemas import MAX_RESOURCES_PER_KEYWORD
from videos.downloader import PixabayVideoAPI, VideoDownloader

logger = logging.getLogger("PixabayDownloader")


def init_logger():
    """初始化日志配置"""
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def download_videos_with_keywords(
    pixabay: PixabayVideoAPI,
    downloader: VideoDownloader,
    keywords: list,
    max_videos_per_keyword: int = MAX_RESOURCES_PER_KEYWORD,
    max_workers: int = 5,
):
    """批量下载多个关键词的视频。

    Args:
        pixabay: PixabayVideoAPI实例。
        downloader: VideoDownloader实例。
        keywords: 关键词列表。
        max_videos_per_keyword: 每个关键词最多下载的视频数量。
        max_workers: 线程池中的最大线程数。
    """
    for keyword in keywords:
        logger.info(f"开始下载关键词 '{keyword}' 的视频, 当前线程池大小: {max_workers}")
        try:
            start_time = time.time()
            downloaded_count = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for video in pixabay.search_all_videos(
                    keyword, max_videos=max_videos_per_keyword
                ):
                    if downloaded_count >= max_videos_per_keyword:
                        break
                    future = executor.submit(downloader.download_video, video)
                    futures.append((future, video.id))
                    downloaded_count += 1

                successful_downloads = 0
                for future, video_id in futures:
                    try:
                        if future.result():
                            successful_downloads += 1
                            logger.info(
                                f"成功下载视频: {video_id} ({successful_downloads}/{len(futures)})"
                            )
                        else:
                            logger.warning(f"视频下载失败: {video_id}")
                    except Exception as e:
                        logger.error(f"下载视频 {video_id} 时发生错误: {str(e)}")

            logger.info(
                f"完成关键词 '{keyword}' 的下载, 共下载 {successful_downloads} 个视频，耗时 {time.time() - start_time:.2f} 秒"
            )

        except Exception as e:
            logger.error(f"下载 '{keyword}' 视频时发生错误: {str(e)}")


if __name__ == "__main__":
    init_logger()
    from cover_video.video_tag import video_tag_list
    # keywords = ["cloud"]
    keywords = video_tag_list
    api_keys = ["47097682-8a286a407b814e98b6c7d3f56"]
    pixabay = PixabayVideoAPI(
        api_key_pool=APIKeyPool(api_keys),
        proxy_provider=None,
        retry_times=3,
        retry_delay=1,
    )
    downloader = VideoDownloader(save_dir="downloads/pixabay")
    try:
        download_videos_with_keywords(
            pixabay=pixabay,
            downloader=downloader,
            keywords=keywords,
            max_videos_per_keyword=MAX_RESOURCES_PER_KEYWORD,
            max_workers=os.cpu_count() + 4,
        )
        logger.info("所有下载任务完成!")
    except Exception as e:
        logger.error(f"下载过程中发生错误: {str(e)}")
