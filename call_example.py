# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-08
# description: 主函数调用两个新闻爬虫示例代码

# detik新闻爬虫
from news_crawler.detik_news import DetikNewsCrawler
from news_crawler.detik_news import RequestHeaders as DetikRequestHeaders
from libs import drissionpage_driver, playwright_driver
# 头条新闻爬虫
from news_crawler.toutiao_news import RequestHeaders as ToutiaoRequestHeaders
from news_crawler.toutiao_news import ToutiaoNewsCrawler
# 微信公众号新闻爬虫
from news_crawler.wechat_news import RequestHeaders as WeChatRequestHeaders
from news_crawler.wechat_news import WeChatNewsCrawler

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



def get_wechat_news_detail(new_url: str):
    """获取微信公众号新闻详情

    Args:
        new_url (str): 新闻详情页URL
    """
    if NEED_AUTO_GET_HEADERS:
        headers = playwright_driver.get_headers(new_url)
        headers = WeChatRequestHeaders(
            user_agent=headers.user_agent,
            cookie=headers.cookie
        )
        wechat_news = WeChatNewsCrawler(new_url, headers=headers)
    else:
        wechat_news = WeChatNewsCrawler(new_url)
    return wechat_news.run()


if __name__ == "__main__":
    # toutiao_url = "https://www.toutiao.com/article/7434425099895210546/?log_from=62fe902b9dcea_1730987379758"
    # get_toutiao_news_detail(toutiao_url)

    # detik_url = "https://news.detik.com/internasional/d-7626006/5-pernyataan-trump-di-pidato-kemenangan-pilpres-as"
    # get_detik_news_detail(detik_url)

    wechat_url = "https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw"
    get_wechat_news_detail(wechat_url)
