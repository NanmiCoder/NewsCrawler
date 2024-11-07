# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-08
# description: 使用playwright获取User-Agent和Cookie
import logging
import os
import time
from typing import Dict
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from .tools import AuthGenHeaders, convert_cookies, get_random_ua

logger = logging.getLogger("Playwright Driver")


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
        PlaywrightGenHeaders: User-Agent和Cookie
    """
    init_logger()

    host = get_url_host(target_url)
    logger.info(f"Auto Get User-Agent And Cookie, site host: {host}")
    if host in CACHE_UA_AND_COOKIE:
        if CACHE_UA_AND_COOKIE[host].last_update_ts + DEFAULT_CACHE_SECONDS > time.time():
            logger.info(f"Get User-Agent And Cookie From Cache, host: {host}")
            return CACHE_UA_AND_COOKIE[host]

    random_ua = get_random_ua()
    result = AuthGenHeaders()
    result.user_agent = random_ua
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        browser_context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=random_ua
        )
        # 获取当前文件所在目录拼接stealth.min.js
        stealth_js_path = os.path.join(os.path.dirname(__file__), "stealth.min.js")
        browser_context.add_init_script(path=stealth_js_path)
        page = browser_context.new_page()

        logger.info(f"Go To Target URL: {target_url}, and extract User-Agent and Cookie")
        page.goto(target_url, wait_until="domcontentloaded")

        cookies_str, _ = convert_cookies(browser_context.cookies())
        result.cookie = cookies_str

        logger.info(f"Get User-Agent And Cookie Success, host: {host}, user-agent: {random_ua}, cookie: {cookies_str}")

        # 更新缓存
        result.last_update_ts = int(time.time())
        CACHE_UA_AND_COOKIE[host] = result

        return result
