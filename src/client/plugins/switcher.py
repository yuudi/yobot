# coding=utf-8

import base64
import json
import os
import sys
from typing import Union


class Switcher:
    setting_url = "http://io.yobot.xyz/v3/setting"
    setting_refer_url = "https://yobot.xyz/setting-help"
    switchers = {
        "抽卡": "gacha",
        "jjc查询": "jjc_consult",
        "无效命令提示": "invalidity_notify"}

    def __init__(self, glo_setting: dict):
        self.setting = glo_setting

    def switch(self, func: str, sw: Union[bool, int, float, str]) -> None:
        self.setting[func] = sw
        config_path = os.path.join(
            self.setting["dirname"], "yobot_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.setting, f, indent=2, ensure_ascii=False)

    @staticmethod
    def match(cmd: str) -> int:
        if cmd.startswith("打开"):
            f = 0x100
        elif cmd.startswith("关闭"):
            f = 0x200
        elif cmd == "设置":
            f = 0x300
        elif cmd.startswith("设置"):
            f = 0x400
        else:
            f = 0
        return f

    def execute(self, match_num: int, msg: dict) -> dict:
        cmd = msg["raw_message"]
        if match_num == 0x300:
            reply = self.setting_url + "\n请在此页进行设置，完成后发送设置码即可"
            # # post to shorten url
            # {
            #     'signature': 'b7b55a841d',
            #     'action': 'shorturl',
            #     'url': 'http://io.yobot.monster/go/yourls-api.php',
            #     'format': 'json'
            # }
        elif match_num == 0x400:
            in_code = cmd[2:]
            try:
                de_code = base64.b64decode(in_code)
            except:
                reply = "设置码解码错误，请检查"
            # todo: ...
        elif match_num == 0x100 or match_num == 0x200:
            if cmd in self.switchers:
                func = self.switchers[cmd]
                sw = (match_num == 0x100)
                self.switch(func, sw)
                reply = func + ("已打开\n" if sw else "已关闭")
            else:
                reply = "没有此功能的开关，目前允许使用开关的功能有：" + \
                    "、".join(self.switchers)
        return {
            "reply": reply,
            "block": True
        }
