# News Extractor Backend

新闻提取器后端 API，基于 FastAPI 构建。

## 快速开始

### 1. 安装依赖

```bash
cd backend
uv sync
```

### 2. 运行服务器

```bash
uv run python run.py
```

服务器将在 `http://localhost:8000` 启动。

### 3. 查看 API 文档

访问 `http://localhost:8000/docs` 查看交互式 API 文档（Swagger UI）。

## API 端点

### POST /api/extract

提取新闻内容

**请求体**:
```json
{
  "url": "https://mp.weixin.qq.com/s/xxxxx",
  "output_format": "json",
  "platform": "wechat"
}
```

**响应**:
```json
{
  "status": "success",
  "data": {...},
  "platform": "wechat",
  "extracted_at": "2024-10-15T23:30:00",
  "markdown": "..."
}
```

### GET /api/platforms

获取支持的平台列表

### GET /api/health

健康检查

## 支持的平台

- 今日头条 (toutiao)
- 微信公众号 (wechat)
- Detik News (detik)

## 技术栈

- FastAPI
- Pydantic
- Uvicorn
- 原有爬虫模块
