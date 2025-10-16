from datetime import datetime
import json
import logging
import os
import pathlib
from enum import Enum
import re
from typing import List, Optional
import requests
from pydantic import BaseModel, Field
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

logger = logging.getLogger("QuoraAnswerCrawler")


def init_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class RequestHeaders(BaseModel):
    """请求头"""

    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )


class ContentType(str, Enum):
    """内容类型"""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ContentItem(BaseModel):
    """内容片段"""

    type: ContentType = Field(default=ContentType.TEXT, title="内容类型")
    content: str = Field(default="", title="内容")
    desc: str = Field(default="", title="描述")


class AnwserMetaInfo(BaseModel):
    """新闻元信息"""

    author_name: str = Field(default="", title="作者")
    author_url: Optional[str] = Field(default="", title="作者链接")
    publish_time: Optional[str] = Field(default="", title="发布时间")


class AnwserItem(BaseModel):
    """新闻项"""

    title: str = Field(default="", title="问题标题")
    anwser_url: str = Field(default="", title="回答链接")
    anwser_id: str = Field(default="", title="回答ID")
    meta_info: AnwserMetaInfo = Field(default=AnwserMetaInfo(), title="元信息")
    contents: List[ContentItem] = Field(default=[], title="回答内容")
    texts: List[str] = Field(default=[], title="纯文本内容")
    images: List[str] = Field(default=[], title="图片")
    videos: Optional[List[str]] = Field(default=[], title="视频")


def timestamp_to_date(timestamp: int) -> str:
    """时间戳转日期

    Args:
        timestamp (int): 时间戳

    Returns:
        str: 日期
    """
    if not timestamp:
        return ""

    seconds = timestamp // 1000000

    return datetime.fromtimestamp(seconds).strftime("%Y-%m-%d %H:%M:%S")


