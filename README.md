# NewsCrawlerCollection

## 免责声明

**本仓库的所有内容仅供学习和参考之用，禁止用于商业用途。**

- 任何人或组织不得将本仓库的内容用于非法用途或侵犯他人合法权益
- 本仓库所涉及的爬虫技术仅用于学习和研究，不得用于对其他平台进行大规模爬虫或其他非法行为
- 对于因使用本仓库内容而引起的任何法律责任，本仓库不承担任何责任
- 使用本仓库的内容即表示您同意本免责声明的所有条款和条件

---

## 项目简介

NewsCrawlerCollection 是一个多平台新闻/内容爬虫集合，目前支持以下平台：

### 新闻/内容平台
- **今日头条 (Toutiao)** - 中国头条新闻文章采集
- **微信公众号 (WeChat)** - 公众号文章采集（支持传统页面和SSR渲染页面）
- **Detik News** - 印尼新闻网站采集
- **Naver News** - 韩国Naver博客新闻采集
- **Lenny's Newsletter** - 国外知名Newsletter采集
- **Quora** - Quora问答内容采集

### 素材资源平台
- **Pexels** - 免费图片和视频素材下载
- **Pixabay** - 免费图片和视频素材下载
- **Coverr** - 免费视频素材下载
- **Mixkit** - 免费视频素材下载

## 环境准备

### 1. 创建 Python 虚拟环境

```bash
python3 -m venv venv
```

### 2. 激活虚拟环境

```bash
# Linux 或 macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装项目依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. (可选) 安装 Playwright 驱动

如果需要自动获取 User-Agent 和 Cookie，可以安装 Playwright：

> 默认不需要安装，因为项目已提供固定的 Headers 配置

```bash
playwright install
```

## 快速开始

### 运行示例代码

```bash
python main.py
```

---

## 今日头条新闻爬虫

### 基本用法

```python
from toutiao_news import ToutiaoNewsCrawler

# 头条新闻详情页 URL
toutiao_url = "https://www.toutiao.com/article/7434425099895210546/"

# 创建爬虫实例并运行
crawler = ToutiaoNewsCrawler(toutiao_url)
crawler.run()
```

### 高级用法 - 自定义 Headers

```python
from toutiao_news import ToutiaoNewsCrawler, RequestHeaders
from libs import playwright_driver

# 自动获取 Headers
new_url = "https://www.toutiao.com/article/7434425099895210546/"
_headers = playwright_driver.get_headers(new_url)

# 使用自定义 Headers
headers = RequestHeaders(
    user_agent=_headers.user_agent,
    cookie=_headers.cookie
)

# 创建爬虫实例，指定保存路径
crawler = ToutiaoNewsCrawler(
    new_url,
    headers=headers,
    save_path="custom_data/"
)
crawler.run()
```

### 输出结果示例

结果保存在 `data/` 目录下，文件名为文章ID，格式为 JSON：

**文件名**: `data/7434425099895210546.json`

```json
{
    "title": "OpenAI发布全新模型GPT-4 Turbo",
    "news_url": "https://www.toutiao.com/article/7434425099895210546/",
    "news_id": "7434425099895210546",
    "meta_info": {
        "author_name": "科技日报",
        "author_url": "https://www.toutiao.com/c/user/123456789/",
        "publish_time": "2024-11-08 10:30"
    },
    "contents": [
        {
            "type": "text",
            "content": "北京时间11月7日，OpenAI在首届开发者大会上发布了全新的GPT-4 Turbo模型。",
            "desc": "北京时间11月7日，OpenAI在首届开发者大会上发布了全新的GPT-4 Turbo模型。"
        },
        {
            "type": "image",
            "content": "https://p3-sign.toutiaoimg.com/tos-cn-i-qvj2lq49k0/xxx.jpg",
            "desc": "https://p3-sign.toutiaoimg.com/tos-cn-i-qvj2lq49k0/xxx.jpg"
        },
        {
            "type": "text",
            "content": "新模型具有更长的上下文窗口和更低的价格。",
            "desc": "新模型具有更长的上下文窗口和更低的价格。"
        }
    ],
    "texts": [
        "北京时间11月7日，OpenAI在首届开发者大会上发布了全新的GPT-4 Turbo模型。",
        "新模型具有更长的上下文窗口和更低的价格。"
    ],
    "images": [
        "https://p3-sign.toutiaoimg.com/tos-cn-i-qvj2lq49k0/xxx.jpg"
    ],
    "videos": []
}
```

---

## 微信公众号新闻爬虫

### 基本用法

```python
from wechat_news import WeChatNewsCrawler

# 微信公众号文章 URL
wechat_url = "https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw"

# 创建爬虫实例并运行
crawler = WeChatNewsCrawler(wechat_url)
crawler.run()
```

### 高级用法 - 自定义 Headers

```python
from wechat_news import WeChatNewsCrawler, RequestHeaders
from libs import playwright_driver

# 自动获取 Headers
new_url = "https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw"
_headers = playwright_driver.get_headers(new_url)

# 使用自定义 Headers
headers = RequestHeaders(
    user_agent=_headers.user_agent,
    cookie=_headers.cookie
)

