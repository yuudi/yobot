# coding=utf-8
import json
import os.path
import sys


class Message():

    @staticmethod
    def match(cmd):
        if (cmd == "报名公会战"
                or cmd == "公会战名单"
                or cmd == "清空公会"
                or cmd == "每日重置"
                or cmd.startswith("踢出公会")):
            return 1
        elif cmd == "下来吧" or cmd == "下树":
            return 2
        elif cmd == "十连抽图" or cmd == "检查卡池" or cmd == "更新卡池":
            return 3
        # elif cmd.startswith("jjc查询"):
        #     return 4
        elif cmd == "台服活动" or cmd == "台服新闻" or cmd == "日服活动" or cmd == "日服新闻":
            return 5
        elif cmd == "ver" or cmd == "V" or cmd == "version":
            return 99
        elif cmd == "菜单" or cmd == "功能" or cmd == "帮助":
            return 98
        else:
            return 0

    @staticmethod
    def msg(func_num):
        if func_num == 99:
            with open(os.path.join(os.path.dirname(sys.argv[0]), "version.json"),
                      "r", encoding="utf-8") as f:
                ver = json.load(f)["vername"]
            return ver
        elif func_num == 98:
            return "请查看https://yobot.xyz/functions_2/"
        else:
            return "此功能已经不再可用，请查看https://yobot.xyz/functions_2/"
