from typing import List, Optional

from pydantic import BaseModel, Field

# 常量配置
MAX_RESOURCES_PER_KEYWORD = 10  # 每个关键词最大下载数量
DEFAULT_PER_PAGE = 100  # 每页返回的资源数量
DEFAULT_RETRY_TIMES = 3  # 默认重试次数
DEFAULT_RETRY_DELAY = 1  # 默认重试延迟(秒)


class MixkitVideo(BaseModel):
    """Mixkit视频信息模型"""

    id: str
    title: str
    video_detail_url: Optional[str]
    download_360_video_url: str
    download_1080_video_url: str


class VideoSearchResponse(BaseModel):
    """视频搜索响应"""

    page: int
    total_pages: int
    hits: List[MixkitVideo]

    @property
    def has_next_page(self) -> bool:
        """是否有下一页"""
        return self.page < self.total_pages
