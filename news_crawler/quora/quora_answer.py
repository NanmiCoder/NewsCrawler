# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# description: Quora 回答爬虫

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from pydantic import Field

from news_crawler.core import (
    BaseNewsCrawler,
    ContentItem,
    ContentType,
    NewsItem,
    NewsMetaInfo,
    RequestHeaders as BaseRequestHeaders,
)


FIXED_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)


class RequestHeaders(BaseRequestHeaders):
    user_agent: str = Field(default=FIXED_USER_AGENT, alias="User-Agent")


def timestamp_to_date(timestamp: int) -> str:
    if not timestamp:
        return ""
    seconds = timestamp // 1_000_000
    from datetime import datetime

    return datetime.fromtimestamp(seconds).strftime("%Y-%m-%d %H:%M:%S")


class QuoraAnswerCrawler(BaseNewsCrawler):
    headers_model = RequestHeaders

    def __init__(
        self,
        answer_url: str,
        save_path: str = "data/",
        headers: RequestHeaders | None = None,
    ):
        super().__init__(answer_url, save_path, headers=headers)

    @property
    def answer_url(self) -> str:
        return self.new_url

    def get_article_id(self) -> str:
        try:
            sanitized = self.answer_url.split("?")[0]
            if "/answers/" in sanitized:
                return sanitized.split("/answers/")[-1]
            if "/answer/" in sanitized:
                return sanitized.split("/answer/")[-1]
            raise ValueError("Unsupported Quora answer url format")
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ValueError("解析答案ID失败") from exc

    def extract_answer_json(self, html_content: str) -> Optional[Dict[str, Any]]:
        pattern = r'push\(("{\\"data\\":{\\"answer\\":.*?}}")\);'
        matches = re.finditer(pattern, html_content, re.DOTALL)
        for match in matches:
            json_str = match.group(1)
            try:
                answer_data = json.loads(json_str)
                answer_data = json.loads(answer_data)
                if (
                    "data" in answer_data
                    and "answer" in answer_data["data"]
                    and "content" in answer_data["data"]["answer"]
                ):
                    return answer_data
            except json.JSONDecodeError:
                continue
        return None

    def extract_answer_meta(self, answer_data: Dict[str, Any]) -> NewsMetaInfo:
        author_name = ""
        author = answer_data.get("author", {})
        names = author.get("names", [])
        if names:
            given = names[0].get("givenName", "")
            family = names[0].get("familyName", "")
            author_name = (given + " " + family).strip()
        author_url = author.get("profileUrl") or ""
        publish_time = timestamp_to_date(answer_data.get("creationTime", 0))
        return NewsMetaInfo(
            author_name=author_name,
            author_url=author_url,
            publish_time=publish_time,
        )

    def extract_question_title(self, answer_data: Dict[str, Any]) -> str:
        question = answer_data.get("question", {})
        raw_title = question.get("title")
        if raw_title:
            try:
                title_data = json.loads(raw_title)
                sections = title_data.get("sections", [])
                if sections and sections[0].get("spans"):
                    return sections[0]["spans"][0].get("text", "").strip()
            except Exception:  # pragma: no cover - fallback branch
                pass
        return question.get("titlePlaintext", "").strip()

    def build_contents(self, answer_data: Dict[str, Any]) -> List[ContentItem]:
        contents: List[ContentItem] = []
        raw_content = answer_data.get("content", {})
        if isinstance(raw_content, str):
            try:
                content_data = json.loads(raw_content)
            except json.JSONDecodeError:
                content_data = {}
        else:
            content_data = raw_content

        for section in content_data.get("sections", []):
            if section.get("type") == "image":
                for span in section.get("spans", []):
                    modifiers = span.get("modifiers", {})
                    image_url = modifiers.get("image")
                    if image_url:
                        contents.append(
                            ContentItem(
                                type=ContentType.IMAGE,
                                content=image_url,
                                desc=modifiers.get("dominant_color", ""),
                            )
                        )
                continue

            for span in section.get("spans", []):
                text = span.get("text", "").strip()
                modifiers = span.get("modifiers", {})
                image_url = modifiers.get("image")
                if image_url:
                    contents.append(
                        ContentItem(
                            type=ContentType.IMAGE,
                            content=image_url,
                            desc=modifiers.get("dominant_color", ""),
                        )
                    )
                elif text:
                    contents.append(ContentItem(type=ContentType.TEXT, content=text))

        return contents

    def parse_content(self, html: str) -> NewsItem:
        answer_json = self.extract_answer_json(html)
        if not answer_json:
            raise ValueError("提取回答数据失败")

        answer_data = answer_json["data"]["answer"]

        title = self.extract_question_title(answer_data)
        meta_info = self.extract_answer_meta(answer_data)
        contents = self.build_contents(answer_data)

        return self.compose_news_item(
            title=title,
            meta_info=meta_info,
            contents=contents,
            news_id=str(answer_data.get("aid", self.get_article_id())),
            extra={
                "question_id": answer_data.get("qid"),
                "answer_id": answer_data.get("aid"),
            },
        )


if __name__ == "__main__":
    url1 = "https://www.quora.com/What-is-the-best-life-advice-you-would-give/answers/113244679"
    url2 = "https://www.quora.com/Many-foreigners-make-fun-of-India-by-saying-India-is-dirty-and-Indians-are-unhygienic-Are-we-really-that-bad/answer/Abhinandan-59"
    url3 = (
        "https://www.quora.com/Why-could-Mongolia-successfully-get-independence-from-China-"
        "but-Tibet-and-Xinjiang-failed-to-get-Independence-from-China/answer/Harry-Wonderer"
    )
    for url in [url1, url2, url3]:
        crawler = QuoraAnswerCrawler(url, save_path="data/")
        crawler.run()
