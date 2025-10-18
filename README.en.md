<div align="center">

# 🌐 NewsCrawler

**Multi-Platform News & Content Crawler Suite**

An open-source crawler toolkit for developers & researchers with CLI invocation, Web UI, and unified JSON output, MCP support

Supports 9+ mainstream platforms: WeChat, Toutiao, NetEase, Sohu, Tencent, Naver, Detik, Quora

[![GitHub stars](https://img.shields.io/github/stars/NanmiCoder/NewsCrawler?style=social)](https://github.com/NanmiCoder/NewsCrawler/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/NanmiCoder/NewsCrawler?style=social)](https://github.com/NanmiCoder/NewsCrawler/network/members)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Educational-green.svg)](LICENSE)

English · [中文](README.md)

</div>

---

![Web UI Interface](static/images/03_webui_en.png)

**Ready-to-use Web UI** - Auto-detect platform, real-time progress, JSON/Markdown export

---

## 🎯 Why NewsCrawler?

<div align="center">

| 🌍 Multi-Platform | 🎨 Dual Modes | 📦 Standardized | ⚡ Fast Setup |
|:---:|:---:|:---:|:---:|
| 9+ Platforms<br/>CN/EN/KR/ID | Python API<br/>+ Web UI | Unified JSON<br/>Easy Integration | uv Manager<br/>Lightning Fast |

</div>

**Key Features:**

- ✅ **Multi-Platform Support** - WeChat, Toutiao, NetEase, Sohu, Tencent, Lenny's Newsletter, Naver Blog, Detik News, Quora
- ✅ **Smart Extraction** - Auto-detect platform type, extract title, content, images, videos
- ✅ **Unified Output** - Standardized JSON format perfect for data analysis, storage, downstream processing
- ✅ **Flexible Usage** - Python API (for automation) + Web UI (visual, no-code) + MCP Server (AI Agents)
- ✅ **One-Click Deployment** - Docker Compose orchestrates all services (Backend + Frontend + MCP)
- ✅ **AI Agent Integration** - MCP (Model Context Protocol) support for Claude Desktop and AI tools
- ✅ **Modular Design** - Decoupled crawlers, easy to extend or optimize
- ✅ **Lightweight & Efficient** - uv-managed dependencies, fast installation, stable runtime

---

## 🚀 Quick Start

### Method 1: Docker Compose (⭐ Recommended - One-Click Deployment)

```bash
# 1. Install Docker & Docker Compose
# Visit: https://docs.docker.com/get-docker/

# 2. Clone repository
git clone https://github.com/NanmiCoder/NewsCrawler.git
cd NewsCrawler

# 3. One-click start all services (Backend + Frontend + MCP)
docker compose up -d

# 4. Access services
# - Frontend UI: http://localhost:3000
# - Backend API: http://localhost:8000/docs
# - MCP Server: http://localhost:8765/health
```

**What's included:**
- ✅ **Backend Service** (FastAPI) - News extraction API
- ✅ **Frontend Service** (Vue 3 + Nginx) - Web UI interface
- ✅ **MCP Service** - AI Agent tools for Claude Desktop
- ✅ **Auto Health Checks** - Ensures all services are running
- ✅ **Data Persistence** - Extracted news saved in `./data/`

**Docker Management:**
```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after code update
docker compose up -d --build
```

📖 **Full Documentation**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

---

### Method 2: Web UI (Manual Setup)

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or: pip install uv

# 2. Clone repository
git clone https://github.com/NanmiCoder/NewsCrawler.git
cd NewsCrawler

# 3. Install all dependencies (uv workspace mode)
uv sync

# 4. Start backend (from project root)
uv run news-extractor-backend --host 0.0.0.0 --port 8000

# 5. Start frontend (new terminal)
cd news-extractor-ui/frontend
npm install && npm run dev

# 6. Visit http://localhost:3000
```

**Web UI Features:**
- 🎯 Paste URL, auto-detect platform type
- 📊 Real-time extraction progress
- 📄 JSON / Markdown dual-format export
- 🖼️ Content preview & one-click download

📖 **Detailed Deployment Guide**: [MANUAL_DEPLOYMENT.md](MANUAL_DEPLOYMENT.md)

---

### Method 3: Python API (For Automation)

```python
from news_crawler.wechat_news import WeChatNewsCrawler
from news_crawler.toutiao_news import ToutiaoNewsCrawler

# WeChat Official Account
wechat_url = "https://mp.weixin.qq.com/s/xxxxxx"
crawler = WeChatNewsCrawler(wechat_url)
result = crawler.run()  # Auto-save to data/ directory

# Toutiao
toutiao_url = "https://www.toutiao.com/article/xxxxxx"
crawler = ToutiaoNewsCrawler(toutiao_url)
result = crawler.run()

print(result)  # Returns JSON format data
```

**Run Examples:**
```bash
uv run call_example.py  # View complete examples
```

---

### Method 4: MCP Server (AI Agent Integration)

**What is MCP?**
[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is a standard for connecting AI assistants (like Claude Desktop) to external tools and data sources.

**Use Cases:**
- 🤖 Let Claude extract news directly through conversation
- 🔄 Batch process multiple URLs via AI commands
- 📊 AI-powered content analysis workflows
- 🚀 Build custom AI agents with news extraction capabilities

**Quick Setup:**

```bash
# 1. Start MCP Server (Recommended: Docker)
docker compose up -d mcp

# 2. Or start manually (from project root)
# First install dependencies
uv sync

# Start MCP server
uv run news-extractor-mcp --host 0.0.0.0 --port 8765

# 3. MCP Server running at: http://localhost:8765/mcp
```

**AI Tool Configuration (Streamable HTTP):**

<details>
<summary><b>Cursor</b> (Click to expand)</summary>

Config file: `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project-level)

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
<summary><b>Windsurf</b> (Click to expand)</summary>

Config file: `~/.codeium/windsurf/mcp_server_config.json`

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
<summary><b>Trae</b> (Click to expand)</summary>

Settings → Tools → MCP Servers → Add Server

```json
{
  "name": "newscrawler",
  "url": "http://127.0.0.1:8765/mcp"
}
```
</details>

<details>
<summary><b>Claude Desktop</b> (Click to expand)</summary>

Config file location:
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
<summary><b>Other MCP-Compatible Tools</b> (Click to expand)</summary>

All MCP clients supporting Streamable HTTP transport can use:

```json
{
  "mcpServers": {
    "newscrawler": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

**Note**: If using Docker and your AI tool runs outside Docker, replace `127.0.0.1` with host IP or `host.docker.internal`
</details>

**Available MCP Tools:**
- `extract_news` - Extract single news article (JSON or Markdown)
- `batch_extract_news` - Extract multiple URLs in batch
- `detect_news_platform` - Identify platform type from URL
- `list_supported_platforms` - Show all supported platforms

**Example Conversation with Claude:**
```
You: "Extract this WeChat article: https://mp.weixin.qq.com/s/xxxxx"
Claude: [Uses extract_news tool] "I've extracted the article..."

You: "Extract these 3 URLs in Markdown format: [url1, url2, url3]"
Claude: [Uses batch_extract_news] "Here's the combined Markdown..."
```

📖 **Full MCP Documentation**: [news_extractor_mcp/README.md](news_extractor_mcp/README.md)

---

## 📦 Supported Platforms

### News / Content Platforms

| Platform | URL Example | Language | Features |
|----------|-------------|----------|----------|
| WeChat Official Accounts | `mp.weixin.qq.com` | Chinese | Articles & videos |
| Toutiao | `toutiao.com` | Chinese | Rich media, videos |
| NetEase News | `163.com` | Chinese | Image galleries |
| Sohu News | `sohu.com` | Chinese | Multimedia content |
| Tencent News | `news.qq.com` | Chinese | Video news |
| Lenny's Newsletter | `lennysnewsletter.com` | English | Long-form content |
| Naver Blog | `blog.naver.com` | Korean | Blog platform |
| Detik News | `detik.com` | Indonesian | Southeast Asia news |
| Quora | `quora.com` | English | Q&A content |

### Stock Video Platforms
**Pexels** · **Pixabay** · **Coverr** · **Mixkit** - High-quality free video downloads

---

## 💡 Use Cases

```
📰 Multi-source news aggregation / Public opinion monitoring
📊 Media content analysis, data mining, recommendation systems
🔬 Academic research / Data science - Cross-platform extraction
🎓 Educational projects / Personal learning - Crawler framework
🤖 AI training data collection / Content quality analysis
```

---

## 📊 Data Output Format

All crawlers output unified JSON format, saved in `data/` directory:

```json
{
  "title": "Article Title",
  "news_url": "Original URL",
  "news_id": "Article ID",
  "meta_info": {
    "author_name": "Author Name",
    "author_url": "Author Homepage",
    "publish_time": "2024-10-15 10:30:00"
  },
  "contents": [
    {"type": "text", "content": "Paragraph text", "desc": ""},
    {"type": "image", "content": "https://example.com/image.jpg", "desc": "Image desc"},
    {"type": "video", "content": "https://example.com/video.mp4", "desc": "Video desc"}
  ],
  "texts": ["Paragraph 1", "Paragraph 2"],
  "images": ["Image URL 1", "Image URL 2"],
  "videos": ["Video URL 1"]
}
```

**Field Descriptions:**
- `contents` - Structured content preserving order and type (text/image/video)
- `texts/images/videos` - Flattened lists for quick access to specific content types
- `meta_info` - Article metadata (author, publish time, etc.)

---

## 🔧 Technology Stack

### Backend
**Python 3.8+** · **FastAPI** · **Pydantic** · **curl_cffi** · **parsel** · **tenacity**

### Frontend
**Vue 3** · **TypeScript** · **Vite** · **Axios**

### Dev Tools
**uv** (package manager) · **Playwright** (browser automation, optional)

### Project Structure
```
NewsCrawler/
├── news_crawler/              # Core crawler modules
│   ├── wechat_news/          # WeChat
│   ├── toutiao_news/         # Toutiao
│   ├── netease_news/         # NetEase
│   ├── sohu_news/            # Sohu
│   ├── tencent_news/         # Tencent
│   └── ...                   # Other platforms
│
├── news_extractor_core/       # Shared core library (uv workspace member)
│   ├── adapters/             # Platform adapters
│   ├── services/             # Business logic
│   └── models/               # Data models
│
├── news_extractor_backend/    # FastAPI backend service (uv workspace member)
│   ├── api/                  # API routes
│   ├── main.py               # Application entry
│   └── cli.py                # CLI entry point
│
├── news_extractor_mcp/        # MCP server (uv workspace member)
│   ├── server.py             # MCP implementation
│   └── README.md             # MCP documentation
│
├── news-extractor-ui/         # Web UI application
│   └── frontend/             # Vue 3 frontend
│
├── video_crawler/             # Video downloaders
├── libs/                      # Utility libraries
├── data/                      # Output directory
│
├── pyproject.toml             # uv workspace root config
├── uv.lock                    # Dependency lock file
├── Dockerfile                 # Multi-stage Docker build
├── docker-compose.yml         # Service orchestration
├── DOCKER_DEPLOYMENT.md       # Docker deployment guide
└── MANUAL_DEPLOYMENT.md       # Manual deployment guide
```

---

## ⚠️ Important Notice

> **This project is for educational and research purposes only. Commercial use is prohibited.**

**Usage Guidelines:**
- ✅ Personal learning, research, educational purposes only
- ✅ Comply with target websites' robots.txt and terms of service
- ✅ Control request frequency to avoid server stress
- ❌ Do not use for illegal purposes or infringe on others' rights
- ❌ No large-scale commercial crawling

**Technical Notes:**
- Some platforms may have anti-scraping mechanisms; adjust strategies accordingly
- Default headers may expire; use Playwright to auto-fetch fresh cookies
- Web page structure changes may cause parsing failures; feel free to submit issues

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

**Contribution Areas:**
- 🐛 Fix bugs
- ✨ Add new platform support
- 📝 Improve documentation
- 🎨 Optimize UI/UX
- ⚡ Performance optimization

**Submission Process:**
1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is for learning and research purposes only. By using this project, you agree to:
- Not use it for commercial purposes
- Not perform large-scale crawling
- Comply with relevant laws and target websites' terms of service

This project assumes no responsibility for any legal liability arising from its use.

---

## 🔗 Resources

- [uv - Python Package Manager](https://github.com/astral-sh/uv)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Playwright Documentation](https://playwright.dev/)

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=NanmiCoder/NewsCrawler&type=Date)](https://star-history.com/#NanmiCoder/NewsCrawler&Date)

---

<div align="center">

**If this project helps you, please give us a ⭐ Star!**

Made with ❤️ by [NanmiCoder](https://github.com/NanmiCoder)

</div>
