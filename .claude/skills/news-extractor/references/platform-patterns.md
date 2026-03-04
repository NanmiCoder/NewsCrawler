# 新闻平台 URL 模式说明

本文档描述各平台的 URL 格式和特殊注意事项。

## 中文平台

### 微信公众号 (wechat)

**URL 格式**:
```
https://mp.weixin.qq.com/s/{article_id}
https://mp.weixin.qq.com/s?__biz=xxx&mid=xxx&idx=xxx&sn=xxx
```

**正则模式**: `https?://mp\.weixin\.qq\.com/s/`

**特点**:
- 支持传统页面和 SSR 渲染页面
- 使用 `curl_cffi` 进行 Chrome 模拟
- 可能需要 Cookie

---

### 今日头条 (toutiao)

**URL 格式**: `https://www.toutiao.com/article/{article_id}/`

**正则模式**: `https?://www\.toutiao\.com/article/`

---

### 网易新闻 (netease)

**URL 格式**:
```
https://www.163.com/news/article/{article_id}.html
https://www.163.com/dy/article/{article_id}.html
```

**正则模式**: `https?://www\.163\.com/(news|dy)/article/`

---

### 搜狐新闻 (sohu)

**URL 格式**: `https://www.sohu.com/a/{article_id}_{source_id}`

**正则模式**: `https?://www\.sohu\.com/a/`

---

### 腾讯新闻 (tencent)

**URL 格式**: `https://news.qq.com/rain/a/{article_id}`

**正则模式**: `https?://news\.qq\.com/rain/a/`

---

## 国际平台

### BBC News (bbc)

**URL 格式**: `https://www.bbc.com/news/articles/{article_id}`

**正则模式**: `https?://www\.bbc\.com/news/articles/`

**特点**:
- 无需认证
- 使用 `curl_cffi` Chrome 模拟
- 内容在 `<article>` 标签中

**示例**: `https://www.bbc.com/news/articles/c797qlx93j0o`

---

### CNN News (cnn)

**URL 格式**: `https://edition.cnn.com/YYYY/MM/DD/section/article-slug`

**正则模式**: `https?://edition\.cnn\.com/.+`

**特点**:
- 无需认证
- 内容在 `<main>` 标签中
- 保持文本和图片的顺序

**示例**: `https://edition.cnn.com/2025/10/27/uk/sami-hamdi-detained-ice-intl`

---

### Twitter/X (twitter)

**URL 格式**:
```
https://x.com/{username}/status/{tweet_id}
https://twitter.com/{username}/status/{tweet_id}
```

**正则模式**: `https?://(x\.com|twitter\.com)/.+/status/`

**特点**:
- 使用 GraphQL API（非 HTML 解析）
- **双认证模式**:
  1. Guest Token 模式（默认）：无需认证，可访问公开推文
  2. Cookie 认证模式：需要 `auth_token` + `ct0`
- 支持普通推文、长推文、文章、引用推文
- 提取图片和视频（最高码率）

**Cookie 获取方式**:
1. 登录 x.com
2. 打开 DevTools -> Network
3. 复制请求中的 Cookie

**示例**: `https://x.com/BarackObama/status/896523232098078720`

---

### Lenny's Newsletter (lenny)

**URL 格式**: `https://www.lennysnewsletter.com/p/{article-slug}`

**正则模式**: `https?://www\.lennysnewsletter\.com/p/`

**特点**:
- 富文本内容解析（列表、标题、图片）
- 处理懒加载图片

**示例**: `https://www.lennysnewsletter.com/p/how-duolingo-reignited-user-growth`

---

### Naver Blog (naver)

**URL 格式**: `https://blog.naver.com/{username}/{post_id}`

**正则模式**: `https?://blog\.naver\.com/`

**特点**:
- 两阶段获取：主页面 -> iframe 内容
- 内容在 `se-main-container` 中

**示例**: `https://blog.naver.com/orangememories/223618759620`

---

### Detik News (detik)

**URL 格式**: `https://news.detik.com/{category}/d-{id}/{slug}`

**正则模式**: `https?://news\.detik\.com/`

**特点**:
- 印尼新闻站点
- 封面媒体和正文分开解析

**示例**: `https://news.detik.com/internasional/d-7626006/5-pernyataan-trump`

---

### Quora (quora)

**URL 格式**:
```
https://www.quora.com/{question}/answers/{answer_id}
https://www.quora.com/{question}/answer/{slug}
```

**正则模式**: `https?://www\.quora\.com/`

**特点**:
- 非 HTML 解析，使用正则提取 JSON 数据
- 双重 JSON 解码
- 时间戳为微秒级

**示例**: `https://www.quora.com/What-is-the-best-life-advice/answers/113244679`

---

## 平台检测逻辑

检测器使用正则表达式按顺序匹配：

```python
PLATFORM_PATTERNS = {
    "wechat": r"https?://mp\.weixin\.qq\.com/s/",
    "toutiao": r"https?://www\.toutiao\.com/article/",
    "netease": r"https?://www\.163\.com/(news|dy)/article/",
    "sohu": r"https?://www\.sohu\.com/a/",
    "tencent": r"https?://news\.qq\.com/rain/a/",
    "bbc": r"https?://www\.bbc\.com/news/articles/",
    "cnn": r"https?://edition\.cnn\.com/.+",
    "twitter": r"https?://(x\.com|twitter\.com)/.+/status/",
    "lenny": r"https?://www\.lennysnewsletter\.com/p/",
    "naver": r"https?://blog\.naver\.com/",
    "detik": r"https?://news\.detik\.com/",
    "quora": r"https?://www\.quora\.com/",
}
```

## 常见问题

### Q: 为什么提取失败？

1. **Cookie 过期** - 更新 Cookie 配置
2. **页面结构变化** - 平台可能更新了模板
3. **反爬策略** - 请求频率过高
4. **网络问题** - 检查网络连接

### Q: Twitter 如何获取 Cookie？

1. 登录 x.com
2. 打开 DevTools (F12) -> Network
3. 找到任意请求，复制 Cookie 头
4. 使用 `--cookie` 参数传入

### Q: 图片无法显示？

某些平台图片有防盗链：
- 微信图片需要特定 Referer
- 搜狐图片可能是加密的 Base64
