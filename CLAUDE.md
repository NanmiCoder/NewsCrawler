# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NewsCrawlerCollection is a multi-platform news and content crawler collection designed for educational purposes only. It supports:
- **News Crawlers**: 6+ platforms (WeChat, Toutiao, Lenny's Newsletter, Naver Blog, Detik News, Quora)
- **Video Downloaders**: Stock media platforms (Pexels, Pixabay, Coverr, Mixkit)
- **Web UI**: Modern FastAPI + Vue 3 interface for easy extraction

**Important**: This codebase is for educational and research purposes only. Do not use for commercial purposes or large-scale crawling.

## Project Structure (Updated)

```
NewsCrawlerCollection/
├── news_crawler/              # Consolidated crawler modules (NEW)
│   ├── wechat_news/          # WeChat crawler
│   ├── toutiao_news/         # Toutiao crawler
│   ├── lennysnewsletter/     # Lenny's Newsletter
│   ├── naver_news/           # Naver Blog
│   ├── detik_news/           # Detik News
│   └── quora/                # Quora
│
├── news-extractor-ui/        # Web UI Application (NEW)
│   ├── backend/              # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/          # API routes
│   │   │   ├── adapters/     # Crawler adapters
│   │   │   ├── services/     # Business logic
│   │   │   └── main.py
│   │   ├── pyproject.toml
│   │   └── run.py
│   │
│   └── frontend/             # Vue 3 frontend
│       ├── src/
│       │   ├── components/   # Vue components
│       │   ├── services/     # API services
│       │   ├── types/        # TypeScript types
│       │   └── App.vue
│       ├── package.json
│       └── vite.config.ts
│
├── video_crawler/            # Video downloader modules
│   ├── pexel/
│   ├── pixabay/
│   ├── cover_video/
│   └── mixkit_video/
│
├── libs/                     # Shared utilities
│   ├── playwright_driver.py
│   ├── drissionpage_driver.py
│   └── tools.py
│
├── data/                     # Output directory
├── call_example.py          # CLI usage examples
├── pyproject.toml           # Root project config (uv)
└── uv.lock                  # Dependency lock file
```

## Commands

### Environment Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or: pip install uv

# Sync root project dependencies
uv sync
```

### Web UI Setup and Usage

**Backend (FastAPI):**
```bash
cd news-extractor-ui/backend
uv sync              # Install backend dependencies
uv run run.py        # Start backend on port 8000
```

**Frontend (Vue 3):**
```bash
cd news-extractor-ui/frontend
npm install          # Install frontend dependencies
npm run dev          # Start frontend on port 3000
npm run build        # Build for production
```

**Access:** Open browser to `http://localhost:3000`

### Python API Usage

```bash
# Run CLI examples
uv run call_example.py

# Direct module execution
uv run -m news_crawler.wechat_news.wechat_news
uv run -m news_crawler.toutiao_news.toutaio_news
```

### Key uv Commands

```bash
# Run script (no venv activation needed)
uv run script.py

# Add/remove dependencies
uv add package-name
uv remove package-name

# Update dependencies
uv sync --upgrade
```

## Architecture

### Web UI Architecture (NEW)

The Web UI provides a modern interface for news extraction:

**Backend (FastAPI):**
- **API Layer** (`app/api/`): RESTful endpoints
  - `POST /api/extract`: Main extraction endpoint
- **Adapter Layer** (`app/adapters/`): Wraps crawler modules
  - `WeChatAdapter`, `ToutiaoAdapter`, etc.
  - Provides unified interface for different platforms
- **Service Layer** (`app/services/`):
  - `detector.py`: Auto-detects platform from URL
  - `extractor.py`: Orchestrates extraction process
  - `markdown_converter.py`: Converts JSON to Markdown

**Frontend (Vue 3 + TypeScript):**
- **Components**:
  - `PlatformSelector.vue`: Platform selection cards
  - `UrlInputNew.vue`: URL input with validation
  - `ExtractProgress.vue`: Real-time progress display
  - `ResultViewerNew.vue`: Multi-tab result viewer (JSON/Markdown/Preview)
- **Services**:
  - `api.ts`: Axios-based API client
- **Types**:
  - `index.ts`: TypeScript interfaces for API responses

**Key Features:**
- Auto-detect platform from URL patterns
- Real-time extraction progress
- Dual-format output (JSON + Markdown)
- Responsive design with modern UI
- Platform-specific logo display

### News Crawler Core Pattern

All crawlers follow a consistent architecture:

1. **RequestHeaders** (Pydantic): User-Agent and Cookie management
2. **ContentType** (Enum): TEXT, IMAGE, VIDEO
3. **ContentItem** (Pydantic): Structured content with type/content/desc
4. **NewsMetaInfo** (Pydantic): Author, publish time, etc.
5. **NewsItem** (Pydantic): Complete article data model
6. **Crawler Class**: Main implementation
   - `__init__(url, save_path, headers)`
   - `fetch_content()`: HTTP with retry
   - `parse_html_to_news_meta()`: Extract metadata
   - `parse_html_to_news_content()`: Extract content
   - `save_as_json()`: Save to data/
   - `run()`: Main entry point

### Platform-Specific Implementations

#### WeChat (`news_crawler/wechat_news/`)
- **URL**: `https://mp.weixin.qq.com/s/{id}`
- **Special**: Supports both traditional and SSR-rendered pages
  - Traditional: Parse from `#js_content`
  - SSR (XHS-style): Parse `window.__QMTPL_SSR_DATA__`
- **HTTP**: Uses `curl_cffi` with Chrome impersonation
- **Parser**: `WechatContentParser` class handles nested content
- **Features**: List detection, paragraph structure preservation

#### Toutiao (`news_crawler/toutiao_news/`)
- **URL**: `https://www.toutiao.com/article/{id}/`
- **Parser**: parsel with XPath
- **Simple**: article/p/img/video extraction

#### Detik (`news_crawler/detik_news/`)
- **URL**: `https://news.detik.com/internasional/d-{id}/...`
- **Parser**: `.detail__body-text` extraction
- **Cover**: Extracts cover media from `.detail__media`

### Import Changes (Important!)

**OLD (before restructuring):**
```python
from wechat_news import WeChatNewsCrawler
from toutiao_news import ToutiaoNewsCrawler
```

**NEW (current structure):**
```python
from news_crawler.wechat_news import WeChatNewsCrawler
from news_crawler.toutiao_news import ToutiaoNewsCrawler
```

All crawler imports now go through the `news_crawler` package.

## Data Structure

All crawlers output JSON to `data/` directory:

```json
{
  "title": "string",
  "news_url": "string",
  "news_id": "string",
  "meta_info": {
    "author_name": "string",
    "author_url": "string",
    "publish_time": "string"
  },
  "contents": [
    {"type": "text|image|video", "content": "...", "desc": "..."}
  ],
  "texts": ["array of text strings"],
  "images": ["array of image URLs"],
  "videos": ["array of video URLs"]
}
```

## Web UI API

### POST /api/extract

Extract news content from URL.

**Request:**
```json
{
  "url": "https://mp.weixin.qq.com/s/xxxxx",
  "output_format": "markdown"  // or "json"
}
```

**Response:**
```json
{
  "status": "success",
  "data": { /* NewsItem JSON */ },
  "platform": "wechat",
  "extracted_at": "2024-10-15T10:30:00",
  "markdown": "# Title\n\nContent..."
}
```

**API Documentation:** Visit `http://localhost:8000/docs` for Swagger UI

## Development Patterns

### Adding a New Platform to Web UI

1. **Create Adapter** (`backend/app/adapters/`):
   ```python
   from news_crawler.platform_news import PlatformNewsCrawler

   class PlatformAdapter:
       def extract(self, url: str) -> NewsItem:
           crawler = PlatformNewsCrawler(url)
           return crawler.run()
   ```

2. **Register in Detector** (`backend/app/services/detector.py`):
   ```python
   URL_PATTERNS = {
       'platform': r'platform\.com',
   }
   ```

3. **Register in Extractor** (`backend/app/services/extractor.py`):
   ```python
   ADAPTERS = {
       'platform': PlatformAdapter(),
   }
   ```

4. **Add Frontend Logo** (`frontend/public/logos/platform.png`)

5. **Update Platform Selector** (`frontend/src/components/PlatformSelector.vue`):
   ```typescript
   {
     id: 'platform',
     name: 'Platform Name',
     icon: '/logos/platform.png',
     description: 'Description'
   }
   ```

### Testing a Crawler

Each crawler has test section in `__main__`:
```bash
uv run -m news_crawler.platform_news.platform_news
```

### Adding New Dependencies

**Backend:**
```bash
cd news-extractor-ui/backend
uv add package-name
```

**Frontend:**
```bash
cd news-extractor-ui/frontend
npm install package-name
```

## Technology Stack

### Backend
- **Python 3.8+**
- **uv** - Package manager
- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **curl_cffi / requests** - HTTP
- **parsel** - HTML parsing
- **tenacity** - Retry logic

### Frontend
- **Vue 3** - Framework (Composition API)
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Axios** - HTTP client

### Tools
- **Playwright** (optional) - Browser automation for header extraction

## Key Implementation Details

### Retry Strategy
- Uses `tenacity` with `@retry` decorator
- 3 attempts, 1 second wait between retries
- Applied to both `fetch_content()` and `run()`

### Headers Management
- Default headers work without authentication
- Optional: Use `playwright_driver.get_headers()` for fresh cookies
- Cookies may expire, use auto-extraction when needed

### WeChat SSR Detection
Check `window.__QMTPL_SSR_DATA__` in HTML:
- Present → `parse_ssr_content()`
- Absent → `parse_html_to_news_content()`

### Content Extraction Philosophy
- Preserve structure (paragraphs, lists)
- Duplicate storage: structured `contents` + flattened `texts/images/videos`
- Handle nested media tags

## Git Workflow

### Ignored Files
```
# Python
__pycache__/
*.pyc
.venv/
data/

# Frontend
news-extractor-ui/frontend/node_modules/
news-extractor-ui/frontend/dist/
news-extractor-ui/frontend/package-lock.json

# Backend
news-extractor-ui/backend/.venv/
news-extractor-ui/backend/uv.lock

# System
.DS_Store
```

### Committing Changes
```bash
git status
git add .
git commit -m "description"
git push origin main
```

## Disclaimer

This repository is for educational and research purposes only. Users must:
- Not use for commercial purposes
- Not perform large-scale crawling
- Respect target websites' robots.txt and terms of service
- Understand that responsibility for misuse lies with the user

## Recent Changes

### 2024-10-17
- Restructured crawler modules into `news_crawler/` directory
- Added comprehensive Web UI (FastAPI + Vue 3)
- Implemented platform auto-detection
- Added Markdown export functionality
- Unified logo display across UI
- Updated README with dual-mode usage instructions
- Fixed UV command formats (`uv run script.py` not `uv run python script.py`)
