from typing import Dict, List, Optional

from common.schemas import BasePixabayResource, BasePixabaySearchResponse
from pydantic import BaseModel, Field


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

    def get_video_by_quality(self, quality: str = "large") -> Optional[VideoFile]:
        """根据质量获取视频文件

        Args:
            quality: 视频质量，可选值：large, medium, small, tiny

        Returns:
            VideoFile | None: 对应质量的视频文件，如果不存在则返回None
        """
        return self.videos.get(quality)


class VideoSearchResponse(BasePixabaySearchResponse):
    """视频搜索响应"""

    hits: List[Video]

    def get_resources(self) -> List[Video]:
        return self.hits
