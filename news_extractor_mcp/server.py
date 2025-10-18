# -*- coding: utf-8 -*-
"""
Streamable HTTP entry-point for the News Extractor MCP server.
"""

from pathlib import Path
from typing import Any, Literal, Sequence
from urllib.parse import urlparse

import click
from anyio import to_thread
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import uvicorn

try:
    from news_extractor_core.models import NewsItem
    from news_extractor_core.services import (
        ExtractorService,
        detect_platform,
        get_supported_platforms,
        to_markdown,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for local runs
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from news_extractor_core.models import NewsItem
    from news_extractor_core.services import (
        ExtractorService,
        detect_platform,
        get_supported_platforms,
        to_markdown,
    )

SERVER_NAME = "news-extractor"
DEFAULT_PATH = "/mcp"
SUPPORTED_FORMATS: set[str] = {"json", "markdown"}

mcp = FastMCP(
    name=SERVER_NAME,
    instructions="Expose the NewsCrawlerCollection extractors to MCP clients.",
    streamable_http_path=DEFAULT_PATH,
)


def _normalize_url(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("URL 不能为空")
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("请提供包含协议的完整链接")
    return candidate


def _normalize_output_format(value: str | None) -> str:
    if value is None:
        return "json"
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_FORMATS:
        raise ValueError("输出格式仅支持 json 或 markdown")
    return normalized


async def _extract(url: str) -> tuple[NewsItem, str]:
    def run() -> tuple[NewsItem, str]:
        return ExtractorService.extract_news(url)

    return await to_thread.run_sync(run)


def _build_news_payload(
    news: NewsItem,
    *,
    platform: str,
    url: str,
    include_markdown: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "success",
        "url": url,
        "platform": platform,
        "data": news.to_dict(),
    }
    if include_markdown:
        payload["markdown"] = to_markdown(news)
    return payload


@mcp.tool(
    name="extract_news",
    title="提取新闻内容",
    description=(
        "抓取单篇新闻并返回结构化数据或 Markdown 文本。\n"
        "参数：\n"
        "- url: 新闻链接\n"
        "- output_format: 输出格式，'json'（返回结构化JSON数据）或 'markdown'（返回纯Markdown文本），默认为 'json'"
    ),
)
async def extract_news(url: str, output_format: str = "json") -> str | dict[str, Any]:
    normalized_url = _normalize_url(url)
    normalized_format = _normalize_output_format(output_format)
    news, platform = await _extract(normalized_url)

    if normalized_format == "markdown":
        # 直接返回 markdown 文本
        return to_markdown(news)
    else:
        # 返回 JSON 结构
        return _build_news_payload(
            news=news,
            platform=platform,
            url=normalized_url,
            include_markdown=False,
        )


@mcp.tool(
    name="batch_extract_news",
    title="批量提取新闻",
    description=(
        "依次抓取多个新闻链接，返回成功/失败统计。\n"
        "参数：\n"
        "- urls: 新闻链接列表\n"
        "- output_format: 输出格式，'json'（返回结构化JSON数据）或 'markdown'（返回合并的Markdown文本），默认为 'json'"
    ),
)
async def batch_extract_news(urls: list, output_format: str = "json") -> str | dict[str, Any]:
    if not urls:
        raise ValueError("请提供至少一个 URL")

    normalized_format = _normalize_output_format(output_format)

    results: list[dict[str, Any]] = []
    markdown_parts: list[str] = []
    success = 0

    for raw in urls:
        try:
            normalized_url = _normalize_url(raw)
            news, platform = await _extract(normalized_url)

            if normalized_format == "markdown":
                # 收集 markdown 内容
                markdown_parts.append(f"## {news.title}\n\n**来源**: {normalized_url}\n**平台**: {platform}\n\n{to_markdown(news)}\n\n---\n")
            else:
                # 收集 JSON 数据
                payload = _build_news_payload(
                    news=news,
                    platform=platform,
                    url=normalized_url,
                    include_markdown=False,
                )
                results.append(payload)
            success += 1
        except Exception as exc:
            if normalized_format == "markdown":
                markdown_parts.append(f"## ❌ 提取失败\n\n**URL**: {raw}\n**错误**: {str(exc)}\n\n---\n")
            else:
                results.append(
                    {
                        "status": "error",
                        "url": str(raw),
                        "message": str(exc),
                    }
                )

    if normalized_format == "markdown":
        # 返回合并的 markdown 文本
        header = f"# 批量提取结果\n\n总计: {len(urls)} | 成功: {success} | 失败: {len(urls) - success}\n\n---\n\n"
        return header + "\n".join(markdown_parts)
    else:
        # 返回 JSON 结构
        return {
            "status": "success",
            "total": len(results),
            "successful": success,
            "failed": len(results) - success,
            "results": results,
        }


@mcp.tool(
    name="detect_news_platform",
    title="识别新闻平台",
    description="根据链接识别所属新闻平台。",
    structured_output=True,
)
async def detect_news_platform(url: str) -> dict[str, Any]:
    normalized_url = _normalize_url(url)
    platform = detect_platform(normalized_url)
    if not platform:
        raise ValueError("无法识别该平台")

    platforms = {item["id"]: item for item in get_supported_platforms()}
    info = platforms.get(platform, {})
    return {
        "status": "success",
        "url": normalized_url,
        "platform": platform,
        "name": info.get("name", "Unknown"),
        "icon": info.get("icon", ""),
    }


@mcp.tool(
    name="list_supported_platforms",
    title="列出支持的平台",
    description="返回当前可用的新闻平台清单。",
    structured_output=True,
)
async def list_supported_platforms() -> dict[str, Any]:
    platforms = get_supported_platforms()
    return {
        "status": "success",
        "platforms": platforms,
        "total": len(platforms),
    }


@mcp.resource("platforms://list", title="Supported Platforms")
def platforms_resource() -> str:
    lines = ["# Supported News Platforms", ""]
    for item in get_supported_platforms():
        lines.append(f"- **{item.get('icon', '')} {item.get('name', 'Unknown')}** (`{item.get('id', '')}`)")
    return "\n".join(lines)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> Response:
    return JSONResponse({"status": "ok", "name": SERVER_NAME})


@click.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="绑定的主机地址")
@click.option("--port", default=8765, show_default=True, help="HTTP 端口")
@click.option(
    "--path",
    default=DEFAULT_PATH,
    show_default=True,
    help="Streamable HTTP 路径，客户端需指向该路径",
)
def main(host: str, port: int, path: str) -> None:
    """
    Run the streamable HTTP MCP server.
    """
    mcp.settings.streamable_http_path = path
    app = mcp.streamable_http_app()
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
