# -*- coding: utf-8 -*-
# author: relakkes@gmail.com
# date: 2024-11-15
# description: Pexels API返回的数据模型

from typing import List, Optional
from pydantic import BaseModel
from common.schemas import BaseResource, BaseSearchResponse


class PhotoSource(BaseModel):
    """图片源信息"""

    original: str
    large2x: str
    large: str
    medium: str
    small: str
    portrait: str
    landscape: str
    tiny: str


class Photo(BaseResource):
    """图片资源模型"""

    photographer: str
    photographer_url: str
    photographer_id: int
    avg_color: str
    src: PhotoSource
    liked: bool
    alt: str


class PhotoSearchResponse(BaseSearchResponse):
    """图片搜索响应"""

    photos: List[Photo]

    def get_resources(self) -> List[Photo]:
        return self.photos
