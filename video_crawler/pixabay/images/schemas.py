from typing import List, Optional

from common.schemas import BasePixabayResource, BasePixabaySearchResponse
from pydantic import BaseModel, Field


class Image(BasePixabayResource):
    """图片资源模型"""

    # 预览图相关
    preview_url: str = Field(alias="previewURL")
    preview_width: int = Field(alias="previewWidth")
    preview_height: int = Field(alias="previewHeight")

    # 网页格式图片 (640px)
    webformat_url: str = Field(alias="webformatURL")
    webformat_width: int = Field(alias="webformatWidth")
    webformat_height: int = Field(alias="webformatHeight")
    webformat_size: Optional[int] = Field(alias="webformatSize", default=None)

    # 大图 (1280px)
    large_image_url: str = Field(alias="largeImageURL")

    # 全高清图片 (1920px) - 可选
    full_hd_url: Optional[str] = Field(alias="fullHDURL", default=None)

    # 原始图片
    image_url: Optional[str] = Field(alias="imageURL", default=None)
    image_width: int = Field(alias="imageWidth")
    image_height: int = Field(alias="imageHeight")
    image_size: int = Field(alias="imageSize")

    # 其他元数据
    views: int
    downloads: int
    likes: int
    comments: int
    user_id: int = Field(alias="user_id")
    user: str
    user_image_url: str = Field(alias="userImageURL")


class ImageSearchResponse(BasePixabaySearchResponse):
    """图片搜索响应"""

    hits: List[Image]

    def get_resources(self) -> List[Image]:
        return self.hits
