# -*- coding: utf-8 -*-
"""
图片代理 API - 解决微信公众号图片防盗链问题
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import requests
from typing import Optional

router = APIRouter()


@router.get("/image")
async def proxy_image(url: str = Query(..., description="图片URL")):
    """
    代理获取图片，解决防盗链问题

    Args:
        url: 图片的原始URL

    Returns:
        图片的二进制流
    """
    try:
        # 设置请求头，伪装成微信公众号平台的请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://mp.weixin.qq.com/',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        # 请求图片
        response = requests.get(url, headers=headers, timeout=10, stream=True)

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="图片获取失败")

        # 获取内容类型
        content_type = response.headers.get('content-type', 'image/jpeg')

        # 返回图片流
        return StreamingResponse(
            response.iter_content(chunk_size=8192),
            media_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=86400',  # 缓存1天
                'Access-Control-Allow-Origin': '*',
            }
        )

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"请求图片失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代理图片失败: {str(e)}")
