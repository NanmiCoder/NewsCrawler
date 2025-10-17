<div align="center">

# 🌐 NewsCrawlerCollection

**Multi-Platform News & Content Crawler Suite**

An open-source crawler toolkit for developers & researchers with CLI invocation, Web UI, and unified JSON output

Supports 9+ mainstream platforms: WeChat, Toutiao, NetEase, Sohu, Tencent, Naver, Detik, Quora

[![GitHub stars](https://img.shields.io/github/stars/NanmiCoder/NewsCrawlerCollection?style=social)](https://github.com/NanmiCoder/NewsCrawlerCollection/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/NanmiCoder/NewsCrawlerCollection?style=social)](https://github.com/NanmiCoder/NewsCrawlerCollection/network/members)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Educational-green.svg)](LICENSE)

English · [中文](README.md)

</div>

---

![Web UI Interface](static/images/03_webui_en.png)

**Ready-to-use Web UI** - Auto-detect platform, real-time progress, JSON/Markdown export

---

## 🎯 Why NewsCrawlerCollection?

<div align="center">

| 🌍 Multi-Platform | 🎨 Dual Modes | 📦 Standardized | ⚡ Fast Setup |
|:---:|:---:|:---:|:---:|
| 9+ Platforms<br/>CN/EN/KR/ID | Python API<br/>+ Web UI | Unified JSON<br/>Easy Integration | uv Manager<br/>Lightning Fast |

</div>

**Key Features:**

- ✅ **Multi-Platform Support** - WeChat, Toutiao, NetEase, Sohu, Tencent, Lenny's Newsletter, Naver Blog, Detik News, Quora
- ✅ **Smart Extraction** - Auto-detect platform type, extract title, content, images, videos
- ✅ **Unified Output** - Standardized JSON format perfect for data analysis, storage, downstream processing
- ✅ **Flexible Usage** - Python API (for automation) + Web UI (visual, no-code)
- ✅ **Modular Design** - Decoupled crawlers, easy to extend or optimize
- ✅ **Lightweight & Efficient** - uv-managed dependencies, fast installation, stable runtime

---

## 🚀 Quick Start

### Method 1: Web UI (Recommended - Ready to Use)

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or: pip install uv

# 2. Clone repository
git clone https://github.com/NanmiCoder/NewsCrawlerCollection.git
cd NewsCrawlerCollection

# 3. Start backend
cd news-extractor-ui/backend
uv sync && uv run run.py

# 4. Start frontend (new terminal)
cd news-extractor-ui/frontend
npm install && npm run dev

# 5. Visit http://localhost:3000
```

**Web UI Features:**
- 🎯 Paste URL, auto-detect platform type
- 📊 Real-time extraction progress
- 📄 JSON / Markdown dual-format export
- 🖼️ Content preview & one-click download

---

### Method 2: Python API (For Automation)

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
NewsCrawlerCollection/
├── news_crawler/              # Core crawler modules
│   ├── wechat_news/          # WeChat
│   ├── toutiao_news/         # Toutiao
│   ├── netease_news/         # NetEase
│   ├── sohu_news/            # Sohu
│   ├── tencent_news/         # Tencent
│   └── ...                   # Other platforms
├── news-extractor-ui/        # Web UI application
│   ├── backend/              # FastAPI backend
│   └── frontend/             # Vue 3 frontend
├── video_crawler/            # Video downloaders
├── libs/                     # Utility libraries
└── data/                     # Output directory
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

[![Star History Chart](https://api.star-history.com/svg?repos=NanmiCoder/NewsCrawlerCollection&type=Date)](https://star-history.com/#NanmiCoder/NewsCrawlerCollection&Date)

---

<div align="center">

**If this project helps you, please give us a ⭐ Star!**

Made with ❤️ by [NanmiCoder](https://github.com/NanmiCoder)

</div>
