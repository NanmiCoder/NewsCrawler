# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-07
# description: 采集头条新闻详情 

import json
import logging
import os
import pathlib
from enum import Enum
from typing import List, Optional

import requests
from parsel import Selector
from pydantic import BaseModel, Field
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

## 头条的cookies不需要登录态，随便打开一个头条新闻提取cookies即可
FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = '_S_IPAD=0;passport_auth_status_ss=284f6e476da6cdac9ed5ceabe1f2582b%2C;ssid_ucp_sso_v1=1.0.0-KGZkNzVlZDhkMDQ3MWFiYjk5ZDk3OTQ3ZjVlMjM3MTQwMDM2ZjYyMTIKHAiHjM-nnQMQvcaEuQYY9hcgDDCvi8LiBTgIQCYaAmhsIiA5ODcwNDYxYTVkY2Q3MjA2NjljYzY4ZTYzNjQzZmI3Ng;ttwid=1%7Cia--HTETz63DvnEC1KTq8T4unZc9z-8xSWLG2tGoT3U%7C1731006909%7C557cc3728e4e4af4f6f3e73204cc87513274a8cfd9afff287e33f9f477c704aa;sso_uid_tt_ss=928dce35007c9d519658774c6beef45e;csrftoken=f281acfa1c9f03f87632ef708982c9dc;local_city_cache=%E6%B7%B1%E5%9C%B3;toutiao_sso_user_ss=9870461a5dcd720669cc68e63643fb76;_ga=GA1.1.1766929141.1726812239;_ga_QEHZPBE5HH=GS1.1.1731005115.10.1.1731006909.0.0.0;_S_DPR=2;_S_WIN_WH=2316_1294;gfkadpd=24,6457;passport_csrf_token=bd28f23b87bcf4301429268682d56420;s_v_web_id=verify_m1abf6k9_gAtTZmw0_vlBj_42X9_9PKg_TFcilJq78KHB;tt_scid=pZTSdqwHuTu3FALst92kSb-UhAGpdIQ.8B8tQHtQ2Ziuy6eGbvI4UIC8k0BGzOk715fb;tt_webid=7344407742516610612;ttcid=e3d8cb0ce95f459991afa37a90490daf25'

logger = logging.getLogger("TouTiaoNewsCrawler")


def init_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class RequestHeaders(BaseModel):
    user_agent: str = Field(default=FIXED_USER_AGENT, title="User-Agent", alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, title="Cookie", alias="Cookie")


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ContentItem(BaseModel):
    type: ContentType = Field(default=ContentType.TEXT, title="内容类型")
    content: str = Field(default="", title="内容")
    desc: str = Field(default="", title="描述")


class NewsMetaInfo(BaseModel):
    author_name: str = Field(default="", title="作者")
    author_url: str = Field(default="", title="作者链接")
    publish_time: str = Field(default="", title="发布时间")


class NewsItem(BaseModel):
    title: str = Field(default="", title="新闻标题")
    news_url: str = Field(default="", title="新闻链接")
    news_id: str = Field(default="", title="新闻ID")
    meta_info: NewsMetaInfo = Field(default=NewsMetaInfo(), title="新闻元信息")
    contents: List[ContentItem] = Field(default=[], title="新闻内容")
    texts: List[str] = Field(default=[], title="新闻正文")
    images: List[str] = Field(default=[], title="新闻图片")
    videos: Optional[List[str]] = Field(default=[], title="新闻视频")


