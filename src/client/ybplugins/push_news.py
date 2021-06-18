import asyncio
import datetime
import re
import time
from email.utils import parsedate_tz
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union

import aiohttp
import feedparser
from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .spider import Spiders


class News:
    Passive = False
    Active = True
    Request = False

    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 bot_api: Api,
                 *args, **kwargs):
        self.setting = glo_setting
        self.news_interval_auto = glo_setting['news_interval_auto']
        self.spiders = Spiders()
        self.scheduler = scheduler
        self.api = bot_api
        self._rssjob = {}
        self.rss = {
            "news_jp_twitter": {
                "name": "日服推特",
                "source": "http://rsshub.app.cdn.cloudflare.net/twitter/user/priconne_redive",
                # headers: 可选，附加请求头
                "headers": {"host": "rsshub.app"},
                "pattern": "{title}\n链接：{link}",
            },
            "news_jp_official": {
                "name": "日服官网",
                "source": "http://rsshub.app.cdn.cloudflare.net/pcr/news",
                "headers": {"host": "rsshub.app"},
                "pattern": "{title}\n{link}",
            },
            "news_cn_bilibili": {
                "name": "国服B站动态",
                "source": "http://rsshub.app.cdn.cloudflare.net/bilibili/user/dynamic/353840826",
                "headers": {"host": "rsshub.app"},
                "pattern": "{title}\n{link}",
            }
        }

    async def from_rss_async(self, source) -> str:
        rss_source = self.rss[source]
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
              + "检查RSS源：{}".format(rss_source["name"]))
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(rss_source["source"], headers=rss_source.get("headers")) as response:
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
        if self.news_interval_auto:
            updated = feed.feed.updated
            if updated is not None:
                # 获取rss上次刷新时间
                lastBuildDate = parsedate_tz(updated)
                nt = datetime.datetime.fromtimestamp(
                    time.mktime(lastBuildDate[:-1])
                    - lastBuildDate[-1]
                    + 28800)
                nt += datetime.timedelta(minutes=25)
                after10min = datetime.datetime.now()+datetime.timedelta(minutes=10)
                if nt > after10min:
                    # 执行时间改为上次刷新后25分钟
                    self.scheduler.reschedule_job(
                        job_id=source,
                        jobstore='default',
                        trigger=DateTrigger(nt),
                    )
        if len(feed["entries"]) == 0:
            print("rss无效："+rss_source["name"])
            return None
        last_id = rss_source.get("last_id")
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

    async def get_news_async(self) -> List[str]:
        '''
        返回最新消息
        '''
        tasks = []

        # RSS
        subscribes = [s for s in self.rss.keys() if self.setting.get(s, True)]
        for source in subscribes:
            tasks.append(self.from_rss_async(source))

        # spider
        subscribes = [s for s in self.spiders.sources()
                      if self.setting.get(s, True)]
        for source in subscribes:
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
                rr = r.replace('&nbsp;', ' ')
                rr = re.sub('\t', '', rr)
                rr = re.sub('(\s)+', '\\1', rr)
                rr = rr.strip()
                news.append(rr)
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
        if self.news_interval_auto:
            # 如果设置为自动
            self.auto_job()
            return tuple()
        interval = self.setting.get("news_interval_minutes", 30)
        trigger = IntervalTrigger(
            minutes=interval, start_date=datetime.datetime.now()+datetime.timedelta(seconds=60))
        job = (trigger, self.send_news_async)
        return (job,)

    def auto_job(self):
        after_60s = datetime.datetime.now()+datetime.timedelta(seconds=60)

        # spider 为20分钟间隔
        self.scheduler.add_job(
            self.send_spider_news_async,
            trigger=IntervalTrigger(minutes=20, start_date=after_60s),
            misfire_grace_time=60,
            coalesce=True,
            max_instances=1,
        )

        # 每个 rss 启动第一个任务
        subscribes = [s for s in self.rss.keys() if self.setting.get(s, True)]
        for source in subscribes:
            self.scheduler.add_job(
                self.send_rss_news_async,
                args=(source,),
                id=source,
                trigger=DateTrigger(after_60s),
                misfire_grace_time=60,
                coalesce=True,
                max_instances=1,
            )

    async def send_spider_news_async(self):
        tasks = [
            self.spiders[s].get_news_async()
            for s in self.spiders.sources()
            if self.setting.get(s, True)
        ]
        res = await asyncio.gather(*tasks, return_exceptions=True)
        for i in range(len(res)):
            if isinstance(res[i], str):
                rr = res[i].replace('&nbsp;', ' ')
                rr = re.sub('\t', '', rr)
                rr = re.sub('(\s)+', '\\1', rr)
                res[i] = rr.strip()
        await self.send_news_msg_async(res)

    async def send_rss_news_async(self, source):
        # 执行时间改为5分钟后
        self.scheduler.add_job(
            self.send_rss_news_async,
            args=(source,),
            id=source,
            jobstore='default',
            misfire_grace_time=60,
            coalesce=True,
            max_instances=1,
            trigger=DateTrigger(
                datetime.datetime.now()+datetime.timedelta(minutes=5)
            ),
        )
        res = await self.from_rss_async(source)
        await self.send_news_msg_async([res])

    async def send_news_msg_async(self, res: List[Union[Exception, str, None]]):
        sub_groups = self.setting.get("notify_groups", [])
        sub_users = self.setting.get("notify_privates", [])
        for new_message in res:
            if new_message is None:
                continue
            elif isinstance(new_message, Exception):
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                      + " Exception: " + str(new_message))
                continue
            for group in sub_groups:
                await self.api.send_group_msg(
                    group_id=group,
                    message=new_message,
                )
            for user in sub_users:
                await self.api.send_private_msg(
                    user_id=user,
                    message=new_message,
                )
