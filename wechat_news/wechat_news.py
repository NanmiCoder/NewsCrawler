# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-08
# description: 采集公众号文章
# https://mp.weixin.qq.com/s/ebMzDPu2zMT_mRgYgtL6eQ
# https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw

import json
import logging
import os
import pathlib
from enum import Enum
import re
from typing import List, Optional

import requests
from parsel import Selector
from pydantic import BaseModel, Field
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = '_qimei_fingerprint=01253b31e9ec4aed2e41ac0e979727ed;_qimei_uuid42=17b0c10360c100c8fcc7c7d843c9c65a405ac57763;o_cookie=524134442;RK=4clVFXZXao;_ga_8YVFNWD1KC=GS1.2.1730678197.1.0.1730678197.0.0.0;pgv_pvid=3981322644;rewardsn=;_ga=GA1.2.1404980183.1730678197;_qimei_h38=5c9a2cfae91848260c187a060300000d817710;_qimei_q36=;ptcz=e9eaa9a8966bdfd1ec504e7efb587377ef47aff780a78b2c0197b3eb9f86d8d1;qq_domain_video_guid_verify=7d82e0c91151b66b;wxtokenkey=777'

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


class WeChatNewsCrawler:
    def __init__(self, new_url: str, save_path: str = "data/", headers: RequestHeaders = RequestHeaders()):
        """初始化公众号文章详情爬虫

        Args:
            new_url (str): 公众号文章详情页url
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
        """获取公众号详情页基础url
            
        Returns:
            str: 公众号详情页基础url
        """
        return "https://mp.weixin.qq.com"

    @property
    def get_article_id(self) -> str:
        """获取公众号详情页文章id
            eg: https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw?may_be_params=test
                return: 3Sr6nYjE1RF05siTblD2mw
        Returns:
            str: 公众号详情页文章id
        """
        try:
            news_id = self.new_url.split("/s/")[1].split("?")[0]                        
            return news_id
        except Exception as e:
            raise Exception(f"解析文章ID失败，请检查URL是否正确")

    def get_save_json_path(self) -> str:
        """获取公众号文章详情页保存的json文件路径

        Returns:
            str: 公众号文章详情页保存的json文件路径
        """
        return os.path.join(self.save_path, f"{self.get_article_id}.json")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def fetch_content(self) -> str:
        """获取公众号文章详情页内容
           该方法会有重试机制，如果状态码不是200，则重试3次每次等待1秒
        Raises:
            Exception: 获取内容失败

        Returns:
            str: 公众号文章详情页内容
        """
        logger.info(f"Start to fetch content from {self.new_url}")
        # from curl_cffi import requests
        # response = requests.get(self.new_url, headers=self.headers, impersonate="chrome")
        response = requests.get(self.new_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch content: {response.status_code}")
        response.encoding = "utf-8"
        return response.text
    
    def _parse_publish_time(self, html_content: str) -> str:
        """解析公众号文章详情页发布时间

        Args:
            html_content (str): 公众号文章详情页内容

        Returns:
            str: 公众号文章详情页发布时间
        """
        js_re_pattern = r"var createTime = '(\d{4}-\d{2}-\d{2} \d{2}:\d{2})';"
        match = re.search(js_re_pattern, html_content)
        if match:
            return match.group(1)
        return ""
    
    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        """解析公众号文章详情页元信息

        Args:
            html_content (str): 公众号文章详情页内容

        Returns:
            NewsMetaInfo: 公众号文章元信息
        """
        logger.info(f"Start to parse html to news meta, news_url: {self.new_url}")
        
        sel = Selector(text=html_content)
        publish_time = self._parse_publish_time(html_content)
        wechat_name = sel.xpath("string(//span[@id='profileBt'])").get("").strip() or ""
        wechat_author_url = sel.xpath("string(//div[@id='meta_content']/span[@class='rich_media_meta rich_media_meta_text'])").get("").strip() or ""
        author_name = f"{wechat_name} - {wechat_author_url}"        

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url=""# 公众号文章详情页中没有作者链接
        )

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        """解析公众号文章详情页内容

        Args:
            html_content (str): 公众号文章内容

        Returns:
            List[ContentItem]: 公众号文章内容
        """
        contents = []
        selector = Selector(text=html_content)

        elements = selector.xpath('//div[@id="js_content"]/*')
        for element in elements:
            # todo 解析内容
            pass

        return contents

    def parse_content(self, html: str) -> NewsItem:
        """解析公众号文章内容

        Args:
            html (str): 公众号文章内容

        Returns:
            NewsItem: 公众号文章详情
        """
        result = NewsItem()
        selector = Selector(text=html)

        # 获取标题微信公众号这边因为内容创作者的富文本编辑可能是多样的
        # 用h1的方式可能正文内容中也会包含标题，所以这里用h1+ID的方式获取标题
        title = selector.xpath('//h1[@id="activity-name"]/text()').get('')
        if not title:
            raise Exception("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)

        result.title = title.strip()
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
        """保存公众号文章详情为json文件

        Args:
            news_item (NewsItem): 公众号文章详情
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
            logger.info(f"parse content from {self.new_url}, result: {news_item}, we will check if the content is empty.")
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
    article_url1 = "https://mp.weixin.qq.com/s/ebMzDPu2zMT_mRgYgtL6eQ"
    article_url2 = "https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw"
    for article_url in [article_url1, article_url2]:
        crawler = WeChatNewsCrawler(article_url, save_path="data/")
        crawler.run()
