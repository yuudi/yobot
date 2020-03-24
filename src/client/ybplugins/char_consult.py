import json
import os

import requests


class Char_consult:
    Passive = True
    Active = False
    Request = False
    Nick_URL = "http://api.yobot.xyz/v2/nicknames/?type=csv"
    Char_URL = "http://api.yobot.xyz/v2/nicknames/?type=charpage"

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting
        self.nickname = {}
        self.number = {}
        nickfile = os.path.join(glo_setting["dirname"], "nickname.csv")
        if not os.path.exists(nickfile):
            res = requests.get(self.Nick_URL)
            if res.status_code != 200:
                raise IOError
            with open(nickfile, "w", encoding="utf-8-sig") as f:
                f.write(res.text)
        with open(nickfile, encoding="utf-8-sig") as f:
            csv = f.read()
            for line in csv.split():
                row = line.split(",")
                for col in row[1:]:
                    self.nickname[col] = row[0]
                self.number[int(row[0])] = row[1]
        charfile = os.path.join(glo_setting["dirname"], "char_page.json")
        if not os.path.exists(charfile):
            res = requests.get(self.Char_URL)
            if res.status_code != 200:
                raise IOError
            with open(charfile, "w", encoding="utf-8") as f:
                f.write(res.text)
            self.char_page = json.loads(res.text)
        else:
            with open(charfile, "r", encoding="utf-8") as f:
                self.char_page = json.load(f)

    @staticmethod
    def match(cmd: str) -> int:
        if cmd.startswith("介绍"):
            return 1
        else:
            return 0

    def execute(self, match_num: int, msg: dict) -> dict:
        cmd = msg["raw_message"]
        char_id = self.nickname.get(cmd[2:].strip().lower(), None)
        if char_id == None:
            reply = "没有找到【{}】".format(cmd[2:])
        elif char_id not in self.char_page["page_id"]:
            reply = "暂无{}的介绍".format(cmd[2:])
        else:
            reply = (self.char_page["prefix"]
                     + str(self.char_page["page_id"][char_id]))
        return {
            "reply": reply,
            "block": True
        }
