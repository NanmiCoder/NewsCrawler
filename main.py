# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-08
# description: 主函数调用两个新闻爬虫示例代码

from detik_news import DetikNewsCrawler
from detik_news import RequestHeaders as DetikRequestHeaders
from libs import drissionpage_driver, playwright_driver
from toutiao_news import RequestHeaders as ToutiaoRequestHeaders
from toutiao_news import ToutiaoNewsCrawler

# 是否需要自动获取headers(User-Agent和Cookie)
NEED_AUTO_GET_HEADERS = False


def get_toutiao_news_detail(new_url: str):
    """获取头条新闻详情

    Args:
        new_url (str): 新闻详情页URL

    Returns:
        _type_: _description_
    """
    if NEED_AUTO_GET_HEADERS:
        _headers = playwright_driver.get_headers(new_url)
        headers = ToutiaoRequestHeaders(
            user_agent=_headers.user_agent,
            cookie=_headers.cookie
        )
        toutiao_news = ToutiaoNewsCrawler(new_url, headers=headers)
    else:
        toutiao_news = ToutiaoNewsCrawler(new_url)
    return toutiao_news.run()


def get_detik_news_detail(new_url: str):
    """获取detik新闻详情

    Args:
        new_url (str): 新闻详情页URL
    """
    if NEED_AUTO_GET_HEADERS:
        headers = playwright_driver.get_headers(new_url)
        headers = DetikRequestHeaders(
            user_agent=headers.user_agent,
            cookie=headers.cookie
        )
        detik_news = DetikNewsCrawler(new_url, headers=headers)
    else:
        detik_news = DetikNewsCrawler(new_url)
    return detik_news.run()


if __name__ == "__main__":
    toutiao_url = "https://www.toutiao.com/article/7434425099895210546/?log_from=62fe902b9dcea_1730987379758"
    get_toutiao_news_detail(toutiao_url)

    detik_url = "https://news.detik.com/internasional/d-7626006/5-pernyataan-trump-di-pidato-kemenangan-pilpres-as"
    get_detik_news_detail(detik_url)
