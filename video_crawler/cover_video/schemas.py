from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# 常量配置
MAX_RESOURCES_PER_KEYWORD = 10  # 每个关键词最大下载数量
DEFAULT_PER_PAGE = 100  # 每页返回的资源数量
DEFAULT_RETRY_TIMES = 3  # 默认重试次数
DEFAULT_RETRY_DELAY = 1  # 默认重试延迟(秒)


class Keyword(BaseModel):
    """关键词信息"""

    name: str
    slug: str


class VideoRendition(BaseModel):
    """视频清晰度选项"""

    type: str  # fhd, hd, sd, original
    size: int
    width: int
    height: int
    is_plus: bool = Field(alias="isPlus")
    url: str
    codec: str
    bitrate: int


class VideoVariant(BaseModel):
    """视频变体信息"""

    aspect_ratio: str = Field(alias="aspectRatio")
    status: str
    renditions: List[VideoRendition]


class VideoUrls(BaseModel):
    """视频URL信息"""

    mp4: str
    mp4_preview: str = Field(alias="mp4Preview")
    mp4_download: str = Field(alias="mp4Download")


class Video(BaseModel):
    """视频资源模型"""

    id: str
    title: str
    description: Optional[str]
    base_filename: str = Field(alias="baseFilename")
    poster: Optional[str]
    thumbnail: Optional[str]
    state: Optional[str]
    is_vertical: bool = Field(alias="isVertical")
    tags: List[str]
    downloads: Optional[int]
    views: Optional[int]
    likes: Optional[int]
    aspect_ratio: str = Field(alias="aspectRatio")
    duration: Optional[str]
    max_height: Optional[int] = Field(alias="maxHeight")
    max_width: Optional[int] = Field(alias="maxWidth")
    video_id: str = Field(alias="videoId")
    urls: VideoUrls
    is_premium: bool = Field(alias="isPremium")
    keywords: List[Keyword]
    fps: Optional[int]
    is_ai_generated: bool = Field(alias="isAiGenerated")


class VideoSearchResponse(BaseModel):
    """视频搜索响应"""

    page: int
    pages: int
    page_size: int = Field(alias="pageSize")
    total: int
    hits: List[Video]

    @property
    def has_next_page(self) -> bool:
        """是否有下一页"""
        return self.page < self.pages
