#coding: utf-8

import csv
import json
import os
import sys
import time

import requests


class Consult():
    URL = "http://api.yobot.xyz/v2/nicknames/?type=csv"
    Feedback_URL = "http://api.yobot.xyz/v2/nicknames/?type=feedback&name="

    def __init__(self):
        path = os.path.dirname(sys.argv[0])
        self.nickname = {}
        self.number = {}
        self.def_lst = []
        nickfile = os.path.join(path, "nickname.csv")
        self.txt_list = []
        if not os.path.exists(nickfile):
            res = requests.get(self.URL)
            assert res.status_code == 200, "服务器不可用"
            with open(nickfile, "w", encoding="utf-8-sig") as f:
                f.write(res.text)
        with open(nickfile, encoding="utf-8-sig")as f:
            f_csv = csv.reader(f)
            for row in f_csv:
                for col in row[1:]:
                    self.nickname[col] = row[0]
                self.number[int(row[0])] = row[1]

    def user_input(self, cmd):
        in_list = cmd.split()
        if len(in_list) > 5:
            self.txt_list.append("防守人数过多")
            return 5
        for index in in_list:
            item = self.nickname.get(index.lower(), "error")
            if item == "error":
                requests.get(self.Feedback_URL+index)
                self.txt_list.append("没有找到"+index+"，已发送反馈")
                os.remove(os.path.join(os.path.dirname(
                    sys.argv[0]), "nickname.csv"))
                return 1
            self.def_lst.append(item)
        return 0

    def jjcsearch(self):
        query = ".".join(self.def_lst)
        data = requests.get("http://api.yobot.xyz/jjc_search?def=" + query)
        res = json.loads(data.text)
        if(res["code"] == 0):
            self.txt_list.append("从pcrdfans.com找到{}条记录".format(
                len(res["data"]["result"])))
            line = "======="
            for result in res["data"]["result"]:
                self.txt_list.append(line)
                line = "-------"
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
                text += "({},{}赞{}踩)；".format(
                    result["updated"][2:10],
                    result["up"],
                    result["down"])
                self.txt_list.append(text)
        else:
            text = "error code: {}, message : {}".format(
                res["code"], res["message"])