class QuoraAnswerCrawler:
    """Quora回答爬虫"""

    def __init__(
        self,
        answer_url: str,
        save_path: str = "data/",
        headers: RequestHeaders = RequestHeaders(),
    ):
        """初始化爬虫

        Args:
            answer_url (str): 回答URL
            save_path (str, optional): 保存路径. Defaults to "data/".
            headers (RequestHeaders, optional): 请求头. Defaults to RequestHeaders().
        """
        init_logger()
        self.answer_url = answer_url
        self.save_path = save_path
        self.save_file_name = self.get_save_json_path()
        self.headers = headers.model_dump()

    def get_article_id(self) -> str:
        """获取文章ID

        Returns:
            str: 文章ID
        """
        try:
            # 去除URL中的参数
            anwser_url = self.answer_url.split("?")[0]
            if "/answers/" in anwser_url:
                return anwser_url.split("/answers/")[-1]
            elif "/answer/" in anwser_url:
                return anwser_url.split("/answer/")[-1]
            else:
                raise Exception(f"解析文章ID失败: {self.answer_url}")
        except Exception as e:
            raise Exception(f"解析文章ID失败: {e}")

    def get_save_json_path(self) -> str:
        """获取保存路径

        Returns:
            str: JSON文件保存路径
        """
        return os.path.join(self.save_path, f"{self.get_article_id()}.json")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def fetch_content(self) -> str:
        """获取页面内容

        Returns:
            str: 页面内容
        """
        logger.info(f"开始获取内容: {self.answer_url}")
        response = requests.get(self.answer_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"获取内容失败: {response.status_code}")
        return response.text

    def extract_answer_json(self, html_content: str) -> Optional[dict]:
        """提取回答的JSON数据，这个网站的数据渲染有点奇葩，导致正则太难写了，fuck!!!

        Args:
            html_content (str): 页面内容

        Returns:
            Optional[Dict]: 回答JSON数据
        """
        pattern = r'push\(("{\\"data\\":{\\"answer\\":.*?}}\")\);'
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

    def extract_anwser_meta_info(self, answer_data: dict) -> AnwserMetaInfo:
        """提取回答信息

        Args:
            answer_json (dict): 回答JSON数据

        Returns:
            AnwserMetaInfo: 回答元信息
        """
        author_name = ""
        if len(answer_data["author"]["names"]) > 0:
            author_name = (
                answer_data["author"]["names"][0]["givenName"]
                + " "
                + answer_data["author"]["names"][0]["familyName"]
            )
        author_url = answer_data["author"].get("profileUrl", "")
        publish_time = timestamp_to_date(answer_data["creationTime"])

        return AnwserMetaInfo(
            author_name=author_name, author_url=author_url, publish_time=publish_time
        )

    def parse_content(self, html: str) -> AnwserItem:
        """解析内容

        Args:
            html (str): 页面内容

        Returns:
            AnwserItem: 解析后的新闻项对象
        """
        answer_json = self.extract_answer_json(html)
        if not answer_json:
            raise Exception("提取回答数据失败")

        answer_data = answer_json["data"]["answer"]

        # 解析问题标题
        question_title = ""
        if answer_data.get("question", {}).get("title"):
            try:
                title_data = json.loads(answer_data["question"]["title"])
                if title_data.get("sections"):
                    question_title = title_data["sections"][0]["spans"][0]["text"]
            except:
                pass

        meta_info = self.extract_anwser_meta_info(answer_data)

        # 解析content
        contents = []
        texts = []
        images = []

        if isinstance(answer_data["content"], str):
            content_data = json.loads(answer_data["content"])
        else:
            content_data = answer_data["content"]

        for section in content_data.get("sections", []):
            # 处理图片类型的section
            if section["type"] == "image":
                for span in section["spans"]:
                    if "modifiers" in span and "image" in span["modifiers"]:
                        image_url = span["modifiers"]["image"]
                        contents.append(
                            ContentItem(
                                type=ContentType.IMAGE,
                                content=image_url,
                                desc=span["modifiers"].get("dominant_color", ""),
                            )
                        )
                        images.append(image_url)
                continue

            # 处理文本内容
            for span in section["spans"]:
                if span["text"].strip():
                    # 检查是否在modifiers中包含图片
                    if "modifiers" in span and "image" in span["modifiers"]:
                        image_url = span["modifiers"]["image"]
                        contents.append(
                            ContentItem(
                                type=ContentType.IMAGE,
                                content=image_url,
                                desc=span["modifiers"].get("dominant_color", ""),
                            )
                        )
                        images.append(image_url)
                    else:
                        # 处理普通文本
                        contents.append(
                            ContentItem(
                                type=ContentType.TEXT, content=span["text"].strip()
                            )
                        )
                        texts.append(span["text"].strip())

        return AnwserItem(
            title=question_title,
            anwser_url=self.answer_url,
            anwser_id=str(answer_data["aid"]),
            meta_info=meta_info,
            contents=contents,
            texts=texts,
            images=images,
        )

    def save_as_json(self, news_item: AnwserItem):
        """保存为JSON

        Args:
            news_item (AnwserItem): 新闻项对象
        """
        pathlib.Path(self.save_path).mkdir(parents=True, exist_ok=True)
        with open(self.save_file_name, "w", encoding="utf-8") as f:
            json.dump(news_item.model_dump(), f, ensure_ascii=False, indent=4)

    def run(self):
        """运行爬虫"""

        @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
        def retry_fetch_content():
            html = self.fetch_content()
            news_item = self.parse_content(html)
            if len(news_item.texts) == 0:
                logger.error(f"获取内容失败: {news_item.title}")
                raise Exception("获取内容失败")
            self.save_as_json(news_item)
            logger.info(f"获取内容成功: {self.answer_url}")

        try:
            retry_fetch_content()
        except RetryError as e:
            logger.error(f"获取内容失败: {self.answer_url}, error: {e}")
            raise e


if __name__ == "__main__":
    url1 = "https://www.quora.com/What-is-the-best-life-advice-you-would-give/answers/113244679"
    url2 = "https://www.quora.com/Many-foreigners-make-fun-of-India-by-saying-India-is-dirty-and-Indians-are-unhygienic-Are-we-really-that-bad/answer/Abhinandan-59"
    url3 = "https://www.quora.com/Why-could-Mongolia-successfully-get-independence-from-China-but-Tibet-and-Xinjiang-failed-to-get-Independence-from-China/answer/Harry-Wonderer?ch=10&oid=1477743745038914&share=066b0c2e&srid=3yuN5t&target_type=answer"
    for url in [url1, url2, url3]:
        crawler = QuoraAnswerCrawler(url, save_path="data/")
        crawler.run()
