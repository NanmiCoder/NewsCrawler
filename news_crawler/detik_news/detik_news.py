# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-07
# description: 采集detik新闻详情 

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

FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = '_clck=wl1fhf%7C2%7Cfqo%7C0%7C1772;__dtmids=7626006,241106115,7627223,7627023,7626997,7627812,241107049;_cc_id=5636ff14d721246adc33085ab05a2edf;__dtmb=146380193.10.10.1730995588;_ga_CY42M5S751=GS1.1.1730995097.2.1.1730995591.27.0.0;_ga_M7E3P87KRC=GS1.1.1730995459.2.1.1730995760.60.0.822827285;panoramaId_expiry=1731078198472;_fbp=fb.1.1730991797745.541515568189888759;_ga_FVWZ0RM4DH=GS1.1.1730995586.2.0.1730995586.60.0.0;_clsk=e2qesp%7C1730996418751%7C8%7C0%7Cz.clarity.ms%2Fcollect;___iat_ses=55EDC87DA0921652;___iat_vis=55EDC87DA0921652.e487f0ce2a88a7b4c505c03da1083879.1730995589444.4363edda93b800fd263bb42aabcc0d7c.AOUROUERIM.11111111.1-0.0;__dtma=146380193.1117904802.1730991797.1730991797.1730995096.2;__dtmc=146380193;_au_1d=AU1D-0100-001730991799-IQNVRNEM-EKVD;_ga=GA1.2.1036737509.1730991797;_gcl_au=1.1.1448781730.1730991797;_gid=GA1.2.2145302462.1730991798;dtklucx=gen_d133f0e4-07cf-48ff-56a2-c85155cecdad;panoramaId=a2ec58106a77f4f9e4efc37fd3b1a9fb927adfb9a149e6304a7510d07254e814;panoramaIdType=panoDevice'

logger = logging.getLogger("DetikNewsCrawler")


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


class DetikNewsCrawler:
    def __init__(self, new_url: str, save_path: str = "data/", headers: RequestHeaders = RequestHeaders()):
        """初始化detik新闻详情爬虫

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
        return "https://news.detik.com"

    @property
    def get_article_id(self) -> str:
        """获取新闻详情页文章id
            eg: https://news.detik.com/internasional/d-7626006/5-pernyataan-trump-di-pidato-kemenangan-pilpres-as
                return: d-76260067404384826024935990
        Returns:
            str: 新闻详情页文章id
        """
        try:
            route_path = self.new_url.replace(self.get_base_url, "")
            news_id = route_path.split("/")[2].split("?")[0]
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
        response = requests.get(self.new_url, headers=self.headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch content: {response.status_code}")
            raise Exception(f"Failed to fetch content: {response.status_code}")
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

        publish_time = sel.xpath("//article[@class='detail']//div[@class='detail__date']/text()").get() or ""
        author_name = sel.xpath("string(//article[@class='detail']//div[@class='detail__author'])").get() or ""
        author_url = ""  # detik新闻详情页没有作者链接

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url=author_url,
        )

    def parse_html_to_news_media(self, html_content: str) -> List[ContentItem]:
        """解析封面媒体信息，detik中标题下面的第一个栏目通常是图片或者视频，解析它

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            List[ContentItem]: 新闻媒体信息
        """
        res = []
        selector = Selector(text=html_content)
        poster_img = selector.xpath("//div[@class='detail__media']/figure[@class='detail__media-image']/img/@src").get()
        poster_video = selector.xpath("//div[@class='detail__media']/iframe/@src").get()
        poster_desc = selector.xpath(
            "string(//div[@class='detail__media']//figcaption[@class='detail__media-caption'])").get() or ""
        if poster_img:
            res.append(ContentItem(type=ContentType.IMAGE, content=poster_img, desc=poster_desc or poster_img))
        if poster_video:
            res.append(ContentItem(type=ContentType.VIDEO, content=poster_video, desc=poster_desc or poster_video))
        return res

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        """解析新闻详情页内容

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            List[ContentItem]: 新闻内容
        """
        contents = []

        # 先尝试解析封面媒体信息
        media_contents = self.parse_html_to_news_media(html_content)
        contents.extend(media_contents)

        # 再解析新闻正文
        selector = Selector(text=html_content)
        elements = selector.xpath('//div[@class="detail__body-text itp_bodycontent"]/*')
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

            if element.root.tag in ['table', 'strong']:
                other_tag_content = element.xpath('string()').get('').strip()
                if other_tag_content:
                    contents.append(
                        ContentItem(type=ContentType.TEXT, content=other_tag_content, desc=other_tag_content))

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
        title = selector.xpath('//h1/text()').get('').strip()
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
                logger.error(f"Failed to get content: {news_item.title}, and we will retry get content")
                raise Exception("Failed to get content")
            self.save_as_json(news_item)
            logger.info(f"Success to get content from {self.new_url}")

        try:
            retry_fetch_content()
        except RetryError as e:
            logger.error(
                f"Failed to get content from {self.new_url}, error: {e}, retry times: {e.last_attempt.attempt_number}")


if __name__ == "__main__":
    article_url1 = "https://news.detik.com/internasional/d-7626006/5-pernyataan-trump-di-pidato-kemenangan-pilpres-as"
    article_url2 = "https://news.detik.com/internasional/d-7627812/4-poin-pernyataan-kamala-akui-kekalahan-dari-trump"
    for article_url in [article_url1, article_url2]:
        crawler = DetikNewsCrawler(article_url, save_path="data/")
        crawler.run()
