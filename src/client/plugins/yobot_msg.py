# coding=utf-8

import json
import os.path
import sys
from typing import Any


class Message:
    Passive = True
    Active = False
    
    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.version = glo_setting["version"]["ver_name"]

    @staticmethod
    def match(cmd: str) -> int:
        if (cmd == "报名公会战"
                or cmd == "公会战名单"
                or cmd == "清空公会"
                or cmd == "每日重置"
                or cmd.startswith("踢出公会")):
            return 1
        elif cmd == "下来吧" or cmd == "下树":
            return 2
        elif cmd == "十连抽图" or cmd == "检查卡池":
            return 3
        elif cmd == "台服活动" or cmd == "台服新闻" or cmd == "日服活动" or cmd == "日服新闻":
            return 5
        elif cmd == "ver" or cmd == "V" or cmd == "version":
            return 99
        elif cmd == "菜单" or cmd == "功能" or cmd == "帮助" or cmd == "help":
            return 98
        else:
            return 0

    def execute(self, match_num: int, msg: dict) -> dict:
        if match_num == 99:
            reply = self.version
        elif match_num == 98:
            reply = "请查看http://h3.yobot.monster/"
        else:
            reply = "此功能已经不再可用，请查看http://h3.yobot.monster/"
        return {
            "reply": reply,
            "block": True
        }
