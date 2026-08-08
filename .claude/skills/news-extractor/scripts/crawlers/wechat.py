# -*- coding: utf-8 -*-
"""
微信公众号文章爬虫
"""
from __future__ import annotations

import hashlib
import html
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

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


def _strip_multiply_by_one(match_obj: "re.Match") -> str:
    """还原 JS 里 '字面量' * 1 的写法

    微信页面用 'xxx' * 1 做字符串转数字，左操作数不一定是数字，
    例如 link_type: 'LINK_TYPE_MP_APPMSG' * 1。只匹配数字会让 * 残留，
    导致 demjson3 解析整个对象失败。
    """
    raw = match_obj.group(1)
    if re.fullmatch(r"-?\d+(?:\.\d+)?", raw):
        # 纯数字仍还原成数字字面量，保持字段类型与旧版本一致
        return raw
    # 非数字在 JS 里结果是 NaN，保留原始字符串比丢字段更有用
    return f"'{raw}'"


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
        js_obj_str = re.sub(
            r"'((?:[^'\\]|\\.)*)'\s*\*\s*1(?!\d)",
            _strip_multiply_by_one,
            js_obj_str,
        )
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

        # Also extract images from SSR data (image articles have most images there)
        ssr_images = self._extract_ssr_images(html_content)
        existing_image_urls = {item.content for item in contents if item.type == ContentType.IMAGE}
        for ssr_img in ssr_images:
            if ssr_img.content not in existing_image_urls:
                contents.insert(0, ssr_img)
                existing_image_urls.add(ssr_img.content)

        return self._remove_duplicate_contents(contents)

    def _extract_ssr_images(self, html_content: str) -> List[ContentItem]:
        """Extract images from SSR/embedded data (covers image articles type 8).

        WeChat image articles store most images inside inline <script> data blocks
        rather than in the visible DOM. This method uses three fallback strategies
        to find them all.
        """
        images: List[ContentItem] = []

        # Method 1: window.picture_page_info_list (primary source for image articles)
        ssr_images = _parse_ssr_image_list(html_content)
        images.extend(ssr_images)

        # Method 2: __QMTPL_SSR_DATA__ / cgiDataNew (fallback)
        ssr_data = _parse_ssr_data(html_content)
        if ssr_data:
            picture_list = ssr_data.get("picture_page_info_list", [])
            for pic_info in picture_list:
                pic_cdn = pic_info.get("cdn_url", "")
                if pic_cdn:
                    pic_cdn = pic_cdn.replace("&amp;", "&")
                    images.append(ContentItem(type=ContentType.IMAGE, content=pic_cdn))

        # Method 3: Global cdn_url scan across all <script> blocks.
        # Some WeChat article types embed image lists as plain JS objects
        # scattered across multiple inline scripts (e.g. type-8 image articles).
        # We scan for cdn_url: '...' patterns and pick up only WeChat CDN JPEGs.
        cdn_urls_seen = {item.content for item in images}
        for m in re.finditer(r"""cdn_url\s*:\s*['"]([^'"]+)['"]""", html_content):
            url = m.group(1)
            if "mmbiz.qpic.cn" in url and ("wx_fmt=jpeg" in url or "wx_fmt=png" in url):
                if url not in cdn_urls_seen:
                    images.append(ContentItem(type=ContentType.IMAGE, content=url))
                    cdn_urls_seen.add(url)

        return images

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
        # Unescape HTML entities (&lt;→<, &gt;→>, &quot;→", &amp;→&)
        text = html.unescape(text)
        # Strip residual HTML tags (e.g. topic links) but keep inner text
        text = re.sub(r'<[^>]+>', '', text)
        text = text.strip()
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
        """Parse SSR/inline data when js_content div is not present.

        WeChat articles rendered as image cards (type 8) or loaded dynamically
        don't have a populated js_content div in the initial HTML. Instead the
        data lives in inline <script> blocks and meta tags.
        """
        contents: List[ContentItem] = []

        # --- Images: try multiple sources ---
        ssr_data_dict = _parse_ssr_data(html_content)

        # Method 1: picture_page_info_list from SSR data
        if ssr_data_dict:
            picture_list = ssr_data_dict.get("picture_page_info_list", [])
            for pic_info in picture_list:
                pic_url = pic_info.get("cdn_url", "")
                if pic_url:
                    pic_url = pic_url.replace("&amp;", "&")
                    contents.append(ContentItem(type=ContentType.IMAGE, content=pic_url))

        # Method 2: window.picture_page_info_list (regex-based, works for type-8 articles)
        ssr_image_list = _parse_ssr_image_list(html_content)
        existing_urls = {item.content for item in contents if item.type == ContentType.IMAGE}
        for img in ssr_image_list:
            if img.content not in existing_urls:
                contents.append(img)
                existing_urls.add(img.content)

        # Method 3: Global cdn_url scan across all <script> blocks
        for m in re.finditer(r"""cdn_url\s*:\s*['"]([^'"]+)['"]""", html_content):
            url = m.group(1)
            if "mmbiz.qpic.cn" in url and ("wx_fmt=jpeg" in url or "wx_fmt=png" in url):
                if url not in existing_urls:
                    contents.append(ContentItem(type=ContentType.IMAGE, content=url))
                    existing_urls.add(url)

        # --- Text: try multiple sources ---
        text_source = ""

        # Source 1: SSR data desc / content_noencode
        if ssr_data_dict:
            desc = ssr_data_dict.get("desc") or ssr_data_dict.get("content_noencode")
            if desc:
                text_source = desc

        # Source 2: Meta description (contains article body for image articles)
        if not text_source:
            meta_match = re.search(
                r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
                html_content,
            )
            if meta_match:
                text_source = meta_match.group(1)

        # Source 3: og:title (bare minimum)
        if not text_source:
            og_match = re.search(
                r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
                html_content,
            )
            if og_match:
                text_source = og_match.group(1)

        if text_source:
            # Decode JS-style escape sequences and HTML entities
            text_source = _js_decode(text_source)
            text_source = html.unescape(text_source)
            # Strip topic-link HTML tags, keep hashtag text
            text_source = re.sub(r'<[^>]+>', '', text_source)
            # Split into paragraphs
            for line in text_source.split('\n'):
                line = line.strip()
                if line:
                    contents.append(ContentItem(type=ContentType.TEXT, content=line))

        return self._remove_duplicate_contents(contents)


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
        """解析文章ID，兼容微信的多种 URL 形态

        - https://mp.weixin.qq.com/s/{id}                          短链
        - https://mp.weixin.qq.com/s?__biz=xx&mid=xx&idx=1&sn={sn} 旧版永久链接
        - https://mp.weixin.qq.com/s?src=11&...&signature=xx       搜索结果跳转链接
        """
        parsed = urlparse(self.new_url)

        if "/s/" in parsed.path:
            path_id = parsed.path.split("/s/", 1)[1].strip("/")
            if path_id:
                return path_id

        query = parse_qs(parsed.query)
        # sn 是旧版链接里的文章唯一标识
        sn = (query.get("sn") or [""])[0].strip()
        if sn:
            return sn

        # 搜索跳转链接没有 sn，用签名摘要保证文件名唯一且可复现
        signature = (query.get("signature") or [""])[0].strip()
        if signature:
            return hashlib.md5(signature.encode("utf-8")).hexdigest()[:16]

        raise ValueError("解析文章ID失败，请检查URL是否正确")

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

    @staticmethod
    def _parse_title_from_dom(html_content: str) -> str:
        """从 HTML 里兜底取标题

        h1#activity-name 内常有换行和内嵌标签，取 text() 只会拿到第一个空白文本节点，
        必须用 string() 才能拿到完整标题。
        """
        selector = Selector(text=html_content)
        title = (
            selector.xpath('string(//h1[@id="activity-name"])').get("") or ""
        ).strip()
        if title:
            return title

        title = (
            selector.xpath('//meta[@property="og:title"]/@content').get("") or ""
        ).strip()
        if title:
            return title

        match = re.search(r"var\s+msg_title\s*=\s*'((?:[^'\\]|\\.)*)'", html_content)
        return _js_decode(match.group(1)).strip() if match else ""

    def parse_content(self, html: str) -> NewsItem:
        ssr_data = _parse_ssr_data(html)
        title = (ssr_data.get("title") or "").strip() if ssr_data else ""
        if not title:
            title = self._parse_title_from_dom(html)

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
