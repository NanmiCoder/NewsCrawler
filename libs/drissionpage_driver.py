# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-08
# description: 使用DrissionPage获取User-Agent和Cookie

import logging
import time
from typing import Dict
from urllib.parse import urlparse

from DrissionPage import ChromiumOptions, ChromiumPage

from .tools import AuthGenHeaders

logger = logging.getLogger("DrissionPage Driver")


def init_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


DEFAULT_CACHE_SECONDS = 600  # 10分钟
CACHE_UA_AND_COOKIE: Dict[str, AuthGenHeaders] = {}


def get_url_host(full_url: str) -> str:
    """获取URL的host

    Args:
        full_url (str): 完整URL

    Returns:
        str: 主机名
    """
    return urlparse(full_url).netloc


def get_headers(target_url: str) -> AuthGenHeaders:
    """自动获取User-Agent和Cookie

    Args:
        target_url (str): 目标URL

    Returns:
        AuthGenHeaders: User-Agent和Cookie
    """
    init_logger()

    host = get_url_host(target_url)
    logger.info(f"Auto Get User-Agent And Cookie, site host: {host}")

    # 检查缓存
    if host in CACHE_UA_AND_COOKIE:
        if CACHE_UA_AND_COOKIE[host].last_update_ts + DEFAULT_CACHE_SECONDS > time.time():
            logger.info(f"Get User-Agent And Cookie From Cache, host: {host}")
            return CACHE_UA_AND_COOKIE[host]

    result = AuthGenHeaders()

    # 创建页面对象
    co = ChromiumOptions().auto_port()
    tab = ChromiumPage(co)
    logger.info(f"Go To Target URL: {target_url}, and extract User-Agent and Cookie")
    tab.get(target_url)
    tab.wait.doc_loaded()

    result.user_agent = tab.user_agent
    for cookie in tab.cookies():
        result.cookie += f"{cookie['name']}={cookie['value']}; "
    logger.info(
        f"Get User-Agent And Cookie Success, host: {host}, user-agent: {result.user_agent}, cookie: {result.cookie}")

    # 更新缓存
    result.last_update_ts = int(time.time())
    CACHE_UA_AND_COOKIE[host] = result

    # 关闭标签页面
    tab.close()
    tab.quit()

    return result
