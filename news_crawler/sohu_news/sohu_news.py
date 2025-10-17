# -*- coding: utf-8 -*-
from __future__ import annotations

# author: relakkes@gmail.com
# date: 2025-10-17
# description: 采集搜狐新闻详情

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
from news_crawler.core.fetchers import CurlCffiFetcher, FetchRequest

## 搜狐的cookies不需要登录态，随便打开一个搜狐新闻提取cookies即可
FIXED_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
FIXED_COOKIE = ''


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


class SohuNewsCrawler(BaseNewsCrawler):
    fetch_strategy = CurlCffiFetcher

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
        fetcher: Optional[CurlCffiFetcher] = None,
    ):
        """初始化搜狐新闻详情爬虫

        Args:
            new_url (str): 新闻详情页url
            save_path (str, optional): 保存路径. Defaults to "data/".
            headers (RequestHeaders, optional): 请求头. Defaults to RequestHeaders().
        """
        super().__init__(new_url, save_path, headers=headers, fetcher=fetcher)

    @property
    def get_base_url(self) -> str:
        """获取新闻详情页基础url

        Returns:
            str: 新闻详情页基础url
        """
        return "https://www.sohu.com"

    def get_article_id(self) -> str:
        """获取新闻详情页文章id
            eg: https://www.sohu.com/a/945014338_160447
                return: 945014338
        Returns:
            str: 新闻详情页文章id
        """
        try:
            # Extract ID from URL pattern: /a/[ID]_[source_id]
            path_part = self.new_url.split("/a/")[1]
            news_id = path_part.split("_")[0].split("?")[0]
            return news_id
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"解析文章ID失败，请检查URL是否正确: {exc}") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.impersonate = "chrome"
        return request

    def _is_valid_image_url(self, url: str) -> bool:
        """Check if the image URL is valid (not encrypted or base64)

        Args:
            url (str): Image URL to validate

        Returns:
            bool: True if valid URL, False otherwise
        """
        if not url:
            return False
        # Filter out encrypted/base64 strings (搜狐的加密图片URL)
        # Valid URLs should start with http://, https://, or //
        if url.startswith(('http://', 'https://', '//')):
            # Additional check: should contain a domain or path
            return '.' in url or '/' in url
        return False

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

        # Extract publish time from .article-info .time or #news-time
        publish_time = sel.xpath('//span[@id="news-time"]/text()').get() or \
                      sel.xpath('//span[@class="time"]/text()').get() or ""

        # Extract author from meta tag or h4 a
        author_name = sel.xpath('//meta[@name="mediaid"]/@content').get() or \
                     sel.xpath('//h4/a/text()').get() or ""
        author_url = sel.xpath('//h4/a/@href').get() or ""

        # Clean author_url if it starts with //
        if author_url.startswith('//'):
            author_url = 'https:' + author_url

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url=author_url,
        )

    def _extract_images_from_json(self, html_content: str) -> List[str]:
        """从HTML中的JavaScript JSON数据提取图片URL

        搜狐新闻将图片URL存储在imgsList变量中

        Args:
            html_content (str): HTML内容

        Returns:
            List[str]: 图片URL列表
        """
        import re
        import json

        # 查找 imgsList: [...] 数据
        pattern = r'imgsList:\s*(\[[\s\S]*?\])\s*,'
        match = re.search(pattern, html_content)

        if match:
            try:
                imgs_json = match.group(1)
                # Remove trailing commas before closing braces/brackets (invalid JSON)
                imgs_json = re.sub(r',(\s*[}\]])', r'\1', imgs_json)
                imgs_list = json.loads(imgs_json)
                return [img.get('url', '') for img in imgs_list if isinstance(img, dict) and img.get('url')]
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse imgsList JSON: {e}")

        return []

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        """解析新闻详情页内容

        Args:
            html_content (str): 新闻详情页内容

        Returns:
            List[ContentItem]: 新闻内容
        """
        contents = []
        selector = Selector(text=html_content)

        # 从JavaScript JSON数据中提取真实图片URL
        image_urls = self._extract_images_from_json(html_content)
        image_index = 0

        # Sohu news content is in article#mp-editor
        elements = selector.xpath('//article[@id="mp-editor"]/*')
        for element in elements:
            # Handle paragraph text
            if element.root.tag == 'p':
                # First check if this paragraph contains an image
                has_img = element.xpath('.//img').get() is not None

                if has_img and image_index < len(image_urls):
                    # Use the real image URL from JavaScript data
                    img_src = image_urls[image_index]
                    image_index += 1

                    # Normalize image URL
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    contents.append(ContentItem(type=ContentType.IMAGE, content=img_src, desc=img_src))

                # Get text content (excluding image-only paragraphs)
                text = element.xpath('string()').get('').strip()
                if text and not has_img:  # Only add text if no image in this paragraph
                    contents.append(ContentItem(type=ContentType.TEXT, content=text, desc=text))

            # Handle standalone images
            elif element.root.tag == 'img':
                if image_index < len(image_urls):
                    img_url = image_urls[image_index]
                    image_index += 1

                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    contents.append(ContentItem(type=ContentType.IMAGE, content=img_url, desc=img_url))

            # Handle videos
            elif element.root.tag == 'video':
                video_url = element.xpath('./@src').get() or \
                           element.xpath('.//source/@src').get()
                if video_url:
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    contents.append(ContentItem(type=ContentType.VIDEO, content=video_url, desc=video_url))

        return contents

    def parse_content(self, html: str) -> NewsItem:
        """解析新闻详情页内容

        Args:
            html (str): 新闻详情页内容

        Returns:
            NewsItem: 新闻详情
        """
        selector = Selector(text=html)

        # Get title from h1 tag
        title = selector.xpath('//h1/text()').get("")
        if not title:
            raise ValueError("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = self.parse_html_to_news_content(html)

        return self.compose_news_item(
            title=title.strip(),
            meta_info=meta_info,
            contents=contents,
        )


if __name__ == "__main__":
    # Test URL
    article_url = "https://www.sohu.com/a/945014338_160447"
    crawler = SohuNewsCrawler(article_url, save_path="data/")
    result = crawler.run()
    print(f"Successfully crawled: {result.title}")
    print(f"Author: {result.meta_info.author_name}")
    print(f"Publish time: {result.meta_info.publish_time}")
    print(f"Text paragraphs: {len(result.texts)}")
    print(f"Images: {len(result.images)}")
