# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-15
# description: Pexels API下载图片示例
import logging
from images.downloader import PexelsAPI, ImageDownloader, APIKeyPool
from images.proxy import SimpleProxyProvider
from images.schemas import ProxyConfig, ProxyAuth, MAX_IMAGES_PER_KEYWORD

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
    max_images_per_keyword: int = MAX_IMAGES_PER_KEYWORD,
):
    """批量下载多个关键词的图片。

    Args:
        pexels: PexelsAPI实例。
        downloader: ImageDownloader实例。
        keywords: 关键词列表。
        max_images_per_keyword: 每个关键词最多下载的图片数量,默认1000。
    """
    for keyword in keywords:
        logger.info(f"开始下载关键词 '{keyword}' 的图片...")
        try:
            downloaded_count = 0
            for photo in pexels.search_all_photos(
                keyword, max_photos=max_images_per_keyword
            ):
                if downloader.download_image(photo):
                    downloaded_count += 1
                    logger.info(
                        f"成功下载图片: {photo.id} ({downloaded_count}/{max_images_per_keyword})"
                    )

            logger.info(
                f"完成关键词 '{keyword}' 的下载, 共下载 {downloaded_count} 张图片"
            )

        except Exception as e:
            logger.error(f"下载 '{keyword}' 图片时发生错误: {str(e)}")


if __name__ == "__main__":
    # 配置代理
    # proxies = [
    #     ProxyConfig(
    #         host="proxy1.example.com",
    #         port=8080,
    #         auth=ProxyAuth(username="user1", password="pass1"),
    #     ),
    #     ProxyConfig(
    #         host="proxy2.example.com",
    #         port=8080,
    #         auth=ProxyAuth(username="user2", password="pass2"),
    #     ),
    # ]
    # proxy_provider = SimpleProxyProvider(proxies)
    init_logger()
    # 配置API密钥池
    api_keys = ["iN21cr1BrTEQAtRhn9TRArfEGmBUgrqrUTecb5FltSO9xGVEAw52SGze"]

    # 初始化API客户端(使用代理)
    pexels = PexelsAPI(
        api_key_pool=APIKeyPool(api_keys),
        proxy_provider=None,
        retry_times=3,
        retry_delay=1,
    )

    # 初始化下载器
    downloader = ImageDownloader(save_dir="downloads/pexel")

    # 定义要下载的关键词
    keywords = ["cloud"]

    # 开始下载
    try:
        download_images_with_keywords(
            pexels=pexels,
            downloader=downloader,
            keywords=keywords,
            max_images_per_keyword=MAX_IMAGES_PER_KEYWORD,  # 使用常量配置
        )
        logger.info("所有下载任务完成!")
    except Exception as e:
        logger.error(f"下载过程中发生错误: {str(e)}")
