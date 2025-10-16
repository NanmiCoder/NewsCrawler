# NewsCrawlerCollection

English · [中文](README.md)

A multi-platform news and content crawler collection, supporting both command-line and Web UI usage modes.

![Web UI](static/images/03_webui_en.png)

## 🎯 Key Features

- **Multi-Platform Support** - 6+ mainstream news/content platforms (WeChat, Toutiao, Lenny, Naver, Detik, Quora)
- **Dual Usage Modes** - Supports both Python API calls and Web UI operations
- **Unified Data Format** - All platforms output standardized JSON format
- **Modern Tooling** - Uses uv package manager for lightning-fast dependency installation




## 📦 Supported Platforms

### News/Content Platforms
| Platform | URL Example | Status |
|----------|-------------|--------|
| WeChat Official Accounts | `mp.weixin.qq.com` | ✅ |
| Toutiao | `toutiao.com` | ✅ |
| Lenny's Newsletter | `lennysnewsletter.com` | ✅ |
| Naver Blog | `blog.naver.com` | ✅ |
| Detik News | `detik.com` | ✅ |
| Quora | `quora.com` | ✅ |

### Stock Video Platforms
- Pexels, Pixabay, Coverr, Mixkit

---

## 🚀 Quick Start

### 1. Environment Setup

**Install uv (Python Package Manager)**

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or use pip
pip install uv
```

**Install Project**

```bash
# Clone the repository
git clone https://github.com/NanmiCoder/NewsCrawlerCollection.git
cd NewsCrawlerCollection

```

### 2. Usage Methods

#### Method 1: Web UI (Recommended, Ready to Use 🎉)

**Start Backend Service**

```bash
cd news-extractor-ui/backend
uv sync          # Install backend dependencies
uv run run.py    # Start backend (port 8000)
```

**Start Frontend Service** (new terminal)

```bash
cd news-extractor-ui/frontend
npm install        # Install frontend dependencies
npm run dev        # Start frontend (port 3000)
```

**Access Application**

Open your browser and visit `http://localhost:3000` to extract news content through the visual interface.

#### Method 2: Python API Calls (Suitable for Automation Integration)

```python
from news_crawler.wechat_news import WeChatNewsCrawler
from news_crawler.toutiao_news import ToutiaoNewsCrawler

# WeChat Official Account
wechat_url = "https://mp.weixin.qq.com/s/xxxxxx"
crawler = WeChatNewsCrawler(wechat_url)
result = crawler.run()

# Toutiao
toutiao_url = "https://www.toutiao.com/article/xxxxxx"
crawler = ToutiaoNewsCrawler(toutiao_url)
result = crawler.run()
```

Run example code:
```bash
# View complete examples
cat call_example.py

# Run examples
uv run call_example.py
```

---

## 📦 Data Output Format

All crawlers output a unified JSON format, saved in the `data/` directory:

```json
{
  "title": "Article Title",
  "news_url": "Original URL",
  "news_id": "Article ID",
  "meta_info": {
    "author_name": "Author",
    "publish_time": "Publish Time"
  },
  "contents": [
    {"type": "text", "content": "Paragraph content", "desc": ""},
    {"type": "image", "content": "Image URL", "desc": ""}
  ],
  "texts": ["Plain text content..."],
  "images": ["Image URLs..."],
  "videos": ["Video URLs..."]
}
```

---

## 📁 Project Structure

```
NewsCrawlerCollection/
│
├── news_crawler/              # News crawler modules (Core)
│   ├── wechat_news/          # WeChat Official Accounts
│   ├── toutiao_news/         # Toutiao
│   ├── lennysnewsletter/     # Lenny's Newsletter
│   ├── naver_news/           # Naver Blog
│   ├── detik_news/           # Detik News
│   └── quora/                # Quora
│
├── news-extractor-ui/         # Web UI Application
│   ├── backend/              # FastAPI Backend
│   │   ├── app/
│   │   │   ├── api/          # API Routes
│   │   │   ├── adapters/     # Crawler Adapters
│   │   │   └── services/     # Business Logic
│   │   ├── pyproject.toml
│   │   └── run.py
│   │
│   └── frontend/             # Vue 3 Frontend
│       ├── src/
│       │   ├── components/   # UI Components
│       │   ├── services/     # API Services
│       │   └── types/        # TypeScript Types
│       ├── package.json
│       └── vite.config.ts
│
├── video_crawler/            # Video Downloader Modules
│   ├── pexel/               # Pexels
│   ├── pixabay/             # Pixabay
│   ├── cover_video/         # Coverr
│   └── mixkit_video/        # Mixkit
│
├── libs/                     # Utility Libraries
│   ├── playwright_driver.py # Browser Automation
│   └── drissionpage_driver.py
│
├── data/                     # Output Data Directory
├── call_example.py          # Usage Example Code
├── pyproject.toml           # Project Configuration (uv)
└── README.md
```

---

## 🔧 Technology Stack

### Backend
- **Python 3.8+**
- **FastAPI** - Modern web framework
- **Pydantic** - Data validation
- **curl_cffi / requests** - HTTP requests
- **parsel** - HTML parsing

### Frontend
- **Vue 3** - Progressive framework
- **TypeScript** - Type safety
- **Vite** - Build tool

### Tools
- **uv** - Lightning-fast Python package manager
- **Playwright** - Browser automation (optional)

---

## ⚠️ Important Notes

1. **Legal Compliance**
   - For educational and research purposes only, commercial use is prohibited
   - Comply with target websites' robots.txt and terms of service
   - Control request frequency to avoid server stress

2. **Cookie Management**
   - Default headers may expire; use Playwright to auto-fetch when issues occur
   - Recommend updating cookies regularly

3. **Data Usage**
   - Respect content copyrights; do not use for illegal purposes
   - Collected data should only be used for personal learning and research

---

## 📝 Disclaimer

**All content in this repository is for learning and reference purposes only. Commercial use is strictly prohibited.**

- No person or organization may use the content of this repository for illegal purposes or to infringe on the legitimate rights and interests of others
- The web scraping techniques involved in this repository are for learning and research only, and must not be used for large-scale crawling or other illegal activities on other platforms
- This repository assumes no responsibility for any legal liability arising from the use of its content
- By using the content of this repository, you agree to all terms and conditions of this disclaimer

---

## 🤝 Contributing

Issues and Pull Requests are welcome to improve the project!

## 📄 License

This project is for learning and research purposes only.

---

## 🔗 Related Links

- [uv - Python Package Manager](https://github.com/astral-sh/uv)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue 3 Documentation](https://vuejs.org/)
