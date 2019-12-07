import json
import time
from dataclasses import dataclass
from typing import Iterator, List, Tuple, Union
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class Item:
    idx: Union[str, int]
    content: str = ""

    def __eq__(self, other):
        return self.idx == other.idx


class Base_spider:
    def __init__(self):
        self.url = None
        self.name = None
        self.last_item = None

    def get_content(self) -> Tuple[str, int]:
        headers = {
            "Host": urlparse(self.url).netloc,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-TW,zh;q=0.9"
        }
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
              + "检查咨询源：{}".format(self.name))
        try:
            res = requests.get(self.url, headers=headers)
        except requests.exceptions.ConnectionError:
            return ("", -1)
        return (res.text, res.status_code)

    def get_json(self):
        text, code = self.get_content()
        if code == 200:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                print("咨询获取错误：{}，json解析错误".format(self.name))
                return None
        else:
            print("咨询获取错误：{}，错误码：{}".format(self.name, code))
            return None

    def get_soup(self) -> Union[BeautifulSoup, None]:
        text, code = self.get_content()
        if code == 200:
            return BeautifulSoup(text, "html.parser")
        else:
            print("咨询获取错误：{}，错误码：{}".format(self.name, code))
            return None

    def get_items(self) -> List[Item]: ...

    def get_new_items(self) -> Iterator[Item]:
        items = self.get_items()
        if not items:
            return
        last = self.last_item
        self.last_item = items[0]
        if last is None:
            print("咨询初始化：{}".format(self.name))
            return
        for item in items:
            if item == last:
                return
            yield item

    def get_news(self) -> str:
        contents = [item.content for item in self.get_new_items()]
        if not contents:
            return None
        return (self.name + "更新\n=======\n"
                + "\n-------\n".join(contents))
