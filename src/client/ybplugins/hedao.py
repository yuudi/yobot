import datetime
import json
import re

import aiohttp
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from arrow.arrow import Arrow

from .yobot_exceptions import InputError, ServerError


class Event:
    Passive = True
    Active = False
    Request = False

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting
        self.timezone = datetime.timezone(datetime.timedelta(hours=0))
        self.timeline = None


    @staticmethod
    def match(cmd: str) -> int:
        if not cmd.startswith("合刀"):
            return 0
        elif cmd.split()[0]!="合刀":
            return 0
        else:
            return 1

    def execute(self, match_num: int, msg: dict) -> dict:
        if match_num == 0:
            return None
        cmd=msg["message"]
        content=cmd.split()
        # print(cmd.split())
        if(len(content)!=4):
            reply="请输入：合刀 刀1伤害 刀2伤害 剩余血量\n如：合刀 50 60 70\n"
            return {
                "reply": reply,
                "block": True
            }
        d1=float(content[1])
        d2=float(content[2])
        rest=float(content[3])
        if(d1+d2<rest):
            reply="醒醒！这两刀是打不死boss的\n"
            return {
                "reply": reply,
                "block": True
            }
        dd1=d1
        dd2=d2
        if d1>=rest:
            dd1=rest
        if d2>=rest:
            dd2=rest        
        res1=(1-(rest-dd1)/dd2)*90+10; # 1先出，2能得到的时间
        res2=(1-(rest-dd2)/dd1)*90+10; # 2先出，1能得到的时间
        res1=round(res1,2)
        res2=round(res2,2)
        res1=str(res1)
        res2=str(res2)
        reply=""
        if(d1>=rest or d2>=rest):
            reply=reply+"注：\n"
            if(d1>=rest):
                reply=reply+"第一刀可直接秒杀boss，伤害按 "+str(rest)+" 计算\n"
            if(d2>=rest):
                reply=reply+"第二刀可直接秒杀boss，伤害按 "+str(rest)+" 计算\n"
        d1=str(d1)
        d2=str(d2)
        reply=reply+d1+"先出，另一刀可获得 "+res1+" 秒补偿刀\n"
        reply=reply+d2+"先出，另一刀可获得 "+res2+" 秒补偿刀\n"
        return {
            "reply": reply,
            "block": True
        }

