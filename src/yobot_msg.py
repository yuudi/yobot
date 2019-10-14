# coding=utf-8


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
        elif cmd == "ver" or cmd =="V" or cmd =="version":
            return 99
        else:
            return 0

    @staticmethod
    def msg(func_num):
        if func_num==99:
            return "yobot [ver 2.1.2.00]"
        else:
            return "此功能已经不再可用，请查看https://yobot.xyz/functions_2/"
