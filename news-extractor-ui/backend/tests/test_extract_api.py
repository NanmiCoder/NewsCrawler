import json
from contextlib import ExitStack
from pathlib import Path
from typing import Dict, NamedTuple, Optional
from unittest.mock import patch

import pytest

from app.adapters.base import NewsItem as AdapterNewsItem
from news_crawler.detik_news import DetikNewsCrawler
from news_crawler.lennysnewsletter import LennysNewsletterCrawler
from news_crawler.naver_news import NaverNewsCrawler
from news_crawler.netease_news import NeteaseNewsCrawler
from news_crawler.quora import QuoraAnswerCrawler
from news_crawler.toutiao_news import ToutiaoNewsCrawler
from news_crawler.wechat_news import WeChatNewsCrawler


class _TestCase(NamedTuple):
    platform: str
    crawler_cls: object
    fixture_name: str
    url: str
    init_patches: Optional[Dict[str, object]]


TEST_CASES: tuple[_TestCase, ...] = (
    (
        "wechat",
        WeChatNewsCrawler,
        "wechat",
        "https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw",
        None,
    ),
    (
        "toutiao",
        ToutiaoNewsCrawler,
        "toutiao",
        "https://www.toutiao.com/article/7404384826024935990/",
        None,
    ),
    (
        "netease",
        NeteaseNewsCrawler,
        "netease",
        "https://www.163.com/news/article/KC12OUHK000189FH.html",
        None,
    ),
    (
        "detik",
        DetikNewsCrawler,
        "detik",
        "https://news.detik.com/internasional/d-7626006/5-pernyataan-trump-di-pidato-kemenangan-pilpres-as",
        None,
    ),
    (
        "lenny",
        LennysNewsletterCrawler,
        "lenny",
        "https://www.lennysnewsletter.com/p/how-to-ship-ai-features",
        None,
    ),
    (
        "naver",
        NaverNewsCrawler,
        "naver",
        "https://blog.naver.com/orangememories/223618759620",
        {
            "get_iframe_url_path": "https://blog.naver.com/PostView.naver?blogId=orangememories&logNo=223618759620&redirect=Dlog&widgetTypeCall=true&noTrackingCode=true&directAccess=false"  # noqa: E501
        },
    ),
    (
        "quora",
        QuoraAnswerCrawler,
        "quora",
        "https://www.quora.com/Why-could-Mongolia-successfully-get-independence-from-China-but-Tibet-and-Xinjiang-failed-to-get-Independence-from-China/answer/Harry-Wonderer?ch=10&oid=1477743745038914&share=066b0c2e&srid=3yuN5t&target_type=answer",  # noqa: E501
        None,
    ),
)


def load_expected_payload(
    platform: str, fixtures_dir: Path, fixture_name: str
) -> Dict[str, object]:
    json_path = fixtures_dir / f"{fixture_name}.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    transformed = {
        "title": data.get("title", ""),
        "news_url": data.get("news_url", ""),
        "news_id": data.get("news_id", ""),
        "meta_info": data.get("meta_info", {}),
        "contents": data.get("contents", []),
        "texts": data.get("texts", []),
        "images": data.get("images", []),
        "videos": data.get("videos", []),
    }

    return AdapterNewsItem(transformed).to_dict()


@pytest.mark.parametrize("platform,crawler_cls,fixture_name,url,init_patches", TEST_CASES)
def test_extract_api_returns_expected_payload(
    client,
    fixtures_dir: Path,
    platform: str,
    crawler_cls,
    fixture_name: str,
    url: str,
    init_patches: Optional[Dict[str, object]],
) -> None:
    html_path = fixtures_dir / f"{fixture_name}.html"
    html_content = html_path.read_text(encoding="utf-8")

    expected_payload = load_expected_payload(platform, fixtures_dir, fixture_name)

    patchers = []
    if init_patches:
        for attr, value in init_patches.items():
            patchers.append(patch.object(crawler_cls, attr, return_value=value))

    patchers.append(patch.object(crawler_cls, "fetch_content", return_value=html_content))

    with ExitStack() as stack:
        for patcher in patchers:
            stack.enter_context(patcher)
        response = client.post(
            "/api/extract",
            json={
                "url": url,
                "platform": platform,
                "output_format": "json",
            },
        )

    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["platform"] == platform
    assert payload["data"] == expected_payload
    # Ensure markdown is generated to help downstream UI toggles
    assert isinstance(payload["markdown"], str) and payload["markdown"].strip()
