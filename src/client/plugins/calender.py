import datetime
import json
import os
import re
import time

import requests
from apscheduler.triggers.cron import CronTrigger
from arrow.arrow import Arrow
from ics import Calendar
from opencc import OpenCC

from .yobot_errors import Input_error, Server_error


class NamedItem:
    def __init__(self, name=""):
        self.name = name


class Event_timeline:
    def __init__(self):
        self._tineline = dict()

    def add_event(self, start_t: Arrow, end_t: Arrow, name):
        t = start_t
        while t <= end_t:
            daystr = t.format(fmt="YYYYMMDD", locale="zh_cn")
            if daystr not in self._tineline:
                self._tineline[daystr] = list()
            self._tineline[daystr].append(NamedItem(name))
            t += datetime.timedelta(days=1)

    def at(self, day: Arrow):
        daystr = day.format(fmt="YYYYMMDD", locale="zh_cn")
        return self._tineline[daystr]


class Event:
    Passive = True
    Active = True

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting
        self.cct2s = OpenCC("t2s")

        # # 时区：东8区
        # self.timezone = datetime.timezone(datetime.timedelta(hours=8))

        # 。。。屁东8区，ics这个库解析的时候把时区略了，加东8区会有bug，导致每天早上8点前获取的calendar会延后一天
        self.timezone = datetime.timezone(datetime.timedelta(hours=0))

        self.load_timeline(glo_setting.get("calender_region", "default"))
        self.last_check = time.time()

    def load_timeline(self, rg):
        if rg == "default":
            self.timeline = None
        elif rg == "jp":
            self.timeline = self.load_timeline_jp()
        elif rg == "tw":
            self.timeline = self.load_timeline_tw()
        elif rg == "cn":
            self.timeline = None
        elif rg == "kr":
            self.timeline = None
        else:
            raise ValueError(f"unknown region: {rg}")

    def load_timeline_jp(self):
        # 代理地址：
        calender_source = "http://api.yobot.xyz/3.1.3/calender/"
        # 直连地址：
        # calender_source = r"https://calendar.google.com/calendar/ical/obeb9cdv0osjuau8e7dbgmnhts%40group.calendar.google.com/public/basic.ics"

        calender = None
        cachefile = os.path.join(self.setting["dirname"], "calender_cache.ics")
        if os.path.exists(cachefile):
            cached_time = time.time() - os.stat(cachefile).st_mtime
            if cached_time < 50000:  # 缓存50000秒
                with open(cachefile, encoding="utf-8") as f:
                    calender = Calendar(f.read())
        if calender is None:
            try:
                res = requests.get(calender_source)
            except requests.exceptions.ConnectionError:
                raise Server_error("无法连接服务器")
            if res.status_code != 200:
                raise Server_error(f"服务器状态错误：{res.status_code}")
            with open(cachefile, "w", encoding="utf-8") as f:
                f.write(res.text)
            calender = Calendar(res.text)
        return calender.timeline

    def load_time_tw(self, timestr) -> Arrow:
        d_time = datetime.datetime.strptime(timestr, r"%Y/%m/%d %H:%M")
        a_time = Arrow.fromdatetime(d_time)
        if a_time.time() < datetime.time(hour=5):
            a_time -= datetime.timedelta(hours=5)
        return a_time

    def load_timeline_tw(self):
        event_source = "https://pcredivewiki.tw/static/data/event.json"
        try:
            res = requests.get(event_source)
        except requests.exceptions.ConnectionError:
            raise Server_error("无法连接服务器")
        if res.status_code != 200:
            raise Server_error(f"服务器状态错误：{res.status_code}")
        events = json.loads(res.text)
        timeline = Event_timeline()
        for e in events:
            timeline.add_event(
                self.load_time_tw(e["start_time"]),
                self.load_time_tw(e["end_time"]),
                e["campaign_name"],
            )
        return timeline

    def check_and_update(self, interval=200000):
        if time.time() - self.last_check > interval:
            self.load_timeline(self.setting.get("calender_region", "default"))
            self.last_check = time.time()

    def get_day_events(self, match_num) -> tuple:
        if match_num == 2:
            daystr = "今天"
            date = Arrow.now(tzinfo=self.timezone)
        elif match_num == 3:
            daystr = "明天"
            date = Arrow.now(tzinfo=self.timezone) + datetime.timedelta(days=1)
        elif match_num & 0xf00000 == 0x100000:
            year = (match_num & 0xff000) >> 12
            month = (match_num & 0xf00) >> 8
            day = match_num & 0xff
            daystr = "{}年{}月{}日".format(2000+year, month, day)
            try:
                date = Arrow(2000+year, month, day)
            except ValueError as v:
                raise Input_error("日期错误：{}".format(v))
        events = self.timeline.at(date)
        return (daystr, events)

    def get_week_events(self) -> str:
        reply = "一周日程："
        date = Arrow.now(tzinfo=self.timezone)
        for i in range(7):
            events = self.timeline.at(date)
            events_str = "\n    ".join(e.name for e in events)
            if events_str == "":
                events_str = "没有记录"
            daystr = date.format("MM月DD日")
            reply += "\n{}：\n    {}".format(daystr,
                                            self.cct2s.convert(events_str))
            date += datetime.timedelta(days=1)
        return reply

    @staticmethod
    def match(cmd: str) -> int:
        if not cmd.startswith("日程"):
            return 0
        if cmd == "日程" or cmd == "日程今日" or cmd == "日程今天":
            return 2
        if cmd == "日程明日" or cmd == "日程明天":
            return 3
        if cmd == "日程表" or cmd == "日程一周" or cmd == "日程本周":
            return 4
        match = re.match(r"日程 ?(\d{1,2})月(\d{1,2})[日号]", cmd)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            return (0x114000 + 0x100*month + day)
        match = re.match(r"日程 ?(?:20)?(\d{2})年(\d{1,2})月(\d{1,2})[日号]", cmd)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return (0x100000 + 0x1000*year + 0x100*month + day)
        return 1

    def execute(self, match_num: int, msg: dict) -> dict:
        if self.timeline is None:
            reply = "未设置区服，请发送“{}设置”".format(
                self.setting.get("preffix_string", ""))
            return {"reply": reply, "block": True}
        if match_num == 1:
            reply = "未知的日期，请参考http://h3.yobot.monster/"
            return {"reply": reply, "block": True}
        self.check_and_update()
        if match_num == 4:
            reply = self.get_week_events()
            return {"reply": reply, "block": True}
        try:
            daystr, events = self.get_day_events(match_num)
        except Input_error as e:
            return {"reply": str(e), "block": True}

        events_str = "\n".join(e.name for e in events)
        if events_str == "":
            events_str = "没有记录"
        reply = "{}活动：\n{}".format(daystr, self.cct2s.convert(events_str))
        return {"reply": reply, "block": True}

    def send_daily(self):
        sub_groups = self.setting.get("notify_groups", [])
        sub_users = self.setting.get("notify_privates", [])
        if not (sub_groups or sub_users):
            return
        _, events = self.get_day_events(2)
        events_str = "\n".join(e.name for e in events)
        if events_str is None:
            return
        msg = "今日活动：\n{}".format(self.cct2s.convert(events_str))
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

    def jobs(self):
        if not self.setting.get("calender_on", False):
            return tuple()
        sub_groups = self.setting.get("notify_groups", [])
        sub_users = self.setting.get("notify_privates", [])
        if not (sub_groups or sub_users):
            return tuple()
        time = self.setting.get("calender_time", "08:00")
        hour, minute = time.split(":")
        trigger = CronTrigger(hour=hour, minute=minute)
        job = (trigger, self.send_daily)
        return (job,)