# 创建爬虫实例，指定保存路径
crawler = WeChatNewsCrawler(
    new_url,
    headers=headers,
    save_path="custom_data/"
)
crawler.run()
```

### 输出结果示例

结果保存在 `data/` 目录下，文件名为文章ID，格式为 JSON：

**文件名**: `data/3Sr6nYjE1RF05siTblD2mw.json`

```json
{
    "title": "AI 时代的编程新范式",
    "news_url": "https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw",
    "news_id": "3Sr6nYjE1RF05siTblD2mw",
    "meta_info": {
        "author_name": "技术最前线",
        "author_url": "",
        "publish_time": "2024-11-09 14:20"
    },
    "contents": [
        {
            "type": "text",
            "content": "随着人工智能技术的快速发展，编程范式正在发生深刻变革。",
            "desc": ""
        },
        {
            "type": "image",
            "content": "https://mmbiz.qpic.cn/mmbiz_jpg/xxx/640",
            "desc": ""
        },
        {
            "type": "text",
            "content": "开发者需要掌握新的工具和思维方式。",
            "desc": ""
        },
        {
            "type": "text",
            "content": "• AI 辅助编程工具的兴起",
            "desc": ""
        },
        {
            "type": "text",
            "content": "• 低代码平台的普及",
            "desc": ""
        },
        {
            "type": "text",
            "content": "• 自然语言编程的探索",
            "desc": ""
        }
    ],
    "texts": [
        "随着人工智能技术的快速发展，编程范式正在发生深刻变革。",
        "开发者需要掌握新的工具和思维方式。",
        "• AI 辅助编程工具的兴起",
        "• 低代码平台的普及",
        "• 自然语言编程的探索"
    ],
    "images": [
        "https://mmbiz.qpic.cn/mmbiz_jpg/xxx/640"
    ],
    "videos": []
}
```

### 特性说明

- 支持传统微信公众号页面解析
- 支持小红书风格的 SSR 渲染页面（Vue SSR）
- 智能识别页面类型，自动选择解析策略
- 保留文章段落结构，支持列表项识别
- 提取图片、视频等多媒体内容

---

## Detik 新闻爬虫

### 基本用法

```python
from detik_news import DetikNewsCrawler

# Detik 新闻详情页 URL
detik_url = "https://news.detik.com/internasional/d-7626006/5-pernyataan-trump-di-pidato-kemenangan-pilpres-as"

# 创建爬虫实例并运行
crawler = DetikNewsCrawler(detik_url)
crawler.run()
```

### 高级用法 - 自定义 Headers

```python
from detik_news import DetikNewsCrawler, RequestHeaders
from libs import playwright_driver

# 自动获取 Headers
new_url = "https://news.detik.com/internasional/d-7626006/5-pernyataan-trump"
_headers = playwright_driver.get_headers(new_url)

# 使用自定义 Headers
headers = RequestHeaders(
    user_agent=_headers.user_agent,
    cookie=_headers.cookie
)

# 创建爬虫实例，指定保存路径
crawler = DetikNewsCrawler(
    new_url,
    headers=headers,
    save_path="custom_data/"
)
crawler.run()
```

---

## 完整示例代码

查看 `main.py` 文件了解如何使用多个爬虫：

```python
from toutiao_news import ToutiaoNewsCrawler
from wechat_news import WeChatNewsCrawler
from detik_news import DetikNewsCrawler

# 头条新闻
toutiao_url = "https://www.toutiao.com/article/7434425099895210546/"
toutiao_crawler = ToutiaoNewsCrawler(toutiao_url)
toutiao_crawler.run()

# 微信公众号
wechat_url = "https://mp.weixin.qq.com/s/3Sr6nYjE1RF05siTblD2mw"
wechat_crawler = WeChatNewsCrawler(wechat_url)
wechat_crawler.run()

# Detik 新闻
detik_url = "https://news.detik.com/internasional/d-7626006/5-pernyataan-trump"
detik_crawler = DetikNewsCrawler(detik_url)
detik_crawler.run()
```

## 数据结构说明

所有爬虫输出的 JSON 数据遵循统一的结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 文章标题 |
| `news_url` | string | 文章链接 |
| `news_id` | string | 文章唯一ID |
| `meta_info` | object | 元信息（作者、发布时间等） |
| `contents` | array | 结构化内容列表 |
| `texts` | array | 纯文本内容列表 |
| `images` | array | 图片URL列表 |
| `videos` | array | 视频URL列表 |

### ContentItem 结构

```json
{
    "type": "text|image|video",
    "content": "内容或URL",
    "desc": "描述信息"
}
```

## 注意事项

1. **Cookie 有效期**: 默认提供的 Cookie 可能会过期，如遇到访问问题，请使用 Playwright 自动获取最新 Headers
2. **请求频率**: 建议添加适当的延时，避免频繁请求被封禁
3. **数据使用**: 爬取的数据仅供学习研究使用，请勿用于商业用途
4. **法律合规**: 使用前请确保遵守目标网站的 robots.txt 和服务条款

## 项目结构

```
NewsCrawlerCollection/
├── data/                   # 爬取结果保存目录
├── libs/                   # 工具库
│   ├── playwright_driver.py
│   └── drissionpage_driver.py
│
├── # 新闻/内容平台爬虫
├── toutiao_news/          # 今日头条新闻爬虫
├── wechat_news/           # 微信公众号爬虫
├── detik_news/            # Detik新闻爬虫
├── naver_news/            # Naver博客新闻爬虫
├── lennysnewsletter/      # Lenny's Newsletter爬虫
├── quora/                 # Quora问答爬虫
│
├── # 素材资源平台爬虫
├── pexel/                 # Pexels素材下载器
├── pixabay/               # Pixabay素材下载器
├── cover_video/           # Coverr视频下载器
├── mixkit_video/          # Mixkit视频下载器
│
├── video_config/          # 视频配置文件
├── main.py                # 主程序入口
└── requirements.txt       # 依赖清单
```

## 技术栈

- **Python 3.x** - 主要编程语言
- **requests / curl_cffi** - HTTP 请求库
- **parsel** - HTML 解析
- **pydantic** - 数据验证
- **tenacity** - 重试机制
- **playwright** (可选) - 自动化浏览器

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 许可证

本项目仅供学习和研究使用。
