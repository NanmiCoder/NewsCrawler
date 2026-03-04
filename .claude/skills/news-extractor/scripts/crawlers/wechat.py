# -*- coding: utf-8 -*-
"""
微信公众号文章爬虫
"""
from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import demjson3
from parsel import Selector
from pydantic import Field

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parents[1]))

from models import ContentItem, ContentType, NewsItem, NewsMetaInfo, RequestHeaders as BaseRequestHeaders
from crawlers.base import BaseNewsCrawler
from crawlers.fetchers import CurlCffiFetcher, FetchRequest


FIXED_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
FIXED_COOKIE = "RK=KfsE+4gSss;rewardsn=;ptcz=13cd54e3b6207f8e605c9a70630509394ef82a923e405fcf0c7c562de1b6e986;wxtokenkey=777"

logger = logging.getLogger(__name__)


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")
    cookie: str = Field(default=FIXED_COOKIE, alias="Cookie")


def _convert_js_obj_to_json(js_obj_str: str) -> str:
    try:
        json.loads(js_obj_str)
        return js_obj_str
    except json.JSONDecodeError:
        try:
            js_obj_str = js_obj_str.replace(" * 1", "")
            parsed_data = demjson3.decode(js_obj_str)
            return json.dumps(parsed_data, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to convert JS object to JSON: {str(e)}")
            return js_obj_str


def _js_decode(s: str) -> str:
    if not s:
        return s
    return (s.replace('\\x5c', '\\')
             .replace('\\x0d', '\r')
             .replace('\\x22', '"')
             .replace('\\x26', '&')
             .replace('\\x27', "'")
             .replace('\\x3c', '<')
             .replace('\\x3e', '>')
             .replace('\\x0a', '\n'))


def _parse_cgi_data_new(html: str) -> Optional[dict]:
    if "window.cgiDataNew" not in html:
        return None

    pattern = r'window\.cgiDataNew\s*=\s*({[\s\S]*?});[\s\n]*}\s*catch'
    match = re.search(pattern, html)
    if not match:
        return None

    try:
        js_obj_str = match.group(1)

        def replace_jsdecode(match_obj):
            encoded_str = match_obj.group(1)
            encoded_str = encoded_str.replace("\\'", "'").replace("\\\\", "\\")
            decoded = _js_decode(encoded_str)
            return json.dumps(decoded, ensure_ascii=False)

        js_obj_str = re.sub(
            r"JsDecode\('((?:[^'\\]|\\.)*)'\)",
            replace_jsdecode,
            js_obj_str
        )
        js_obj_str = re.sub(r"'([\d.]+)'\s*\*\s*1", r'\1', js_obj_str)
        parsed_data = demjson3.decode(js_obj_str)
        return parsed_data

    except Exception as e:
        logger.error(f"Failed to parse cgiDataNew: {str(e)}")
        return None


def _parse_ssr_data(html: str) -> Optional[dict]:
    cgi_data = _parse_cgi_data_new(html)
    if cgi_data:
        return cgi_data

    if "window.__QMTPL_SSR_DATA__" not in html:
        return None

    ssr_data_match = re.search(r"window\.__QMTPL_SSR_DATA__=(.+);</script>", html)
    if not ssr_data_match:
        return None

    try:
        ssr_data_str = _convert_js_obj_to_json(ssr_data_match.group(1).strip())
        return json.loads(ssr_data_str)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to parse SSR data: {str(e)}")
        return None


def _parse_ssr_image_list(html: str) -> List[ContentItem]:
    contents: List[ContentItem] = []
    regex_compile = re.compile(
        r"window\.picture_page_info_list = (\[[\s\S]*?\])\.slice\(0,\s*20\);", re.DOTALL
    )
    picture_list_match = regex_compile.search(html)
    if not picture_list_match:
        return []
    try:
        js_image_list_str = picture_list_match.group(1)
        cdn_urls = re.findall(r"cdn_url:\s*'([^']+)'", js_image_list_str)
        for url in cdn_urls:
            url = url.replace("\\x26amp;", "&")
            contents.append(ContentItem(type=ContentType.IMAGE, content=url))
        return contents
    except Exception as e:
        logger.error(f"Failed to parse SSR image list: {str(e)}")
        return []


class WechatContentParser:
    def __init__(self):
        self._contents: List[ContentItem] = []

    def parse_html_to_news_content(self, html_content: str) -> List[ContentItem]:
        self._contents = []
        selector = Selector(text=html_content)
        content_node = selector.xpath('//div[@id="js_content"]')

        if not content_node:
            return self.parse_ssr_content(html_content)

        for node in content_node.xpath("./*"):
            self._process_content_node(node)

        contents = [item for item in self._contents if item.content.strip()]
        return self._remove_duplicate_contents(contents)

    def parse(self, html_content: str) -> List[ContentItem]:
        return self.parse_html_to_news_content(html_content)

    def _remove_duplicate_contents(self, contents: List[ContentItem]) -> List[ContentItem]:
        unique_contents = []
        seen_contents = set()
        for item in contents:
            content_key = f"{item.type}:{item.content}"
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique_contents.append(item)
        return unique_contents

    @staticmethod
    def _process_media(node: Selector) -> Optional[ContentItem]:
        if node.root.tag == "img":
            img_url = node.attrib.get("src", "") or node.attrib.get("data-src", "")
            if img_url:
                return ContentItem(type=ContentType.IMAGE, content=img_url)
        elif node.root.tag in ["video", "iframe"]:
            video_url = node.attrib.get("src", "")
            if video_url:
                return ContentItem(type=ContentType.VIDEO, content=video_url)
        return None

    @staticmethod
    def _process_text_block(node: Selector) -> Optional[str]:
        if node.root.tag in ["script", "style"]:
            return None
        text = node.xpath("string(.)").get("").strip()
        if not text:
            return None
        return text

    def _process_list_item(self, node: Selector) -> Optional[str]:
        text = self._process_text_block(node)
        if not text:
            return None
        if node.xpath("./ancestor::ol"):
            position = len(node.xpath("./preceding-sibling::li")) + 1
            return f"{position}. {text}"
        else:
            return f"• {text}"

    def _process_content_node(self, node: Selector):
        if node.root.tag in ["section", "div", "article", "blockquote", "figure"]:
            if node.xpath("./text()").get("").strip():
                self._contents.append(
                    ContentItem(
                        type=ContentType.TEXT,
                        content=node.xpath("./text()").get("").strip(),
                    )
                )
            for child in node.xpath("./*"):
                self._process_content_node(child)
            return

        if node.root.tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        if node.root.tag in ["ul", "ol"]:
            list_items = []
            for li in node.xpath(".//li"):
                item_text = self._process_list_item(li)
                if item_text:
                    list_items.append(item_text)
            if len(list_items) > 0:
                for item in list_items:
                    self._contents.append(ContentItem(type=ContentType.TEXT, content=item))
            return

        if node.root.tag == "li":
            text = self._process_list_item(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        media_content = self._process_media(node)
        if media_content:
            self._contents.append(media_content)
            return

        if node.root.tag == "p":
            if node.xpath(".//img") or node.xpath(".//video") or node.xpath(".//iframe"):
                maybe_exist_nodes = node.xpath(".//img | .//video | .//iframe")
                for maybe_exist_node in maybe_exist_nodes:
                    media_content = self._process_media(maybe_exist_node)
                    if media_content:
                        self._contents.append(media_content)

            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        if node.root.tag in ["span", "strong"]:
            if node.xpath(".//img") or node.xpath(".//video") or node.xpath(".//iframe"):
                maybe_exist_nodes = node.xpath(".//img | .//video | .//iframe")
                for maybe_exist_node in maybe_exist_nodes:
                    media_content = self._process_media(maybe_exist_node)
                    if media_content:
                        self._contents.append(media_content)

            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

        if node.root.tag == "a":
            if node.xpath(".//img"):
                for img_node in node.xpath(".//img"):
                    media_content = self._process_media(img_node)
                    if media_content:
                        self._contents.append(media_content)

            text = self._process_text_block(node)
            if text:
                self._contents.append(ContentItem(type=ContentType.TEXT, content=text))
            return

    def parse_ssr_content(self, html_content: str) -> List[ContentItem]:
        contents = []
        ssr_data_dict = _parse_ssr_data(html_content)

        if ssr_data_dict:
            try:
                picture_list = ssr_data_dict.get("picture_page_info_list", [])
                if picture_list:
                    for pic_info in picture_list:
                        cdn_url = pic_info.get("cdn_url", "")
                        if cdn_url:
                            cdn_url = cdn_url.replace("&amp;", "&")
                            contents.append(ContentItem(type=ContentType.IMAGE, content=cdn_url))

                if not picture_list:
                    contents.extend(_parse_ssr_image_list(html_content))

                desc = ssr_data_dict.get("desc") or ssr_data_dict.get("content_noencode")
                title = ssr_data_dict.get("title")
                final_desc = desc or title
                if final_desc:
                    desc_list = final_desc.split("\n")
                    for desc_item in desc_list:
                        if not desc_item:
                            continue
                        contents.append(
                            ContentItem(type=ContentType.TEXT, content=desc_item.strip())
                        )
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Failed to parse SSR data: {str(e)}")

        return contents


class WeChatNewsCrawler(BaseNewsCrawler):
    headers_model = RequestHeaders
    fetch_strategy = CurlCffiFetcher

    def __init__(
        self,
        new_url: str,
        save_path: str = "data/",
        headers: Optional[RequestHeaders] = None,
        fetcher: Optional[CurlCffiFetcher] = None,
    ):
        super().__init__(new_url, save_path, headers=headers, fetcher=fetcher)
        self._content_parser = WechatContentParser()

    @property
    def get_base_url(self) -> str:
        return "https://mp.weixin.qq.com"

    def get_article_id(self) -> str:
        try:
            return self.new_url.split("/s/")[1].split("?")[0]
        except Exception as exc:
            raise ValueError("解析文章ID失败，请检查URL是否正确") from exc

    def build_fetch_request(self) -> FetchRequest:
        request = super().build_fetch_request()
        request.impersonate = "chrome"
        return request

    @staticmethod
    def _parse_publish_time(html_content: str) -> str:
        pattern = r"var createTime = '(\d{4}-\d{2}-\d{2} \d{2}:\d{2})';"
        match = re.search(pattern, html_content)
        return match.group(1) if match else ""

    def parse_html_to_news_meta(self, html_content: str) -> NewsMetaInfo:
        self.logger.info("Start to parse html to news meta, news_url: %s", self.new_url)

        ssr_data = _parse_ssr_data(html_content)
        if ssr_data:
            author_name = ssr_data.get("nick_name", "")
            publish_time = ssr_data.get("create_time", "")
            if not publish_time:
                ori_send_time = ssr_data.get("ori_send_time")
                if ori_send_time:
                    try:
                        dt = datetime.fromtimestamp(int(ori_send_time))
                        publish_time = dt.strftime("%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        publish_time = ""

            return NewsMetaInfo(
                publish_time=publish_time.strip(),
                author_name=author_name.strip(),
                author_url="",
            )

        sel = Selector(text=html_content)
        publish_time = self._parse_publish_time(html_content)
        wechat_name = sel.xpath("string(//span[@id='profileBt'])").get("").strip() or ""
        wechat_author_url = (
            sel.xpath(
                "string(//div[@id='meta_content']/span[@class='rich_media_meta rich_media_meta_text'])"
            )
            .get("")
            .strip()
            or ""
        )
        author_name = f"{wechat_name} - {wechat_author_url}".strip("- ")

        return NewsMetaInfo(
            publish_time=publish_time.strip(),
            author_name=author_name.strip(),
            author_url="",
        )

    def parse_content(self, html: str) -> NewsItem:
        ssr_data = _parse_ssr_data(html)
        if ssr_data:
            title = (ssr_data.get("title") or "").strip()
        else:
            selector = Selector(text=html)
            title = (
                selector.xpath('//h1[@id="activity-name"]/text()').get("") or ""
            ).strip()

        if not title:
            raise ValueError("Failed to get title")

        meta_info = self.parse_html_to_news_meta(html)
        contents = list[ContentItem](self._content_parser.parse(html))

        return self.compose_news_item(
            title=title,
            meta_info=meta_info,
            contents=contents,
        )

    def validate_item(self, news_item: NewsItem) -> None:
        super().validate_item(news_item)
        if not news_item.title:
            raise ValueError("Failed to get title")
