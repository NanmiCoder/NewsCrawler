# -*- coding: utf-8 -*-
from __future__ import annotations

# author: relakkes@gmail.com
# date: 2024-11-07
# description: 采集detik新闻详情

from typing import List, Optional

from parsel import Selector
from pydantic import Field

from news_crawler.core import (
    BaseNewsCrawler,
    ContentItem,
    ContentType,
    NewsItem,
    NewsMetaInfo,
    RequestHeaders as BaseRequestHeaders,
)

FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = '_clck=wl1fhf%7C2%7Cfqo%7C0%7C1772;__dtmids=7626006,241106115,7627223,7627023,7626997,7627812,241107049;_cc_id=5636ff14d721246adc33085ab05a2edf;__dtmb=146380193.10.10.1730995588;_ga_CY42M5S751=GS1.1.1730995097.2.1.1730995591.27.0.0;_ga_M7E3P87KRC=GS1.1.1730995459.2.1.1730995760.60.0.822827285;panoramaId_expiry=1731078198472;_fbp=fb.1.1730991797745.541515568189888759;_ga_FVWZ0RM4DH=GS1.1.1730995586.2.0.1730995586.60.0.0;_clsk=e2qesp%7C1730996418751%7C8%7C0%7Cz.clarity.ms%2Fcollect;___iat_ses=55EDC87DA0921652;___iat_vis=55EDC87DA0921652.e487f0ce2a88a7b4c505c03da1083879.1730995589444.4363edda93b800fd263bb42aabcc0d7c.AOUROUERIM.11111111.1-0.0;__dtma=146380193.1117904802.1730991797.1730991797.1730995096.2;__dtmc=146380193;_au_1d=AU1D-0100-001730991799-IQNVRNEM-EKVD;_ga=GA1.2.1036737509.1730991797;_gcl_au=1.1.1448781730.1730991797;_gid=GA1.2.2145302462.1730991798;dtklucx=gen_d133f0e4-07cf-48ff-56a2-c85155cecdad;panoramaId=a2ec58106a77f4f9e4efc37fd3b1a9fb927adfb9a149e6304a7510d07254e814;panoramaIdType=panoDevice'


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class DetikNewsCrawler(BaseNewsCrawler):
    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
    ):
        """初始化detik新闻详情爬虫

        Args:
            new_url (str): 新闻详情页url
            save_path (str, optional): 保存路径. Defaults to "".
            headers (RequestHeaders, optional): 请求头. Defaults to RequestHeaders().
        """
        super().__init__(new_url, save_path, headers=headers)

    @property
    def get_base_url(self) -> str:
        """获取新闻详情页基础url
            
        Returns:
            str: 新闻详情页基础url
        """
        return "https://news.detik.com"

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
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ValueError("解析文章ID失败，请检查URL是否正确") from exc

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        """解析新闻详情页元信息

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            NewsMetaInfo: 新闻元信息
        """
        self.logger.info(
            "Start to parse html to news meta, news_url: %s", self.new_url
        )
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
        selector = Selector(text=html)
        title = selector.xpath("//h1/text()").get("").strip()
        if not title:
            raise ValueError("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)

        return self.compose_news_item(
            title=title,
            meta_info=meta_info,
            contents=contents,
        )


if __name__ == "__main__":
    article_url1 = "https://news.detik.com/internasional/d-7626006/5-pernyataan-trump-di-pidato-kemenangan-pilpres-as"
    article_url2 = "https://news.detik.com/internasional/d-7627812/4-poin-pernyataan-kamala-akui-kekalahan-dari-trump"
    for article_url in [article_url1, article_url2]:
        crawler = DetikNewsCrawler(article_url, save_path="data/")
        crawler.run()
