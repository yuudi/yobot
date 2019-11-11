#coding: utf-8


import csv
import json
import os
import sys
import time

import requests

from plugins.yobot_errors import Server_error


class Consult:
    URL = "http://api.yobot.xyz/v2/nicknames/?type=csv"
    Feedback_URL = "http://api.yobot.xyz/v2/nicknames/?type=feedback&name="

    def __init__(self, glo_setting: dict):
        self.setting = glo_setting
        self.nickname = {}
        self.number = {}
        nickfile = os.path.join(glo_setting["dirname"], "nickname.csv")
        if not os.path.exists(nickfile):
            res = requests.get(self.URL)
            if res.status_code != 200:
                raise Server_error(
                    "bad server response. code: "+str(res.status_code))
            with open(nickfile, "w", encoding="utf-8-sig") as f:
                f.write(res.text)
        with open(nickfile, encoding="utf-8-sig") as f:
            f_csv = csv.reader(f)
            for row in f_csv:
                for col in row[1:]:
                    self.nickname[col] = row[0]
                self.number[int(row[0])] = row[1]

    def user_input(self, cmd: str) -> dict:
        def_lst = []
        in_list = cmd.split()
        if len(in_list) > 5:
            return {"code": 5, "msg": "防守人数过多"}
        for index in in_list:
            item = self.nickname.get(index.lower(), "error")
            if item == "error":
                requests.get(self.Feedback_URL+index)
                return {"code": 1, "msg": "没有找到"+index}
            def_lst.append(item)
        return {"code": 0, "def_lst": def_lst}

    def jjcsearch(self, def_lst: list) -> str:
        reply = ""
        query = ".".join(def_lst)
        data = requests.get("http://api.yobot.xyz/jjc_search?def=" + query)
        res = json.loads(data.text)
        if(res["code"] == 0):
            reply += "从pcrdfans com找到{}条记录\n".format(
                len(res["data"]["result"]))
            line = "\n=======\n"
            for result in res["data"]["result"]:
                reply += line
                line = "\n-------\n"
                text = ""
                for atker in result["atk"]:
                    text += self.number[atker["id"]]
                    if atker["equip"] or atker["star"]:
                        cmt = ""
                        if atker["star"]:
                            cmt += str(atker["star"])
                        if atker["equip"]:
                            cmt += "专"
                        text += "("+cmt+")"
                    text += " "
                text += "({},{}赞{}踩)".format(
                    result["updated"][2:10],
                    result["up"],
                    result["down"])
                reply += text
        else:
            raise Server_error("error code: {}, message : {}".format(
                res["code"], res["message"]))
        return reply

    @staticmethod
    def match(cmd: str) -> int:
        if cmd.startswith("jjc查询"):
            return 1
        else:
            return 0

    def execute(self, match_num: int, msg: dict) -> dict:
        if self.setting.get("jjc_consult",True) == False:
            reply = "此功能未启用"
        else:
            anlz = self.user_input(msg["raw_message"][5:])
            if anlz["code"] == 0:
                reply = self.jjcsearch(anlz["def_lst"])
            else:
                reply = anlz["msg"]
        return {
            "reply": reply,
            "block": True
        }
