# NewsCrawlerCollection

## 安装项目依赖

### 创建Python虚拟环境
```bash
python3 -m venv venv
```

### 激活Python虚拟环境
```bash
# linux or macos
source venv/bin/activate

# windows
venv\Scripts\activate
```

### 安装项目依赖
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果需要使用自动获取User-Agent和Cookie，需要单独安装playwright驱动
> 默认不使用，因为这两个网站目前看cookies固定跑着也没啥问题
> 
> 项目也集成了DrissionPage,也可以使用，安装文档见项目也集成了DrissionPage官网

```bash
playwright install
```

## 代码运行

可以直接到main.py中查看代码运行方式
```bash
python main.py
```

下面是单独运行头条新闻爬虫和detik新闻爬虫的代码

## 头条新闻爬虫

### 代码使用方式
```python
from libs import playwright_driver
from toutiao_news import ToutiaoNewsCrawler, RequestHeaders

# 是否需要自动获取headers(User-Agent和Cookie)
NEED_AUTO_GET_HEADERS = False

def get_toutiao_news_detail(new_url: str):
    """获取头条新闻详情

    Args:
        new_url (str): 新闻详情页URL

    Returns:
        _type_: _description_
    """
    if NEED_AUTO_GET_HEADERS:
        headers = playwright_driver.get_headers(new_url)
        toutiao_news = ToutiaoNewsCrawler(new_url, headers=RequestHeaders(**headers))
    else:
        toutiao_news = ToutiaoNewsCrawler(new_url)
    return toutiao_news.run()

if __name__ == "__main__":
    toutiao_url = "https://www.toutiao.com/article/7434425099895210546/?log_from=62fe902b9dcea_1730987379758"
    get_toutiao_news_detail(toutiao_url)
```

### 输出结果
以文章ID作为JSON文件名，保存到脚本运行的data目录下，`ToutiaoNewsCrawler`也支持传入`save_path`参数指定保存路径

## detik新闻爬虫

### 代码使用方式
```python
from libs import playwright_driver
from detik_news import DetikNewsCrawler, RequestHeaders

# 是否需要自动获取headers(User-Agent和Cookie)
NEED_AUTO_GET_HEADERS = False

def get_detik_news_detail(new_url: str):
    """获取detik新闻详情

    Args:
        new_url (str): 新闻详情页URL
    """
    if NEED_AUTO_GET_HEADERS:   
        headers = playwright_driver.get_headers(new_url)
        detik_news = DetikNewsCrawler(new_url, headers=RequestHeaders(**headers))
    else:
        detik_news = DetikNewsCrawler(new_url)
    return detik_news.run() 


if __name__ == "__main__":
    detik_url = "https://news.detik.com/internasional/d-7626006/5-pernyataan-trump-di-pidato-kemenangan-pilpres-as"
    get_detik_news_detail(detik_url)
```

### 输出结果
以文章ID作为JSON文件名，保存到脚本运行的data目录下，`DetikNewsCrawler`也支持传入`save_path`参数指定保存路径