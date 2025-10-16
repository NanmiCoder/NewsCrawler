from typing import List, Optional

from common.schemas import BaseResource, BaseSearchResponse
from pydantic import BaseModel


class VideoFile(BaseModel):
    """视频文件信息"""

    id: int
    quality: Optional[str]
    file_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    link: str


class VideoUser(BaseModel):
    """视频作者信息"""

    id: Optional[int]
    name: Optional[str]
    url: Optional[str]


class VideoPicture(BaseModel):
    """视频预览图"""

    id: int
    picture: Optional[str]
    nr: Optional[int]


class Video(BaseResource):
    """视频资源模型"""

    duration: Optional[int]
    image: Optional[str]
    user: Optional[VideoUser]
    video_files: List[VideoFile]
    video_pictures: List[VideoPicture]


class VideoSearchResponse(BaseSearchResponse):
    """视频搜索响应"""

    videos: List[Video]
    url: str

    def get_resources(self) -> List[Video]:
        return self.videos
