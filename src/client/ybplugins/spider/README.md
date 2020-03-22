# RSS订阅与网页抓取

## RSS订阅

在[push_news.py](../push_news.py)文件里可以添加RSS订阅源

在`self.rss`里添加订阅，格式如下

```python
"news_jp_official": {  # 订阅名称，在yobot_config.json文件中控制开关的名称相同
    "name": "日服官网",  # 可读的名称
    "source": "https://priconne-redive.jp/news/feed/",  # 订阅地址
    "pattern": "标题：{title}\n链接：{link}\n{summary}",  # 转化为字符串的方法
    "last_id": None,  # 此项必须为 None
}
```

## 网页抓取

在[spider](../spider/)文件夹中可以添加爬虫

导入父类，创建一个子类

```python
from .base_spider import Base_spider, Item

class Spider_ostw(Base_spider):
    ...
```

编写属性

```python
    def __init__(self):
        super().__init__()
        self.url = "http://www.princessconnect.so-net.tw/news/" # 地址来源
        self.type = "html" # 来源的种类，取值：html, json, xml
        self.name = "台服官网" # 可读的名称
```

编写分析器

```python
    def get_items(self, soup): # 如果self.type是"html"则传入BeautifulSoup对象
        return [
            Item(
                # 编号，整数或字符串，判断新闻是否相同的依据
                idx=dd.a["href"],

                # 内容，字符串，要发送的新闻
                content="{}\n{}".format(dd.text, urljoin(self.url, dd.a["href"]))
            )
            for dd in soup.find_all("dd")
        ]
```

加入订阅（在[__init__.py](./__init__.py)文件里）

```python
# import新编写的子类
from .official_site_tw import Spider_ostw

class Spiders:
    def __init__(self):
        self.spiders = {
            "news_tw_official": Spider_ostw()
            # 将新的订阅加入
            # 键：订阅名称，在yobot_config.json文件中控制开关的名称相同
            # 值：对象，由新编写的子类创建出的对象
        }
    ...
```
