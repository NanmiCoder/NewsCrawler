# -*- coding: utf-8 -*-
"""
FastAPI 主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import extract, proxy

# 创建 FastAPI 应用
app = FastAPI(
    title="News Extractor API",
    description="新闻提取器后端 API",
    version="0.1.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(extract.router, prefix="/api", tags=["extract"])
app.include_router(proxy.router, prefix="/api/proxy", tags=["proxy"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "News Extractor API",
        "version": "0.1.0",
        "docs": "/docs"
    }
