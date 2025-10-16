# -*- coding: utf-8 -*-
"""
提取 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from ..services.extractor import ExtractorService
from ..services.formatter import to_markdown
from ..services.detector import get_supported_platforms

router = APIRouter()


class ExtractRequest(BaseModel):
    """提取请求"""
    url: str = Field(..., description="新闻链接")
    output_format: str = Field(default="json", description="输出格式: json 或 markdown")
    platform: Optional[str] = Field(default=None, description="平台名称（可选，自动检测）")


class ExtractResponse(BaseModel):
    """提取响应"""
    status: str
    data: Optional[Dict[str, Any]] = None
    markdown: Optional[str] = None
    platform: Optional[str] = None
    extracted_at: str
    error: Optional[Dict[str, str]] = None


@router.post("/extract", response_model=ExtractResponse)
async def extract_news(request: ExtractRequest):
    """提取新闻内容"""
    try:
        # 提取新闻
        news_item, platform = ExtractorService.extract_news(
            url=request.url,
            platform=request.platform
        )

        # 准备响应数据
        response_data = {
            "status": "success",
            "data": news_item.to_dict(),
            "platform": platform,
            "extracted_at": datetime.now().isoformat(),
            # 总是生成 markdown，方便前端切换格式
            "markdown": to_markdown(news_item)
        }

        return response_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "error": {
                "code": "EXTRACTION_FAILED",
                "message": str(e)
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"服务器内部错误: {str(e)}"
            }
        })


@router.get("/platforms")
async def list_platforms():
    """获取支持的平台列表"""
    return {
        "status": "success",
        "platforms": get_supported_platforms()
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
