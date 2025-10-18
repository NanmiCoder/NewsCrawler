<div align="center">

# 🌐 NewsCrawler

**多平台新闻 & 内容爬虫集合**


支持微信公众号、今日头条、网易新闻、搜狐、腾讯、Naver、Detik、Quora 等 9+ 主流平台

提供命令行调用、可视化 Web UI、统一 JSON 输出、支持MCP协议

[![GitHub stars](https://img.shields.io/github/stars/NanmiCoder/NewsCrawler?style=social)](https://github.com/NanmiCoder/NewsCrawler/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/NanmiCoder/NewsCrawler?style=social)](https://github.com/NanmiCoder/NewsCrawler/network/members)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Educational-green.svg)](LICENSE)

[English](README.en.md) · 中文

</div>

---

![Web UI 界面](static/images/01_webui.png)

**开箱即用的 Web UI** - 自动识别平台、实时提取进度、JSON/Markdown 双格式导出

---

## 🎯 为什么选择 NewsCrawler?

<div align="center">

| 🌍 多平台支持 | 🎨 双模式使用 | 📦 标准化输出 | ⚡ 快速部署 | 🤖 MCP 支持 |
|:---:|:---:|:---:|:---:|:---:|
| 9+ 主流平台<br/>覆盖中英韩印尼 | Python API<br/>+ Web UI | 统一 JSON 格式<br/>易于集成 | uv 包管理器<br/>极速安装 | 集成各类AI总结文章 |


</div>

**核心特性:**

- ✅ **全平台覆盖** - 支持微信公众号、今日头条、网易、搜狐、腾讯、Lenny's Newsletter、Naver Blog、Detik News、Quora
- ✅ **智能提取** - 自动识别平台类型,提取标题、正文、图片、视频等多媒体内容
- ✅ **统一输出** - 所有平台输出标准化 JSON 格式,完美适配数据分析、入库、下游处理
- ✅ **灵活使用** - 支持 Python API(自动化) + Web UI(可视化) + MCP Server(AI Agent)
- ✅ **一键部署** - Docker Compose 编排所有服务(后端 + 前端 + MCP)
- ✅ **AI 智能体集成** - 支持 MCP 协议,可接入 Claude Desktop 等 AI 工具
- ✅ **模块化设计** - 各平台爬虫解耦,易于扩展新平台或优化现有实现
- ✅ **轻量高效** - 使用 uv 管理依赖,安装快速,运行稳定

---

## 🚀 快速开始

### 方式一:Docker Compose (⭐ 推荐 - 一键部署)

```bash
# 1. 安装 Docker 和 Docker Compose
# 访问: https://docs.docker.com/get-docker/

# 2. 克隆项目
git clone https://github.com/NanmiCoder/NewsCrawler.git
cd NewsCrawler

# 3. 一键启动所有服务(后端 + 前端 + MCP)
docker compose up -d

# 4. 访问服务
# - 前端界面: http://localhost:3000
# - 后端 API: http://localhost:8000/docs
# - MCP 服务: http://localhost:8765/health
```

**包含服务:**
- ✅ **Backend 服务** (FastAPI) - 新闻提取 API
- ✅ **Frontend 服务** (Vue 3 + Nginx) - Web UI 界面
- ✅ **MCP 服务** - AI Agent 工具(支持 Claude Desktop)
- ✅ **自动健康检查** - 确保所有服务正常运行
- ✅ **数据持久化** - 提取的新闻保存在 `./data/` 目录

**Docker 管理命令:**
```bash
# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 代码更新后重新构建
docker compose up -d --build
```

📖 **完整文档**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

---

### 方式二:Web UI (手动部署)

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# 或: pip install uv

# 2. 克隆项目
git clone https://github.com/NanmiCoder/NewsCrawler.git
cd NewsCrawler

# 3. 启动后端
cd news-extractor-ui/backend
uv sync && uv run run.py

# 4. 启动前端 (新终端)
cd news-extractor-ui/frontend
npm install && npm run dev

# 5. 访问 http://localhost:3000
```

**Web UI 功能:**
- 🎯 粘贴 URL,自动识别平台类型
- 📊 实时显示提取进度
- 📄 支持 JSON / Markdown 双格式导出
- 🖼️ 内容预览与一键下载

---

### 方式三:Python API (适合自动化集成)

```python
from news_crawler.wechat_news import WeChatNewsCrawler
from news_crawler.toutiao_news import ToutiaoNewsCrawler

# 微信公众号
wechat_url = "https://mp.weixin.qq.com/s/xxxxxx"
crawler = WeChatNewsCrawler(wechat_url)
result = crawler.run()  # 自动保存到 data/ 目录

# 今日头条
toutiao_url = "https://www.toutiao.com/article/xxxxxx"
crawler = ToutiaoNewsCrawler(toutiao_url)
result = crawler.run()

print(result)  # 返回 JSON 格式数据
```

**运行示例:**
```bash
uv run call_example.py  # 查看完整示例
```

---

### 方式四:MCP Server (AI 智能体集成)

**什么是 MCP?**
[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 是一个连接 AI 助手(如 Claude Desktop)与外部工具和数据源的标准协议。

**使用场景:**
- 🤖 让 Claude、Cursor、ChatGPT等工具通过对话直接提取新闻内容
- 🔄 通过 AI 指令批量处理多个 URL
- 📊 AI 驱动的内容分析工作流
- 🚀 构建具有新闻提取能力的自定义 AI 智能体

**快速配置:**

```bash
# 1. 启动 MCP 服务(推荐使用 Docker)
docker compose up -d mcp

# 2. 或手动启动
uv run news-extractor-mcp --host 0.0.0.0 --port 8765

# 3. MCP 服务运行在: http://localhost:8765/mcp
```

**AI 工具配置 (Streamable HTTP 方式):**

<details>
<summary><b>Cursor</b> (点击展开)</summary>

配置文件位置: `~/.cursor/mcp.json` (全局) 或 `.cursor/mcp.json` (项目级别)

```json
{
  "mcpServers": {
    "newscrawler": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```
</details>

<details>
<summary><b>Windsurf</b> (点击展开)</summary>

配置文件位置: `~/.codeium/windsurf/mcp_server_config.json`

```json
{
  "mcpServers": {
    "newscrawler": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```
</details>

<details>
<summary><b>Trae</b> (点击展开)</summary>

设置 → 工具 → MCP 服务器 → 添加服务器

```json
{
  "name": "newscrawler",
  "url": "http://127.0.0.1:8765/mcp"
}
```
</details>

<details>
<summary><b>Claude Desktop</b> (点击展开)</summary>

配置文件位置:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "newscrawler": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```
</details>

<details>
<summary><b>其他支持 MCP 的工具</b> (点击展开)</summary>

所有支持 Streamable HTTP 传输的 MCP 客户端都可以使用以下配置:

```json
{
  "mcpServers": {
    "newscrawler": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

**注意**: 如果使用 Docker 且 AI 工具运行在 Docker 外，请将 `127.0.0.1` 替换为宿主机 IP 或 `host.docker.internal`
</details>

**可用 MCP 工具:**
- `extract_news` - 提取单篇新闻(JSON 或 Markdown 格式)
- `batch_extract_news` - 批量提取多个 URL
- `detect_news_platform` - 从 URL 识别平台类型
- `list_supported_platforms` - 显示所有支持的平台


📖 **完整 MCP 文档**: [news_extractor_mcp/README.md](news_extractor_mcp/README.md)

---

## 📦 支持的平台

### 新闻 / 内容平台

| 平台 | URL 示例 | 语言 | 特性 |
|------|---------|------|------|
| 微信公众号 | `mp.weixin.qq.com` | 中文 | 支持图文提取 |
| 今日头条 | `toutiao.com` | 中文 | 富媒体内容|
| 网易新闻 | `163.com` | 中文 | 图片画廊支持 |
| 搜狐新闻 | `sohu.com` | 中文 | 多媒体内容 |
| 腾讯新闻 | `news.qq.com` | 中文 | 新闻支持 |
| Lenny's Newsletter | `lennysnewsletter.com` | 英文 | 长文内容 |
| Naver Blog | `blog.naver.com` | 韩语 | 博客平台 |
| Detik News | `detik.com` | 印尼语 | 东南亚新闻 |
| Quora | `quora.com` | 英文 | 问答内容 |

### 视频素材平台
**Pexels** · **Pixabay** · **Coverr** · **Mixkit** - 高质量免费视频素材下载

---

## 💡 使用场景

```
📰 多源新闻聚合平台 / 舆情监控系统
📊 媒体内容分析、数据挖掘、推荐系统
🔬 学术研究 / 数据科学 - 跨平台内容抓取
🎓 教学项目 / 个人学习 - 爬虫框架模板
🤖 AI 训练数据采集 / 内容质量分析
```

---

## 📊 数据输出格式

所有爬虫输出统一的 JSON 格式,保存在 `data/` 目录:

```json
{
  "title": "文章标题",
  "news_url": "原文链接",
  "news_id": "文章ID",
  "meta_info": {
    "author_name": "作者名称",
    "author_url": "作者主页",
    "publish_time": "2024-10-15 10:30:00"
  },
  "contents": [
    {"type": "text", "content": "段落文本内容", "desc": ""},
    {"type": "image", "content": "https://example.com/image.jpg", "desc": "图片描述"},
    {"type": "video", "content": "https://example.com/video.mp4", "desc": "视频描述"}
  ],
  "texts": ["段落1文本", "段落2文本"],
  "images": ["图片URL1", "图片URL2"],
  "videos": ["视频URL1"]
}
```

**字段说明:**
- `contents` - 结构化内容,保留顺序和类型(文本/图片/视频)
- `texts/images/videos` - 扁平化列表,便于快速访问特定类型内容
- `meta_info` - 文章元信息(作者、发布时间等)

---

## 🔧 技术架构

### 后端技术
**Python 3.8+** · **FastAPI** · **Pydantic** · **curl_cffi** · **parsel** · **tenacity**

### 前端技术
**Vue 3** · **TypeScript** · **Vite** · **Axios**

### 开发工具
**uv** (包管理器) · **Playwright** (浏览器自动化,可选)

### 项目结构
```
NewsCrawler/
├── news_crawler/              # 核心爬虫模块
│   ├── wechat_news/          # 微信公众号
│   ├── toutiao_news/         # 今日头条
│   ├── netease_news/         # 网易新闻
│   ├── sohu_news/            # 搜狐新闻
│   ├── tencent_news/         # 腾讯新闻
│   └── ...                   # 其他平台
│
├── news_extractor_core/       # 共享核心库
│   ├── adapters/             # 平台适配器
│   ├── services/             # 业务逻辑
│   └── models/               # 数据模型
│
├── news_extractor_backend/    # FastAPI 后端服务
│   ├── api/                  # API 路由
│   └── main.py               # 应用入口
│
├── news_extractor_mcp/        # MCP 服务器(AI Agent)
│   ├── server.py             # MCP 实现
│   └── README.md             # MCP 文档
│
├── news-extractor-ui/         # Web UI 应用
│   ├── backend/              # (旧版) FastAPI 后端
│   └── frontend/             # Vue 3 前端
│
├── video_crawler/             # 视频素材下载器
├── libs/                      # 工具库
├── data/                      # 输出数据目录
│
├── Dockerfile                 # 多阶段 Docker 构建
├── docker-compose.yml         # 服务编排配置
└── DOCKER_DEPLOYMENT.md       # Docker 部署指南
```

---

## ⚠️ 重要提醒

> **本项目仅供学习和研究使用,禁止用于商业用途**

**使用须知:**
- ✅ 仅用于个人学习、研究、教学目的
- ✅ 遵守目标网站的 robots.txt 和服务条款
- ✅ 控制请求频率,避免给服务器造成压力
- ❌ 不得用于非法用途或侵犯他人权益
- ❌ 不得进行大规模商业化爬取

**技术说明:**
- 部分平台可能有反爬机制,需适当调整策略
- 默认 Headers 可能过期,可使用 Playwright 自动获取最新 Cookie
- 网页结构变化可能导致解析失败,欢迎提交 Issue

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request!

**贡献方向:**
- 🐛 修复 Bug
- ✨ 添加新平台支持
- 📝 改进文档
- 🎨 优化 UI/UX
- ⚡ 性能优化

**提交流程:**
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目仅供学习和研究使用。使用本项目即表示您同意:
- 不将其用于商业目的
- 不进行大规模爬取
- 遵守相关法律法规和目标网站的使用条款

对于因使用本项目内容而引起的任何法律责任,本项目不承担责任。

---

## 🔗 相关资源

- [uv - Python 包管理器](https://github.com/astral-sh/uv)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
- [Playwright 文档](https://playwright.dev/)

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=NanmiCoder/NewsCrawler&type=Date)](https://star-history.com/#NanmiCoder/NewsCrawler&Date)

---

<div align="center">

**如果这个项目对你有帮助,请给个 ⭐ Star 支持一下!**

Made with ❤️ by [NanmiCoder](https://github.com/NanmiCoder)

</div>
