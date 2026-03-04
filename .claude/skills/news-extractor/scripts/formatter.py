# -*- coding: utf-8 -*-
"""
格式化服务 - 将 NewsItem 转换为 Markdown
"""
from models import NewsItem


def to_markdown(news_item: NewsItem, platform: str = "default") -> str:
    """
    将 NewsItem 转换为 Markdown 格式

    Args:
        news_item: 新闻数据
        platform: 平台名称

    Returns:
        Markdown 格式的字符串
    """
    md_lines = []

    # 标题
    md_lines.append(f"# {news_item.title}\n")

    # 元信息
    meta = news_item.meta_info
    md_lines.append("## 文章信息\n")
    if meta.author_name:
        md_lines.append(f"**作者**: {meta.author_name}  ")
    if meta.publish_time:
        md_lines.append(f"**发布时间**: {meta.publish_time}  ")
    md_lines.append(f"**原文链接**: [{news_item.news_url}]({news_item.news_url})\n")
    md_lines.append("---\n")

    # 正文内容
    md_lines.append("## 正文内容\n")
    for content in news_item.contents:
        content_type = content.type.value if hasattr(content.type, 'value') else content.type
        content_text = content.content

        if content_type == "text":
            md_lines.append(f"{content_text}\n")
        elif content_type == "image":
            md_lines.append(f"![图片]({content_text})\n")
        elif content_type == "video":
            md_lines.append(f"[视频]({content_text})\n")

    # 媒体资源统计
    if news_item.images or news_item.videos:
        md_lines.append("\n---\n")
        md_lines.append("## 媒体资源\n")

        if news_item.images:
            md_lines.append(f"\n### 图片 ({len(news_item.images)})\n")
            for idx, img_url in enumerate(news_item.images, 1):
                md_lines.append(f"{idx}. {img_url}\n")

        if news_item.videos:
            md_lines.append(f"\n### 视频 ({len(news_item.videos)})\n")
            for idx, video_url in enumerate(news_item.videos, 1):
                md_lines.append(f"{idx}. {video_url}\n")

    return "\n".join(md_lines)
