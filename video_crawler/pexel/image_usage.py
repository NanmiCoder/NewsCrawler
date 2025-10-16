# -*- coding: utf-8 -*-
import sys
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

from common.base import APIKeyPool
from common.proxy import SimpleProxyProvider
from common.schemas import MAX_RESOURCES_PER_KEYWORD, ProxyAuth, ProxyConfig
from images.downloader import ImageDownloader, PexelsAPI

logger = logging.getLogger("PexelsDownloader")


def init_logger():
    """初始化日志配置"""
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def download_images_with_keywords(
    pexels: PexelsAPI,
    downloader: ImageDownloader,
    keywords: list,
    max_images_per_keyword: int = MAX_RESOURCES_PER_KEYWORD,
    max_workers: int = 5,
):
    """批量下载多个关键词的图片。

    Args:
        pexels: PexelsAPI实例。
        downloader: ImageDownloader实例。
        keywords: 关键词列表。
        max_images_per_keyword: 每个关键词最多下载的图片数量。
        max_workers: 线程池中的最大线程数。
    """
    for keyword in keywords:
        logger.info(f"开始下载关键词 '{keyword}' 的图片, 当前线程池大小: {max_workers}")
        try:
            start_time = time.time()
            downloaded_count = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for photo in pexels.search_all_photos(
                    keyword, max_photos=max_images_per_keyword
                ):
                    if downloaded_count >= max_images_per_keyword:
                        break
                    future = executor.submit(downloader.download_image, keyword, photo)
                    futures.append((future, photo.id))
                    downloaded_count += 1

                successful_downloads = 0
                for future, photo_id in futures:
                    try:
                        if future.result():
                            successful_downloads += 1
                            logger.info(
                                f"成功下载图片: {photo_id} ({successful_downloads}/{len(futures)})"
                            )
                        else:
                            logger.warning(f"图片下载失败: {photo_id}")
                    except Exception as e:
                        logger.error(f"下载图片 {photo_id} 时发生错误: {str(e)}")

            logger.info(
                f"完成关键词 '{keyword}' 的下载, 共下载 {successful_downloads} 张图片，耗时 {time.time() - start_time:.2f} 秒"
            )

        except Exception as e:
            logger.error(f"下载 '{keyword}' 图片时发生错误: {str(e)}")


if __name__ == "__main__":
    init_logger()
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from video_config.video_tag import video_tag_list

    keywords = video_tag_list
    api_keys = [
        "iN21cr1BrTEQAtRhn9TRArfEGmBUgrqrUTecb5FltSO9xGVEAw52SGze",
        "3WoGqOUU6CNLiPv7IoCVrEXFvnG7d1Khh8sGe11bg7BHWntBeCkG5hnz",
    ]
    pexels = PexelsAPI(
        api_key_pool=APIKeyPool(api_keys),
        proxy_provider=None,
        retry_times=3,
        retry_delay=1,
    )
    downloader = ImageDownloader(save_dir="downloads/pexel")
    try:
        download_images_with_keywords(
            pexels=pexels,
            downloader=downloader,
            keywords=keywords,
            max_images_per_keyword=MAX_RESOURCES_PER_KEYWORD,
            max_workers=os.cpu_count() + 4,
        )
        logger.info("所有下载任务完成!")
    except Exception as e:
        logger.error(f"下载过程中发生错误: {str(e)}")
