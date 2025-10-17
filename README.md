<div align="center">

# 🌐 NewsCrawlerCollection

**多平台新闻 & 内容爬虫集合**

一个面向开发者和研究者的开源爬虫工具箱,提供命令行调用、可视化 Web UI、统一 JSON 输出

支持微信公众号、今日头条、网易新闻、搜狐、腾讯、Naver、Detik、Quora 等 9+ 主流平台

[![GitHub stars](https://img.shields.io/github/stars/NanmiCoder/NewsCrawlerCollection?style=social)](https://github.com/NanmiCoder/NewsCrawlerCollection/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/NanmiCoder/NewsCrawlerCollection?style=social)](https://github.com/NanmiCoder/NewsCrawlerCollection/network/members)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Educational-green.svg)](LICENSE)

[English](README.en.md) · 中文

</div>

---

![Web UI 界面](static/images/01_webui.png)

**开箱即用的 Web UI** - 自动识别平台、实时提取进度、JSON/Markdown 双格式导出

---

## 🎯 为什么选择 NewsCrawlerCollection?

<div align="center">

| 🌍 多平台支持 | 🎨 双模式使用 | 📦 标准化输出 | ⚡ 快速部署 |
|:---:|:---:|:---:|:---:|
| 9+ 主流平台<br/>覆盖中英韩印尼 | Python API<br/>+ Web UI | 统一 JSON 格式<br/>易于集成 | uv 包管理器<br/>极速安装 |

</div>

**核心特性:**

- ✅ **全平台覆盖** - 支持微信公众号、今日头条、网易、搜狐、腾讯、Lenny's Newsletter、Naver Blog、Detik News、Quora
- ✅ **智能提取** - 自动识别平台类型,提取标题、正文、图片、视频等多媒体内容
- ✅ **统一输出** - 所有平台输出标准化 JSON 格式,完美适配数据分析、入库、下游处理
- ✅ **灵活使用** - 支持 Python 代码调用(适合自动化)和 Web UI 操作(可视化,零代码)
- ✅ **模块化设计** - 各平台爬虫解耦,易于扩展新平台或优化现有实现
- ✅ **轻量高效** - 使用 uv 管理依赖,安装快速,运行稳定

---

## 🚀 快速开始

### 方式一:Web UI (推荐 - 开箱即用)

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# 或: pip install uv

# 2. 克隆项目
git clone https://github.com/NanmiCoder/NewsCrawlerCollection.git
cd NewsCrawlerCollection

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

### 方式二:Python API (适合自动化集成)

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
NewsCrawlerCollection/
├── news_crawler/              # 核心爬虫模块
│   ├── wechat_news/          # 微信公众号
│   ├── toutiao_news/         # 今日头条
│   ├── netease_news/         # 网易新闻
│   ├── sohu_news/            # 搜狐新闻
│   ├── tencent_news/         # 腾讯新闻
│   └── ...                   # 其他平台
├── news-extractor-ui/        # Web UI 应用
│   ├── backend/              # FastAPI 后端
│   └── frontend/             # Vue 3 前端
├── video_crawler/            # 视频素材下载器
├── libs/                     # 工具库
└── data/                     # 输出数据目录
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

[![Star History Chart](https://api.star-history.com/svg?repos=NanmiCoder/NewsCrawlerCollection&type=Date)](https://star-history.com/#NanmiCoder/NewsCrawlerCollection&Date)

---

<div align="center">

**如果这个项目对你有帮助,请给个 ⭐ Star 支持一下!**

Made with ❤️ by [NanmiCoder](https://github.com/NanmiCoder)

</div>
