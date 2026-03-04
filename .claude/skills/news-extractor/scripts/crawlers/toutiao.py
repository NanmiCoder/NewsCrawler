# -*- coding: utf-8 -*-
"""
今日头条新闻爬虫
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from parsel import Selector
from pydantic import Field

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parents[1]))

from models import ContentItem, ContentType, NewsItem, NewsMetaInfo, RequestHeaders as BaseRequestHeaders
from crawlers.base import BaseNewsCrawler


FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = '_S_IPAD=0;passport_auth_status_ss=284f6e476da6cdac9ed5ceabe1f2582b%2C;ssid_ucp_sso_v1=1.0.0-KGZkNzVlZDhkMDQ3MWFiYjk5ZDk3OTQ3ZjVlMjM3MTQwMDM2ZjYyMTIKHAiHjM-nnQMQvcaEuQYY9hcgDDCvi8LiBTgIQCYaAmhsIiA5ODcwNDYxYTVkY2Q3MjA2NjljYzY4ZTYzNjQzZmI3Ng;ttwid=1%7Cia--HTETz63DvnEC1KTq8T4unZc9z-8xSWLG2tGoT3U%7C1731006909%7C557cc3728e4e4af4f6f3e73204cc87513274a8cfd9afff287e33f9f477c704aa;sso_uid_tt_ss=928dce35007c9d519658774c6beef45e;csrftoken=f281acfa1c9f03f87632ef708982c9dc;local_city_cache=%E6%B7%B1%E5%9C%B3;toutiao_sso_user_ss=9870461a5dcd720669cc68e63643fb76;_ga=GA1.1.1766929141.1726812239;_ga_QEHZPBE5HH=GS1.1.1731005115.10.1.1731006909.0.0.0;_S_DPR=2;_S_WIN_WH=2316_1294;gfkadpd=24,6457;passport_csrf_token=bd28f23b87bcf4301429268682d56420;s_v_web_id=verify_m1abf6k9_gAtTZmw0_vlBj_42X9_9PKg_TFcilJq78KHB;tt_scid=pZTSdqwHuTu3FALst92kSb-UhAGpdIQ.8B8tQHtQ2Ziuy6eGbvI4UIC8k0BGzOk715fb;tt_webid=7344407742516610612;ttcid=e3d8cb0ce95f459991afa37a90490daf25'


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class ToutiaoNewsCrawler(BaseNewsCrawler):
    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
    ):
        super().__init__(new_url, save_path, headers=headers)

    @property
    def get_base_url(self) -> str:
        return self.new_url.split("/article/")[0]

    def get_article_id(self) -> str:
        try:
            news_id = self.new_url.split("/article/")[1].split("?")[0]
            if news_id.endswith("/"):
                news_id = news_id[:-1]
            return news_id
        except Exception as exc:
            raise ValueError("解析文章ID失败，请检查URL是否正确") from exc

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        self.logger.info("Start to parse html to news meta, news_url: %s", self.new_url)
        sel = Selector(text=html_content)

        publish_time = sel.xpath("//div[@class='article-meta']/span[1]/text()").get() or ""
        author_name = sel.xpath("//div[@class='article-meta']/span[@class='name']/a/text()").get() or ""
        author_url = sel.xpath("//div[@class='article-meta']/span[@class='name']/a/@href").get() or ""

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url=(self.get_base_url + author_url.strip()) if author_url else "",
        )

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        contents = []
        selector = Selector(text=html_content)

        elements = selector.xpath('//article/*')
        for element in elements:
            if element.root.tag == 'p':
                text = element.xpath('string()').get('').strip()
                if text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

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
        selector = Selector(text=html)
        title = selector.xpath("//h1/text()").get("") or ""
        if not title:
            raise ValueError("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)

        return self.compose_news_item(
            title=title.strip(),
            meta_info=meta_info,
            contents=contents,
        )
