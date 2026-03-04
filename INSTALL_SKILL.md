# 安装 News Extractor 技能

本文档指导 AI 助手（如 Claude Code）将 `news-extractor` 技能安装到目标项目中。

## 技能概述

**news-extractor** 是一个独立可迁移的新闻内容提取技能，支持从 12 个主流新闻平台提取文章内容，输出 JSON 和 Markdown 格式。

### 支持平台

| 分类 | 平台 | ID |
|------|------|----|
| 中文 | 微信公众号 | wechat |
| 中文 | 今日头条 | toutiao |
| 中文 | 网易新闻 | netease |
| 中文 | 搜狐新闻 | sohu |
| 中文 | 腾讯新闻 | tencent |
| 国际 | BBC News | bbc |
| 国际 | CNN News | cnn |
| 国际 | Twitter/X | twitter |
| 国际 | Lenny's Newsletter | lenny |
| 国际 | Naver Blog | naver |
| 国际 | Detik News | detik |
| 国际 | Quora | quora |

## 安装步骤

### 1. 克隆技能源仓库

```bash
git clone https://github.com/NanmiCoder/NewsCrawler.git
```

### 2. 复制技能目录到目标项目

将克隆下来的仓库中 `.claude/skills/news-extractor/` 目录复制到你的目标项目：

```bash
# 确保目标项目的技能目录存在
mkdir -p <目标项目>/.claude/skills/

# 从克隆的仓库中复制技能
cp -r NewsCrawler/.claude/skills/news-extractor <目标项目>/.claude/skills/news-extractor
```

### 3. 安装依赖

> **前置条件**: 需要安装 [uv](https://github.com/astral-sh/uv) 包管理器。
> 安装方式: `curl -LsSf https://astral.sh/uv/install.sh | sh`

```bash
cd <目标项目>/.claude/skills/news-extractor
uv sync
```

### 4. 验证安装

```bash
# 列出支持的平台
uv run scripts/extract_news.py --list-platforms

# 测试提取（使用任意支持平台的 URL）
uv run scripts/extract_news.py "https://www.bbc.com/news/articles/c797qlx93j0o"
```

### 5. 清理（可选）

安装完成后可删除克隆的源仓库：

```bash
rm -rf NewsCrawler
```

## 使用方式

所有命令在 `.claude/skills/news-extractor/` 目录下执行：

```bash
# 基本提取（自动检测平台，输出 JSON + Markdown）
uv run scripts/extract_news.py "URL"

# 指定输出目录
uv run scripts/extract_news.py "URL" --output ./output

# 仅输出 JSON
uv run scripts/extract_news.py "URL" --format json

# 仅输出 Markdown
uv run scripts/extract_news.py "URL" --format markdown

# Twitter 受保护推文（需要 Cookie）
uv run scripts/extract_news.py "URL" --cookie "auth_token=xxx; ct0=yyy"
```

## 目录结构

```
.claude/skills/news-extractor/
├── SKILL.md                      # 技能定义文件（Claude Code 自动读取）
├── pyproject.toml                # 依赖管理
├── references/
│   └── platform-patterns.md      # 平台 URL 模式说明
└── scripts/
    ├── extract_news.py           # CLI 入口脚本
    ├── models.py                 # 数据模型
    ├── detector.py               # 平台检测
    ├── formatter.py              # Markdown 格式化
    └── crawlers/                 # 爬虫模块
        ├── __init__.py
        ├── base.py               # BaseNewsCrawler 基类
        ├── fetchers.py           # HTTP 获取策略
        ├── wechat.py             # 微信公众号
        ├── toutiao.py            # 今日头条
        ├── netease.py            # 网易新闻
        ├── sohu.py               # 搜狐新闻
        ├── tencent.py            # 腾讯新闻
        ├── bbc.py                # BBC News
        ├── cnn.py                # CNN News
        ├── twitter.py            # Twitter/X
        ├── twitter_client.py     # Twitter API 客户端
        ├── twitter_types.py      # Twitter 数据类型
        ├── lenny.py              # Lenny's Newsletter
        ├── naver.py              # Naver Blog
        ├── detik.py              # Detik News
        └── quora.py              # Quora
```

## 依赖说明

| 包名 | 用途 |
|------|------|
| pydantic | 数据模型验证 |
| requests | HTTP 请求 |
| curl_cffi | 浏览器模拟抓取 |
| tenacity | 重试机制 |
| parsel | HTML/XPath 解析 |
| demjson3 | 非标准 JSON 解析 |

## 注意事项

- 所有脚本必须使用 `uv run` 执行，不要直接用 `python`
- 技能完全自包含，不依赖外部项目代码
- 微信公众号可能需要有效的 Cookie（默认配置通常可用）
- Twitter 公开推文无需认证，受保护推文需要 `auth_token` + `ct0` Cookie
- 仅用于教育和研究目的，请遵守目标网站的 robots.txt 和服务条款
