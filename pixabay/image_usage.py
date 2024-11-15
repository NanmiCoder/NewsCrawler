# -*- coding: utf-8 -*-
import logging

from common.base import APIKeyPool
from common.proxy import SimpleProxyProvider
from common.schemas import MAX_RESOURCES_PER_KEYWORD, ProxyAuth, ProxyConfig
from images.downloader import ImageDownloader, PixabayAPI

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


def download_images_with_keywords(
    pixabay: PixabayAPI,
    downloader: ImageDownloader,
    keywords: list,
    max_images_per_keyword: int = MAX_RESOURCES_PER_KEYWORD,
):
    """批量下载多个关键词的图片。

    Args:
        pixabay: PixabayAPI实例。
        downloader: ImageDownloader实例。
        keywords: 关键词列表。
        max_images_per_keyword: 每个关键词最多下载的图片数量。
    """
    for keyword in keywords:
        logger.info(f"开始下载关键词 '{keyword}' 的图片...")
        try:
            downloaded_count = 0
            for image in pixabay.search_all_images(
                keyword, max_images=max_images_per_keyword
            ):
                if downloader.download_image(image):
                    downloaded_count += 1
                    logger.info(
                        f"成功下载图片: {image.id} ({downloaded_count}/{max_images_per_keyword})"
                    )

            logger.info(
                f"完成关键词 '{keyword}' 的下载, 共下载 {downloaded_count} 张图片"
            )

        except Exception as e:
            logger.error(f"下载 '{keyword}' 图片时发生错误: {str(e)}")
            raise e


if __name__ == "__main__":
    init_logger()
    keywords = ["cloud"]
    api_keys = ["47097682-8a286a407b814e98b6c7d3f56"]
    pixabay = PixabayAPI(
        api_key_pool=APIKeyPool(api_keys),
        proxy_provider=None,
        retry_times=3,
        retry_delay=1,
    )
    downloader = ImageDownloader(save_dir="downloads/pixabay")
    try:
        download_images_with_keywords(
            pixabay=pixabay,
            downloader=downloader,
            keywords=keywords,
            max_images_per_keyword=MAX_RESOURCES_PER_KEYWORD,
        )
        logger.info("所有下载任务完成!")
    except Exception as e:
        logger.error(f"下载过程中发生错误: {str(e)}")
