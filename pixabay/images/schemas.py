from typing import List, Optional

from common.schemas import BasePixabayResource, BasePixabaySearchResponse
from pydantic import BaseModel, Field


class Image(BasePixabayResource):
    """图片资源模型"""

    webformat_url: str = Field(alias="webformatURL")
    large_image_url: str = Field(alias="largeImageURL")
    preview_url: str = Field(alias="previewURL")
    type: str
    webformat_width: int = Field(alias="webformatWidth")
    webformat_height: int = Field(alias="webformatHeight")


class ImageSearchResponse(BasePixabaySearchResponse):
    """图片搜索响应"""

    hits: List[Image]

    def get_resources(self) -> List[Image]:
        return self.hits
