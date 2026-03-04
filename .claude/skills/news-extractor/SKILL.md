---
name: news-extractor
description: 新闻站点内容提取。支持 12 个平台：微信公众号、今日头条、网易新闻、搜狐新闻、腾讯新闻、BBC News、CNN News、Twitter/X、Lenny's Newsletter、Naver Blog、Detik News、Quora。当用户需要提取新闻内容、抓取公众号文章、爬取新闻、或获取新闻JSON/Markdown时激活。
---

# News Extractor Skill

从主流新闻平台提取文章内容，输出 JSON 和 Markdown 格式。

**独立可迁移**：本 Skill 包含所有必需代码，无外部依赖，可直接复制到其他项目使用。

## 支持平台 (12)

### 中文平台

| 平台 | ID | URL 示例 |
|------|-----|----------|
| 微信公众号 | wechat | `https://mp.weixin.qq.com/s/xxxxx` |
| 今日头条 | toutiao | `https://www.toutiao.com/article/123456/` |
| 网易新闻 | netease | `https://www.163.com/news/article/ABC123.html` |
| 搜狐新闻 | sohu | `https://www.sohu.com/a/123456_789` |
| 腾讯新闻 | tencent | `https://news.qq.com/rain/a/20251016A07W8J00` |

### 国际平台

| 平台 | ID | URL 示例 |
|------|-----|----------|
| BBC News | bbc | `https://www.bbc.com/news/articles/c797qlx93j0o` |
| CNN News | cnn | `https://edition.cnn.com/2025/10/27/uk/article-slug` |
| Twitter/X | twitter | `https://x.com/user/status/123456789` |
| Lenny's Newsletter | lenny | `https://www.lennysnewsletter.com/p/article-slug` |
| Naver Blog | naver | `https://blog.naver.com/username/123456` |
| Detik News | detik | `https://news.detik.com/internasional/d-123456/slug` |
| Quora | quora | `https://www.quora.com/question/answers/123456` |

## 依赖安装

本 skill 使用 uv 管理依赖。首次使用前需要安装：

```bash
cd .claude/skills/news-extractor
uv sync
```

**重要**: 所有脚本必须使用 `uv run` 执行，不要直接用 `python` 运行。

### 依赖列表

| 包名 | 用途 |
|------|------|
| pydantic | 数据模型验证 |
| requests | HTTP 请求 |
| curl_cffi | 浏览器模拟抓取 |
| tenacity | 重试机制 |
| parsel | HTML/XPath 解析 |
| demjson3 | 非标准 JSON 解析 |

## 使用方式

### 基本用法

```bash
# 提取新闻，自动检测平台，输出 JSON + Markdown
uv run .claude/skills/news-extractor/scripts/extract_news.py "URL"

# 指定输出目录
uv run .claude/skills/news-extractor/scripts/extract_news.py "URL" --output ./output

# 仅输出 JSON
uv run .claude/skills/news-extractor/scripts/extract_news.py "URL" --format json

# 仅输出 Markdown
uv run .claude/skills/news-extractor/scripts/extract_news.py "URL" --format markdown

# Twitter 受保护推文 (需要 Cookie)
uv run .claude/skills/news-extractor/scripts/extract_news.py "URL" --cookie "auth_token=xxx; ct0=yyy"

# 列出支持的平台
uv run .claude/skills/news-extractor/scripts/extract_news.py --list-platforms
```

### 输出文件

脚本默认输出两种格式到指定目录（默认 `./output`）：
- `{news_id}.json` - 结构化 JSON 数据
- `{news_id}.md` - Markdown 格式文章

## 工作流程

1. **接收 URL** - 用户提供新闻链接
2. **平台检测** - 自动识别平台类型
3. **内容提取** - 调用对应爬虫获取并解析内容
4. **格式转换** - 生成 JSON 和 Markdown
5. **输出文件** - 保存到指定目录

## 输出格式

### JSON 结构

```json
{
  "title": "文章标题",
  "news_url": "原始链接",
  "news_id": "文章ID",
  "meta_info": {
    "author_name": "作者/来源",
    "author_url": "",
    "publish_time": "2024-01-01 12:00"
  },
  "contents": [
    {"type": "text", "content": "段落文本", "desc": ""},
    {"type": "image", "content": "https://...", "desc": ""},
    {"type": "video", "content": "https://...", "desc": ""}
  ],
  "texts": ["段落1", "段落2"],
  "images": ["图片URL1", "图片URL2"],
  "videos": []
}
```

### Markdown 结构

```markdown
# 文章标题

## 文章信息
**作者**: xxx
**发布时间**: 2024-01-01 12:00
**原文链接**: [链接](URL)

---

## 正文内容

段落内容...

![图片](URL)

---

## 媒体资源
### 图片 (N)
1. URL1
2. URL2
```

## 使用示例

### 提取微信公众号文章

```bash
uv run .claude/skills/news-extractor/scripts/extract_news.py \
  "https://mp.weixin.qq.com/s/ebMzDPu2zMT_mRgYgtL6eQ"
```

### 提取 BBC 新闻

```bash
uv run .claude/skills/news-extractor/scripts/extract_news.py \
  "https://www.bbc.com/news/articles/c797qlx93j0o"
```

### 提取 Twitter 推文

```bash
# 公开推文 (无需认证)
uv run .claude/skills/news-extractor/scripts/extract_news.py \
  "https://x.com/BarackObama/status/896523232098078720"

# 受保护推文 (需要 Cookie)
uv run .claude/skills/news-extractor/scripts/extract_news.py \
  "https://x.com/user/status/123456" --cookie "auth_token=xxx; ct0=yyy"
```

## 错误处理

| 错误类型 | 说明 | 解决方案 |
|----------|------|----------|
| `无法识别该平台` | URL 不匹配任何支持的平台 | 检查 URL 是否正确 |
| `平台不支持` | 非支持的站点 | 本 Skill 仅支持列出的 12 个平台 |
| `提取失败` | 网络错误或页面结构变化 | 重试或检查 URL 有效性 |
| `认证失败` | Twitter Cookie 无效 | 重新获取 Cookie |

## 注意事项

- 仅用于教育和研究目的
- 不要进行大规模爬取
- 尊重目标网站的 robots.txt 和服务条款
- 微信公众号可能需要有效的 Cookie（当前默认配置通常可用）
- Twitter 公开推文无需认证，受保护推文需要 Cookie

## 目录结构

```
news-extractor/
├── SKILL.md                      # [必需] Skill 定义文件
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

## 参考

- [平台 URL 模式说明](references/platform-patterns.md)
