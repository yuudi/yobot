import datetime
from typing import Any, Callable, Dict, Iterable, Tuple, Union

import feedparser
from apscheduler.triggers.interval import IntervalTrigger


class News:
    Passive = False
    Active = True

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting
        self.rss = {
            "news_jp_twitter": {
                "name": "日服推特",
                "source": "https://rsshub.app/twitter/user/priconne_redive",
                "last_id": None
            },
            "news_jp_official": {
                "name": "日服官网",
                "source": "https://priconne-redive.jp/news/feed/",
                "last_id": None
            }
        }

    def get_news(self) -> Iterable[Union[None, str]]:
        subscripts = [s for s in self.rss.keys() if self.setting.get(s, True)]
        for source in subscripts:
            rss_source = self.rss[source]
            feed = feedparser.parse(rss_source["source"])
            if feed["bozo"]:
                print("rss源错误："+rss_source["name"])
                continue
            last_id = rss_source["last_id"]
            rss_source["last_id"] = feed["entries"][0]["id"]
            if last_id is None:
                print("rss初始化"+rss_source["name"])
                continue
            news_list = list()
            for item in feed["entries"]:
                if item["id"] == last_id:
                    break
                news_list.append(
                    "标题：{title}\n链接：{link}\n{summary}".format_map(item)
                )
            if news_list:
                yield (rss_source["name"]+"更新：\n=======\n"
                       + "\n-------\n".join(news_list))

    def send_news(self) -> Iterable[Dict[str, Any]]:
        sub_groups = self.setting.get("notify_groups", [])
        sub_users= self.setting.get("notify_privates", [])
        if not (sub_groups or sub_users):
            return
        for msg in self.get_news():
            for group in sub_groups:
                yield {
                    "message_type": "group",
                    "group_id": group,
                    "message": msg
                }
            for userid in sub_users:
                yield {
                    "message_type": "private",
                    "user_id": userid,
                    "message": msg
                }

    def jobs(self) -> Iterable[Tuple[IntervalTrigger, Callable[[], Iterable[Dict[str, Any]]]]]:
        if not any([self.setting.get(s, True) for s in self.rss.keys()]):
            return tuple()
        interval = self.setting.get("news_interval_minutes", 30)
        trigger = IntervalTrigger(
            minutes=interval, start_date=datetime.datetime.now()+datetime.timedelta(seconds=5))
        job = (trigger, self.send_news)
        return (job,)
