import asyncio
import datetime
import time
from typing import Any, Callable, Dict, Iterable, List, Tuple

import aiohttp
import feedparser
from apscheduler.triggers.interval import IntervalTrigger

from .spider import Spiders


class News:
    Passive = False
    Active = True
    Request = False

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting
        self.spiders = Spiders()
        self.rss = {
            "news_jp_twitter": {
                "name": "日服推特",
                "source": "https://rsshub.app/twitter/user/priconne_redive",
                "pattern": "{title}\n链接：{link}",
                "last_id": None
            },
            "news_jp_official": {
                "name": "日服官网",
                "source": "https://rsshub.app/pcr/news",
                "pattern": "{title}\n{link}",
                "last_id": None
            },
            "news_tw_facebook": {
                "name": "台服FaceBook",
                "source": "https://rsshub.app/facebook/page/SonetPCR",
                "pattern": "链接：{link}",
                "last_id": None
            },
            "news_cn_bilibili": {
                "name": "国服B站动态",
                "source": "https://rsshub.app/bilibili/user/dynamic/353840826/",
                "pattern": "{title}\n{link}",
                "last_id": None
            }
        }

    async def from_rss_async(self, source) -> str:
        rss_source = self.rss[source]
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
              + "检查RSS源：{}".format(rss_source["name"]))
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(rss_source["source"]) as response:
                    code = response.status
                    if code != 200:
                        print("rss源错误：{}，返回值：{}".format(
                            rss_source["name"], code))
                        return None
                    res = await response.text()
        except aiohttp.client_exceptions.ClientConnectionError:
            print("rss源连接错误："+rss_source["name"])
            return None
        except Exception as e:
            print("未知错误{} {}".format(type(e).__name__, e))
            return None
        feed = feedparser.parse(res)
        if feed["bozo"]:
            print("rss源解析错误："+rss_source["name"])
            return None
        last_id = rss_source["last_id"]
        rss_source["last_id"] = feed["entries"][0]["id"]
        if last_id is None:
            print("rss初始化："+rss_source["name"])
            return None
        news_list = list()
        for item in feed["entries"]:
            if item["id"] == last_id:
                break
            news_list.append(rss_source["pattern"].format_map(item))
        if news_list:
            return (rss_source["name"]+"更新：\n=======\n"
                    + "\n-------\n".join(news_list))
        else:
            return None

    async def from_spider_async(self, rss_source) -> str: ...

    async def get_news_async(self) -> List[str]:
        '''
        返回最新消息
        '''
        tasks = []

        # RSS
        subscripts = [s for s in self.rss.keys() if self.setting.get(s, True)]
        for source in subscripts:
            tasks.append(self.from_rss_async(source))

        # spider
        subscripts = [s for s in self.spiders.sources()
                      if self.setting.get(s, True)]
        for source in subscripts:
            tasks.append(self.spiders[source].get_news_async())

        if not tasks:
            return None

        res = await asyncio.gather(*tasks, return_exceptions=True)
        news = []
        for r in res:
            if r is None:
                continue
            elif isinstance(r, Exception):
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                      + " Exception: " + str(r))
                continue
            elif isinstance(r, str):
                news.append(r)
            else:
                print("ValueError")
        return news

    async def send_news_async(self) -> List[Dict[str, Any]]:
        sub_groups = self.setting.get("notify_groups", [])
        sub_users = self.setting.get("notify_privates", [])
        if not (sub_groups or sub_users):
            return None
        news = await self.get_news_async()
        sends = []
        for msg in news:
            for group in sub_groups:
                sends.append({
                    "message_type": "group",
                    "group_id": group,
                    "message": msg
                })
            for userid in sub_users:
                sends.append({
                    "message_type": "private",
                    "user_id": userid,
                    "message": msg
                })
        return sends

    def jobs(self) -> Iterable[Tuple[IntervalTrigger, Callable[[], Iterable[Dict[str, Any]]]]]:
        if not any([self.setting.get(s, True) for s in self.rss.keys()]):
            return tuple()
        sub_groups = self.setting.get("notify_groups", [])
        sub_users = self.setting.get("notify_privates", [])
        if not (sub_groups or sub_users):
            return tuple()
        interval = self.setting.get("news_interval_minutes", 30)
        trigger = IntervalTrigger(
            minutes=interval, start_date=datetime.datetime.now()+datetime.timedelta(seconds=60))
        job = (trigger, self.send_news_async)
        return (job,)
