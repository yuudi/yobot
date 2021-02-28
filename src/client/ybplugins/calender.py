import datetime
import json
import re

import aiohttp
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from arrow.arrow import Arrow

from .yobot_exceptions import InputError, ServerError

_calender_url = {
    "jp": "https://pcrbot.github.io/pcr-calendar/#jp",
    "tw": "https://pcrbot.github.io/pcr-calendar/#tw",
    "cn": "https://pcrbot.github.io/pcr-calendar/#cn",
}


class Event_timeline:
    def __init__(self):
        self._tineline = dict()

    def add_event(self, start_t: Arrow, end_t: Arrow, name):
        t = start_t
        while t <= end_t:
            daystr = t.format(fmt="YYYYMMDD", locale="zh_cn")
            if daystr not in self._tineline:
                self._tineline[daystr] = list()
            self._tineline[daystr].append(name)
            t += datetime.timedelta(days=1)

    def at(self, day: Arrow):
        daystr = day.format(fmt="YYYYMMDD", locale="zh_cn")
        return self._tineline.get(daystr, ())


class Event:
    Passive = True
    Active = True
    Request = False

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting

        # # 时区：东8区
        # self.timezone = datetime.timezone(datetime.timedelta(hours=8))

        # 。。。屁东8区，Arrow这个库解析的时候把时区略了，加东8区会有bug，导致每天早上8点前获取的calendar会延后一天
        self.timezone = datetime.timezone(datetime.timedelta(hours=0))

        self.timeline_default_region = "unknown"
        self.timelines = {
            "jp": None,
            "tw": None,
            "cn": None,
        }

    def load_timeline(self, rg):
        raise RuntimeError("no more sync calling")

    async def load_timeline_async(self, rg=None):
        if rg is None:
            rg = self.setting.get("calender_region", "default")
        self.timeline_default_region = rg
        try:
            self.timelines["jp"] = await self.load_timeline_jp_async()
            print("刷新日服日程表成功")
        except Exception as e:
            print("刷新日服日程表失败"+e)
        try:
            self.timelines["tw"] = await self.load_timeline_tw_async()
            print("刷新台服日程表成功")
        except Exception as e:
            print("刷新台服日程表失败"+e)
        try:
            self.timelines["cn"] = await self.load_timeline_cn_async()
            print("刷新国服日程表成功")
        except Exception as e:
            print("刷新国服日程表失败"+e)

    def load_time_jp(self, timestr) -> Arrow:
        d_time = datetime.datetime.strptime(timestr, r"%Y/%m/%d %H:%M:%S")
        a_time = Arrow.fromdatetime(d_time)
        if a_time.time() < datetime.time(hour=4):
            a_time -= datetime.timedelta(hours=4)
        return a_time

    async def load_timeline_jp_async(self):
        event_source = "https://cdn.jsdelivr.net/gh/pcrbot/calendar-updater-action@gh-pages/jp.json"
        async with aiohttp.request("GET", url=event_source) as response:
            if response.status != 200:
                raise ServerError(f"服务器状态错误：{response.status}")
            res = await response.text()
        events = json.loads(res)
        timeline = Event_timeline()
        for e in events:
            timeline.add_event(
                self.load_time_jp(e["start_time"]),
                self.load_time_jp(e["end_time"]),
                e["name"],
            )
        return timeline

    def load_time_tw(self, timestr) -> Arrow:
        d_time = datetime.datetime.strptime(timestr, r"%Y/%m/%d %H:%M")
        a_time = Arrow.fromdatetime(d_time)
        if a_time.time() < datetime.time(hour=5):
            a_time -= datetime.timedelta(hours=5)
        return a_time

    async def load_timeline_tw_async(self):
        event_source = "https://pcredivewiki.tw/static/data/event.json"
        async with aiohttp.request("GET", url=event_source) as response:
            if response.status != 200:
                raise ServerError(f"服务器状态错误：{response.status}")
            res = await response.text()
        events = json.loads(res)
        timeline = Event_timeline()
        for e in events:
            timeline.add_event(
                self.load_time_tw(e["start_time"]),
                self.load_time_tw(e["end_time"]),
                e["campaign_name"],
            )
        return timeline

    def load_time_cn(self, timestr) -> Arrow:
        d_time = datetime.datetime.strptime(timestr, r"%Y/%m/%d %H:%M:%S")
        a_time = Arrow.fromdatetime(d_time)
        if a_time.time() < datetime.time(hour=5):
            a_time -= datetime.timedelta(hours=5)
        return a_time

    async def load_timeline_cn_async(self):
        event_source = "https://cdn.jsdelivr.net/gh/pcrbot/calendar-updater-action@gh-pages/cn.json"
        async with aiohttp.request("GET", url=event_source) as response:
            if response.status != 200:
                raise ServerError(f"服务器状态错误：{response.status}")
            res = await response.text()
        events = json.loads(res)
        timeline = Event_timeline()
        for e in events:
            timeline.add_event(
                self.load_time_cn(e["start_time"]),
                self.load_time_cn(e["end_time"]),
                e["name"],
            )
        return timeline

    def get_day_events(self, date_num, rg) -> tuple:
        if date_num == 2:
            daystr = "今天"
            date = Arrow.now(tzinfo=self.timezone)
        elif date_num == 3:
            daystr = "明天"
            date = Arrow.now(tzinfo=self.timezone) + datetime.timedelta(days=1)
        elif date_num & 0xf00000 == 0x100000:
            year = (date_num & 0xff000) >> 12
            month = (date_num & 0xf00) >> 8
            day = date_num & 0xff
            daystr = "{}年{}月{}日".format(2000+year, month, day)
            try:
                date = Arrow(2000+year, month, day)
            except ValueError as v:
                raise InputError("日期错误：{}".format(v))
        else:
            raise ValueError(f'unespected date_num: {date_num}')
        events = self.timelines[rg].at(date)
        return (daystr, events)

    def get_week_events(self, rg) -> str:
        reply = "一周日程："
        date = Arrow.now(tzinfo=self.timezone)
        for i in range(7):
            events = self.timelines[rg].at(date)
            events_str = "\n⨠".join(events)
            if events_str == "":
                events_str = "没有记录"
            daystr = date.format("MM月DD日")
            reply += "\n======{}======\n⨠{}".format(daystr, events_str)
            date += datetime.timedelta(days=1)
        reply += "\n\n更多日程：{}".format(_calender_url.get(rg))
        return reply

    def execute(self, _: int, msg: dict) -> dict:
        cmd = msg["raw_message"]
        if cmd.startswith("日服"):
            rg = "jp"
            cmd = cmd[2:]
        elif cmd.startswith("台服"):
            rg = "tw"
            cmd = cmd[2:]
        elif cmd.startswith("国服"):
            rg = "cn"
            cmd = cmd[2:]
        else:
            rg = self.timeline_default_region
        if not cmd.startswith("日程"):
            return None
        if (rg is None) or (rg == "default"):
            return "未设置区服，请发送“{}设置”".format(self.setting.get("preffix_string", ""))
        timeline = self.timelines.get(rg)
        if timeline is None:
            return "日程表未初始化\n\n更多日程：{}".format(_calender_url.get(rg))

        if cmd == "日程表" or cmd == "日程一周" or cmd == "日程本周":
            reply = self.get_week_events(rg)
            return {"reply": reply, "block": True}
        if cmd == "日程" or cmd == "日程今日" or cmd == "日程今天":
            date_num = 2
        elif cmd == "日程明日" or cmd == "日程明天":
            date_num = 3
        elif cmd == "日程表" or cmd == "日程一周" or cmd == "日程本周":
            date_num = 4
        else:
            match = re.match(r"日程 ?(\d{1,2})月(\d{1,2})[日号]", cmd)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                date_num = (0x114000 + 0x100*month + day)
            else:
                match = re.match(
                    r"日程 ?(?:20)?(\d{2})年(\d{1,2})月(\d{1,2})[日号]", cmd)
                if match:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    date_num = (0x100000 + 0x1000*year + 0x100*month + day)
                else:
                    return None
        try:
            daystr, events = self.get_day_events(date_num, rg)
        except InputError as e:
            return {"reply": str(e), "block": True}

        events_str = "\n".join(events)
        if events_str == "":
            events_str = "没有记录"
        reply = "{}活动：\n{}".format(daystr, events_str)
        return {"reply": reply, "block": True}

    async def send_daily_async(self):
        print("正在刷新日程表")
        try:
            await self.load_timeline_async()
        except Exception as e:
            print("刷新日程表失败，失败原因："+str(e))
        if not self.setting['calender_on']:
            return
        sub_groups = self.setting.get("notify_groups", [])
        sub_users = self.setting.get("notify_privates", [])
        if not (sub_groups or sub_users):
            return
        _, events = self.get_day_events(2)
        events_str = "\n".join(events)
        if events_str is None:
            return
        msg = "今日活动：\n{}".format(events_str)
        sends = []
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

    def jobs(self):
        # 初始化任务
        init_trigger = DateTrigger(
            datetime.datetime.now() +
            datetime.timedelta(seconds=5)
        )  # 启动5秒后初始化
        init_job = (init_trigger, self.load_timeline_async)
        # 定时任务
        time = self.setting.get("calender_time", "08:00")
        splited_time = time.split(":")
        if len(splited_time) != 2:
            print('Error: 配置文件 calender_time 格式错误，将停止自动推送任务')
            return (init_job,)
        hour, minute = splited_time
        trigger = CronTrigger(hour=hour, minute=minute)
        job = (trigger, self.send_daily_async)
        return (job, init_job)
