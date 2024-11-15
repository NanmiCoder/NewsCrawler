from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# 常量配置
MAX_RESOURCES_PER_KEYWORD = 10  # 每个关键词最大下载数量
DEFAULT_PER_PAGE = 200  # 每页返回的资源数量
DEFAULT_RETRY_TIMES = 3  # 默认重试次数
DEFAULT_RETRY_DELAY = 1  # 默认重试延迟(秒)


class ProxyAuth(BaseModel):
    """代理认证信息"""

    username: str
    password: str


class ProxyConfig(BaseModel):
    """代理配置"""

    host: str
    port: int
    auth: Optional[ProxyAuth] = None
    protocol: str = "http"

    def to_proxy_dict(self) -> dict:
        """转换为requests库使用的代理格式"""
        auth_str = f"{self.auth.username}:{self.auth.password}@" if self.auth else ""
        proxy_str = f"{self.protocol}://{auth_str}{self.host}:{self.port}"
        return {"http": proxy_str, "https": proxy_str}


class BasePixabayResource(BaseModel):
    """Pixabay基础资源模型"""

    id: int
    page_url: str = Field(alias="pageURL")
    type: str
    tags: str
    views: int
    downloads: int
    likes: int
    comments: int
    user_id: int
    user: str
    user_image_url: str = Field(alias="userImageURL")


class BasePixabaySearchResponse(BaseModel):
    """Pixabay基础搜索响应"""

    total: int
    total_hits: int = Field(alias="totalHits")
    hits: List[BasePixabayResource]

    @property
    def has_next_page(self) -> bool:
        """是否有下一页"""
        return len(self.hits) > 0


class VideoFile(BaseModel):
    """视频文件信息"""

    url: str
    width: int
    height: int
    size: int
    thumbnail: str


class Video(BasePixabayResource):
    """视频资源模型"""

    duration: int
    videos: Dict[str, VideoFile]
    video_large: VideoFile = Field(default=None)
    video_medium: VideoFile = Field(default=None)
    video_small: VideoFile = Field(default=None)
    video_tiny: VideoFile = Field(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        # 将videos字典中的文件信息转换为属性
        if self.videos:
            for quality, file_info in self.videos.items():
                setattr(self, f"video_{quality}", VideoFile(**file_info))


class VideoSearchResponse(BasePixabaySearchResponse):
    """视频搜索响应"""

    hits: List[Video]


class Image(BasePixabayResource):
    """图片资源模型"""

    preview_url: str = Field(alias="previewURL")
    preview_width: int = Field(alias="previewWidth")
    preview_height: int = Field(alias="previewHeight")
    webformat_url: str = Field(alias="webformatURL")
    webformat_width: int = Field(alias="webformatWidth")
    webformat_height: int = Field(alias="webformatHeight")
    large_image_url: str = Field(alias="largeImageURL")
    full_hd_url: Optional[str] = Field(alias="fullHDURL", default=None)
    image_url: Optional[str] = Field(alias="imageURL", default=None)
    image_width: int = Field(alias="imageWidth")
    image_height: int = Field(alias="imageHeight")
    image_size: int = Field(alias="imageSize")


class ImageSearchResponse(BasePixabaySearchResponse):
    """图片搜索响应"""

    hits: List[Image]