class ToutiaoNewsCrawler:
    def __init__(self, new_url: str, save_path: str = "data/", headers: RequestHeaders = RequestHeaders()):
        """初始化头条新闻详情爬虫

        Args:
            new_url (str): 新闻详情页url
            save_path (str, optional): 保存路径. Defaults to "".
            headers (RequestHeaders, optional): 请求头. Defaults to RequestHeaders().
        """
        init_logger()
        self.new_url = new_url
        self.save_path = save_path
        self.save_file_name = self.get_save_json_path()
        self.headers = headers.model_dump()

    @property
    def get_base_url(self) -> str:
        """获取新闻详情页基础url
            
        Returns:
            str: 新闻详情页基础url
        """
        return self.new_url.split("/article/")[0]

    @property
    def get_article_id(self) -> str:
        """获取新闻详情页文章id
            eg: https://www.toutiao.com/article/7404384826024935990/?log_from=6ca9c55804822_1729740822770
                return: 7404384826024935990
        Returns:
            str: 新闻详情页文章id
        """
        try:
            news_id = self.new_url.split("/article/")[1].split("?")[0]
            if news_id.endswith("/"):
                news_id = news_id[:-1]
            return news_id
        except Exception as e:
            raise Exception(f"解析文章ID失败，请检查URL是否正确")

    def get_save_json_path(self) -> str:
        """获取新闻详情页保存的json文件路径

        Returns:
            str: 新闻详情页保存的json文件路径
        """
        return os.path.join(self.save_path, f"{self.get_article_id}.json")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def fetch_content(self) -> str:
        """获取新闻详情页内容
           该方法会有重试机制，如果状态码不是200，则重试3次每次等待1秒
        Raises:
            Exception: 获取内容失败

        Returns:
            str: 新闻详情页内容
        """
        logger.info(f"Start to fetch content from {self.new_url}")
        # from curl_cffi import requests
        # response = requests.get(self.new_url, headers=self.headers, impersonate="chrome")
        response = requests.get(self.new_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch content: {response.status_code}")
        response.encoding = "utf-8"
        return response.text

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        """解析新闻详情页元信息

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            NewsMetaInfo: 新闻元信息
        """
        logger.info(f"Start to parse html to news meta, news_url: {self.new_url}")
        sel = Selector(text=html_content)

        publish_time = sel.xpath("//div[@class='article-meta']/span[1]/text()").get() or ""
        author_name = sel.xpath("//div[@class='article-meta']/span[@class='name']/a/text()").get() or ""
        author_url = sel.xpath("//div[@class='article-meta']/span[@class='name']/a/@href").get() or ""

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url=self.get_base_url + author_url.strip(),
        )

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        """解析新闻详情页内容

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            List[ContentItem]: 新闻内容
        """
        contents = []
        selector = Selector(text=html_content)

        elements = selector.xpath('//article/*')
        for element in elements:
            if element.root.tag == 'p':
                text = element.xpath('string()').get('').strip()
                if text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

            # img标签有可能被包括在div、p标签中所以要特殊处理一下                     
            if element.root.tag in ['img', 'div', 'p']:
                if element.root.tag == 'img':
                    img_url = element.xpath('./@src').get('')
                    if img_url:
                        contents.append(ContentItem(type=ContentType.IMAGE, content=img_url, desc=img_url))
                else:
                    img_urls = element.xpath(".//img/@src").getall()
                    for img_url in img_urls:
                        if img_url:
                            contents.append(ContentItem(type=ContentType.IMAGE, content=img_url, desc=img_url))

            if element.root.tag == 'video':
                video_url = element.xpath('./@src').get('')
                if video_url:
                    contents.append(ContentItem(type=ContentType.VIDEO, content=video_url, desc=video_url))

        return contents

    def parse_content(self, html: str) -> NewsItem:
        """解析新闻详情页内容

        Args:
            html (str): 新闻详情页内容

        Returns:
            NewsItem: 新闻详情
        """
        result = NewsItem()
        selector = Selector(text=html)

        # 获取标题
        title = selector.xpath('//h1/text()').get('')
        if not title:
            raise Exception("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)

        result.title = title
        result.news_url = self.new_url
        result.news_id = self.get_article_id
        result.meta_info = meta_info
        result.contents = contents

        # 提取文本、图片、视频放到单独的列表中，备用
        result.texts = [content.content for content in contents if content.type == ContentType.TEXT]
        result.images = [content.content for content in contents if content.type == ContentType.IMAGE]
        result.videos = [content.content for content in contents if content.type == ContentType.VIDEO]

        return result

    def save_as_json(self, news_item: NewsItem):
        """保存新闻详情为json文件

        Args:
            news_item (NewsItem): 新闻详情
        """
        pathlib.Path(self.save_path).mkdir(parents=True, exist_ok=True)
        with open(self.save_file_name, 'w', encoding='utf-8') as f:
            json.dump(news_item.model_dump(), f, ensure_ascii=False, indent=4)

    def run(self):
        """运行爬虫
        """

        @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
        def retry_fetch_content():
            html = self.fetch_content()
            news_item = self.parse_content(html)
            if len(news_item.texts) == 0 and len(news_item.contents) == 0:
                logger.error(f"Failed to get content: {news_item.title}, and we will retry get content ...")
                raise Exception("Failed to get content")
            self.save_as_json(news_item)
            logger.info(f"Success to get content from {self.new_url}")

        try:
            retry_fetch_content()
        except RetryError as e:
            logger.error(
                f"Failed to get content from {self.new_url}, error: {e}, retry times: {e.last_attempt.attempt_number}")
            raise e


if __name__ == "__main__":
    article_url1 = "https://www.toutiao.com/article/7434425099895210546/?log_from=62fe902b9dcea_1730987379758"
    article_url2 = "https://www.toutiao.com/article/7404384826024935990/?log_from=6ca9c55804822_1729740822770"
    for article_url in [article_url1, article_url2]:
        crawler = ToutiaoNewsCrawler(article_url, save_path="data/")
        crawler.run()
