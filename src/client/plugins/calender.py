import datetime
import os
import re
import time

import requests
from apscheduler.triggers.cron import CronTrigger
from arrow.arrow import Arrow
from ics import Calendar
from opencc import OpenCC

from .yobot_errors import Input_error, Server_error


class Event:
    Passive = True
    Active = False

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting
        self.cct2s = OpenCC("t2s")

        # 时区：东8区
        self.timezone = datetime.timezone(datetime.timedelta(hours=8))

        # 代理地址：
        calender_source = "http://api.yobot.xyz/3.1.3/calender/"
        # 直连地址：
        # calender_source = r"https://calendar.google.com/calendar/ical/obeb9cdv0osjuau8e7dbgmnhts%40group.calendar.google.com/public/basic.ics"

        calender = None
        cachefile = os.path.join(glo_setting["dirname"], "calender_cache.ics")
        if os.path.exists(cachefile):
            cached_time = time.time() - os.stat(cachefile).st_mtime
            if cached_time < 500000:  # 缓存500000秒
                with open(cachefile, encoding="utf-8") as f:
                    calender = Calendar(f.read())
        if calender is None:
            try:
                res = requests.get(calender_source)
            except requests.exceptions.ConnectionError:
                raise Server_error("无法连接服务器")
            if res.status_code != 200:
                raise Server_error("无法连接服务器")
            with open(cachefile, "w", encoding="utf-8") as f:
                f.write(res.text)
            calender = Calendar(res.text)
        self.timeline = calender.timeline

    def get_day_events(self, match_num):
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
        events = self.timeline.on(date)
        return (daystr, events)

    @staticmethod
    def match(cmd: str) -> int:
        if not cmd.startswith("日程"):
            return 0
        if cmd == "日程" or cmd == "日程今日" or cmd == "日程今天":
            return 2
        if cmd == "日程明日" or cmd == "日程明天":
            return 3
        match = re.match(r"日程 ?(\d{1,2})月(\d{1,2})[日号]", cmd)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            return (0x113000 + 0x100*month + day)
        match = re.match(r"日程 ?(?:20)?(\d{2})年(\d{1,2})月(\d{1,2})[日号]", cmd)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return (0x100000 + 0x1000*year + 0x100*month + day)
        return 1

    def execute(self, match_num: int, msg: dict) -> dict:
        if match_num == 1:
            reply = "未知的日期，请参考http://h3.yobot.monster/"
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
        if not self.setting.get("calender_on", 1):
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
