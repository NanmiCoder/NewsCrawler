from typing import List, Optional

from common.schemas import BaseResource, BaseSearchResponse
from pydantic import BaseModel


class VideoFile(BaseModel):
    """视频文件信息"""

    id: int
    quality: str
    file_type: str
    width: Optional[int]
    height: Optional[int]
    link: str


class VideoUser(BaseModel):
    """视频作者信息"""

    id: int
    name: str
    url: str


class VideoPicture(BaseModel):
    """视频预览图"""

    id: int
    picture: str
    nr: int


class Video(BaseResource):
    """视频资源模型"""

    duration: int
    image: str
    user: VideoUser
    video_files: List[VideoFile]
    video_pictures: List[VideoPicture]


class VideoSearchResponse(BaseSearchResponse):
    """视频搜索响应"""

    videos: List[Video]
    url: str

    def get_resources(self) -> List[Video]:
        return self.videos
