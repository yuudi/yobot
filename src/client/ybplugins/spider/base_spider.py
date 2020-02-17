import abc
import json
import time
from dataclasses import dataclass
from typing import List, Tuple, Union
from urllib.parse import urlparse

import aiohttp
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
        self.type = None
        self.name = None
        self.last_item = None

    async def get_content_async(self) -> Tuple[str, int]:
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
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(self.url) as response:
                    code = response.status
                    res = await response.text()
        except aiohttp.client_exceptions.ClientConnectionError:
            return ("", -1)
        return (res, code)

    async def get_json_async(self):
        text, code = await self.get_content_async()
        if code == 200:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                print("咨询获取错误：{}，json解析错误".format(self.name))
                return None
        else:
            print("咨询获取错误：{}，错误码：{}".format(self.name, code))
            return None

    async def get_soup_async(self) -> Union[BeautifulSoup, None]:
        text, code = await self.get_content_async()
        if code == 200:
            return BeautifulSoup(text, "html.parser")
        else:
            print("咨询获取错误：{}，错误码：{}".format(self.name, code))
            return None

    @abc.abstractmethod
    def get_items(self, response: Union[BeautifulSoup, dict]) -> List[Item]:
        ...

    async def get_new_items_async(self) -> List[Item]:
        if self.type == "html":
            response = await self.get_soup_async()
        elif self.type == "json":
            response = await self.get_json_async()
        if response is None:
            return []
        items = self.get_items(response)
        if not items:
            return []
        last = self.last_item
        self.last_item = items[0]
        if last is None:
            print("咨询初始化：{}".format(self.name))
            return []
        if last in items:
            idx = items.index(last)
            items = items[:idx]
        return items

    async def get_news_async(self) -> str:
        items = await self.get_new_items_async()
        if not items:
            return None
        contents = [i.content for i in items]
        return (self.name + "更新\n=======\n"
                + "\n-------\n".join(contents))
