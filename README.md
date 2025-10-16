# NewsCrawlerCollection

[English](README.en.md) · 中文

一个多平台新闻内容爬取工具集，支持命令行调用和 Web UI 两种使用方式。

![Web UI](static/images/01_webui.png)

## 🎯 项目特点

- **多平台支持** - 7+ 主流新闻/内容平台（微信、头条、网易、Lenny、Naver、Detik、Quora）
- **双模式使用** - 支持 Python 代码调用 和 Web UI 操作
- **统一数据格式** - 所有平台输出标准化的 JSON 格式
- **现代化工具** - 使用 uv 包管理器，极速安装依赖




## 📦 支持的平台

### 新闻/内容平台
| 平台 | URL 示例 | 状态 |
|------|---------|------|
| 微信公众号 | `mp.weixin.qq.com` | ✅ |
| 今日头条 | `toutiao.com` | ✅ |
| 网易新闻 | `163.com` | ✅ |
| Lenny's Newsletter | `lennysnewsletter.com` | ✅ |
| Naver Blog | `blog.naver.com` | ✅ |
| Detik News | `detik.com` | ✅ |
| Quora | `quora.com` | ✅ |

### 视频素材平台
- Pexels、Pixabay、Coverr、Mixkit

---

## 🚀 快速开始

### 1. 环境准备

**安装 uv（Python 包管理器）**

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

**安装项目**

```bash
# 克隆项目
git clone https://github.com/NanmiCoder/NewsCrawlerCollection.git
cd NewsCrawlerCollection

```

### 2. 使用方式

#### 方式一：Web UI 操作（推荐，开箱即用 🎉）

**启动后端服务**

```bash
cd news-extractor-ui/backend
uv sync          # 安装后端依赖
uv run run.py    # 启动后端（端口 8000）
```

**启动前端服务**（新终端）

```bash
cd news-extractor-ui/frontend
npm install        # 安装前端依赖
npm run dev        # 启动前端（端口 3000）
```

**访问应用**

打开浏览器访问 `http://localhost:3000`，即可通过可视化界面提取新闻内容。

#### 方式二：Python 代码调用（适合自动化集成）

```python
from news_crawler.wechat_news import WeChatNewsCrawler
from news_crawler.toutiao_news import ToutiaoNewsCrawler

# 微信公众号
wechat_url = "https://mp.weixin.qq.com/s/xxxxxx"
crawler = WeChatNewsCrawler(wechat_url)
result = crawler.run()

# 今日头条
toutiao_url = "https://www.toutiao.com/article/xxxxxx"
crawler = ToutiaoNewsCrawler(toutiao_url)
result = crawler.run()
```

运行示例代码：
```bash
# 查看完整示例
cat call_example.py

# 运行示例
uv run call_example.py
```

---

## 📦 数据输出格式

所有爬虫输出统一的 JSON 格式，保存在 `data/` 目录：

```json
{
  "title": "文章标题",
  "news_url": "原文链接",
  "news_id": "文章ID",
  "meta_info": {
    "author_name": "作者",
    "publish_time": "发布时间"
  },
  "contents": [
    {"type": "text", "content": "段落内容", "desc": ""},
    {"type": "image", "content": "图片URL", "desc": ""}
  ],
  "texts": ["纯文本内容..."],
  "images": ["图片URL..."],
  "videos": ["视频URL..."]
}
```

---

## 📁 项目结构

```
NewsCrawlerCollection/
│
├── news_crawler/              # 新闻爬虫模块（核心）
│   ├── wechat_news/          # 微信公众号
│   ├── toutiao_news/         # 今日头条
│   ├── netease_news/         # 网易新闻
│   ├── lennysnewsletter/     # Lenny's Newsletter
│   ├── naver_news/           # Naver Blog
│   ├── detik_news/           # Detik News
│   └── quora/                # Quora
│
├── news-extractor-ui/         # Web UI 应用
│   ├── backend/              # FastAPI 后端
│   │   ├── app/
│   │   │   ├── api/          # API 路由
│   │   │   ├── adapters/     # 爬虫适配器
│   │   │   └── services/     # 业务逻辑
│   │   ├── pyproject.toml
│   │   └── run.py
│   │
│   └── frontend/             # Vue 3 前端
│       ├── src/
│       │   ├── components/   # UI 组件
│       │   ├── services/     # API 服务
│       │   └── types/        # TypeScript 类型
│       ├── package.json
│       └── vite.config.ts
│
├── video_crawler/            # 视频素材爬虫
│   ├── pexel/               # Pexels
│   ├── pixabay/             # Pixabay
│   ├── cover_video/         # Coverr
│   └── mixkit_video/        # Mixkit
│
├── libs/                     # 工具库
│   ├── playwright_driver.py # 自动化浏览器
│   └── drissionpage_driver.py
│
├── data/                     # 输出数据目录
├── call_example.py          # 使用示例代码
├── pyproject.toml           # 项目配置（uv）
└── README.md
```

---

## 🔧 技术栈

### 后端
- **Python 3.8+**
- **FastAPI** - 现代化 Web 框架
- **Pydantic** - 数据验证
- **curl_cffi / requests** - HTTP 请求
- **parsel** - HTML 解析

### 前端
- **Vue 3** - 渐进式框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具

### 工具
- **uv** - 极速 Python 包管理器
- **Playwright** - 浏览器自动化（可选）

---

## ⚠️ 注意事项

1. **合法合规**
   - 仅供学习研究使用，禁止商业用途
   - 遵守目标网站的 robots.txt 和服务条款
   - 控制请求频率，避免给服务器造成压力

2. **Cookie 管理**
   - 默认 Headers 可能过期，遇到问题时使用 Playwright 自动获取
   - 建议定期更新 Cookie

3. **数据使用**
   - 尊重内容版权，不得用于非法用途
   - 采集数据仅用于个人学习研究

---

## 📝 免责声明

**本仓库的所有内容仅供学习和参考之用，禁止用于商业用途。**

- 任何人或组织不得将本仓库的内容用于非法用途或侵犯他人合法权益
- 本仓库所涉及的爬虫技术仅用于学习和研究，不得用于对其他平台进行大规模爬虫或其他非法行为
- 对于因使用本仓库内容而引起的任何法律责任，本仓库不承担任何责任
- 使用本仓库的内容即表示您同意本免责声明的所有条款和条件

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 📄 许可证

本项目仅供学习和研究使用。

---

## 🔗 相关链接

- [uv - Python 包管理器](https://github.com/astral-sh/uv)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
