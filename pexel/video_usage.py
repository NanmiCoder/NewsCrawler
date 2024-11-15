# -*- coding: utf-8 -*-
import logging
from common.base import APIKeyPool
from common.proxy import SimpleProxyProvider
from common.schemas import MAX_RESOURCES_PER_KEYWORD
from videos.downloader import PexelsVideoAPI, VideoDownloader

logger = logging.getLogger("PexelsDownloader")


def init_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def download_videos_with_keywords(
    pexels: PexelsVideoAPI,
    downloader: VideoDownloader,
    keywords: list,
    max_videos_per_keyword: int = MAX_RESOURCES_PER_KEYWORD,
):
    """批量下载多个关键词的视频。

    Args:
        pexels: PexelsVideoAPI实例。
        downloader: VideoDownloader实例。
        keywords: 关键词列表。
        max_videos_per_keyword: 每个关键词最多下载的视频数量。
    """
    for keyword in keywords:
        logger.info(f"开始下载关键词 '{keyword}' 的视频...")
        try:
            downloaded_count = 0
            for video in pexels.search_all_videos(
                keyword, max_videos=max_videos_per_keyword
            ):
                if downloader.download_video(video):
                    downloaded_count += 1
                    logger.info(
                        f"成功下载视频: {video.id} ({downloaded_count}/{max_videos_per_keyword})"
                    )

            logger.info(
                f"完成关键词 '{keyword}' 的下载, 共下载 {downloaded_count} 个视频"
            )

        except Exception as e:
            logger.error(f"下载 '{keyword}' 视频时发生错误: {str(e)}")


if __name__ == "__main__":
    init_logger()
    keywords = ["cloud"]
    api_keys = ["iN21cr1BrTEQAtRhn9TRArfEGmBUgrqrUTecb5FltSO9xGVEAw52SGze"]
    pexels = PexelsVideoAPI(
        api_key_pool=APIKeyPool(api_keys),
        proxy_provider=None,
        retry_times=3,
        retry_delay=1,
    )
    downloader = VideoDownloader(save_dir="downloads/pexel")
    try:
        download_videos_with_keywords(
            pexels=pexels,
            downloader=downloader,
            keywords=keywords,
            max_videos_per_keyword=MAX_RESOURCES_PER_KEYWORD,
        )
        logger.info("所有下载任务完成!")
    except Exception as e:
        logger.error(f"下载过程中发生错误: {str(e)}")
