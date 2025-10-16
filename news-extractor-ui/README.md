# 新闻提取器 UI

一个现代化的新闻提取器 Web 应用，支持从多个平台（微信公众号、今日头条、Detik等）提取新闻内容，并导出为 JSON 或 Markdown 格式。

## ✨ 特性

- 🎯 **智能识别** - 自动识别新闻平台，无需手动选择
- 📰 **多平台支持** - 微信公众号、今日头条、Detik News 等
- 📦 **双格式导出** - 支持 JSON 和 Markdown 两种格式
- 🚀 **实时进度** - 提取过程进度实时展示
- 💅 **现代UI** - 基于 Vue 3，简洁美观的界面
- ⚡ **高性能** - FastAPI 后端，响应迅速

## 🏗️ 技术栈

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全
- **Vite** - 极速构建工具
- **Pinia** - 状态管理
- **Axios** - HTTP 客户端

### 后端
- **FastAPI** - 现代化 Python Web 框架
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI 服务器
- **原有爬虫模块** - 复用项目现有爬虫

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Node.js 18+
- uv (Python 包管理器)

### 1. 安装依赖

#### 后端
```bash
cd news-extractor-ui/backend
uv sync
```

#### 前端
```bash
cd news-extractor-ui/frontend
npm install
```

### 2. 启动服务

#### 启动后端 (终端1)
```bash
cd backend
uv run python run.py
```

后端将在 `http://localhost:8000` 启动

#### 启动前端 (终端2)
```bash
cd frontend
npm run dev
```

前端将在 `http://localhost:3000` 启动

### 3. 访问应用

打开浏览器访问 `http://localhost:3000`

## 📖 使用说明

1. **输入链接** - 在输入框中粘贴新闻链接
2. **选择格式** - 选择 JSON 或 Markdown 输出格式
3. **开始提取** - 点击"开始提取"按钮
4. **查看结果** - 等待提取完成，查看结果
5. **导出** - 下载或复制提取的内容

## 🌐 支持的平台

| 平台 | URL 示例 | 状态 |
|------|---------|------|
| 微信公众号 | `https://mp.weixin.qq.com/s/xxxxx` | ✅ |
| 今日头条 | `https://www.toutiao.com/article/xxxxx` | ✅ |
| Detik News | `https://news.detik.com/...` | ✅ |
| Naver News | `https://blog.naver.com/...` | 🚧 开发中 |
| Lenny's Newsletter | `https://www.lennysnewsletter.com/...` | 🚧 开发中 |
| Quora | `https://www.quora.com/...` | 🚧 开发中 |

## 📁 项目结构

```
news-extractor-ui/
├── backend/                # 后端 FastAPI 应用
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── adapters/      # 爬虫适配器
│   │   ├── services/      # 业务逻辑
│   │   └── main.py        # 主应用
│   ├── pyproject.toml
│   └── run.py             # 启动脚本
│
├── frontend/              # 前端 Vue 3 应用
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   ├── services/      # API 服务
│   │   ├── types/         # TypeScript 类型
│   │   └── App.vue        # 根组件
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## 🔌 API 文档

### POST /api/extract
提取新闻内容

**Request:**
```json
{
  "url": "https://mp.weixin.qq.com/s/xxxxx",
  "output_format": "json",
  "platform": "wechat"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {...},
  "platform": "wechat",
  "extracted_at": "2024-10-15T23:30:00",
  "markdown": "..."
}
```

访问 `http://localhost:8000/docs` 查看完整 API 文档。

## 🛠️ 开发指南

### 添加新平台支持

1. 在 `backend/app/adapters/` 创建新的适配器
2. 在 `backend/app/services/extractor.py` 注册适配器
3. 在 `backend/app/services/detector.py` 添加 URL 模式

### 修改 UI 样式

编辑 `frontend/src/assets/main.css` 中的 CSS 变量。

## 📝 注意事项

- 爬虫请遵守目标网站的 robots.txt 和服务条款
- 本项目仅供学习研究使用，禁止商业用途
- Cookie 可能会过期，需要定期更新

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
