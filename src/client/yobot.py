# coding=utf-8
import json
import os
import platform
import sys
from typing import List

from opencc import OpenCC

from plugins import (boss_dmg, char_consult, gacha, jjc_consult, switcher,
                     updater, yobot_errors, yobot_msg, custom)


class Yobot:
    def __init__(self):
        # dirname = os.__file__
        dirname = os.getcwd()
        config_f_path = os.path.join(dirname, "yobot_config.json")
        if not os.path.exists(config_f_path):
            with open(config_f_path, "w", encoding="utf-8") as config_file:
                config_file.write('{"port":9222,"run-as":"exe"}')
        with open(config_f_path, "r", encoding="utf-8") as config_file:
            try:
                self.glo_setting = json.load(config_file)
            except:
                raise yobot_errors.File_error(
                    config_f_path + " been damaged")

        inner_info = {
            "dirname": dirname,
            "version": {
                "ver_name": "yobot[v3.0.0]",
                "ver_id": 3000,
                "checktime": 0,
                "latest": True,
                "check_url": ["https://gitee.com/yobot/yobot/raw/master/docs/v3/ver.json",
                              "https://yuudi.github.io/yobot/v3/ver.json",
                              "http://api.yobot.xyz/v3/version/"]}}
        self.glo_setting.update(inner_info)

        self.ccs2t = OpenCC(self.glo_setting.get("zht_out_style","s2t"))
        self.cct2s = OpenCC("t2s")

        self.plugins = [
            updater.Updater(self.glo_setting),
            switcher.Switcher(self.glo_setting),
            yobot_msg.Message(self.glo_setting),
            gacha.Gacha(self.glo_setting),
            char_consult.Char_consult(self.glo_setting),
            jjc_consult.Consult(self.glo_setting),
            boss_dmg.Boss_dmg(self.glo_setting),
            custom.Custom(self.glo_setting)
        ]

        if (platform.system() == "Windows"
                and not self.plugins[0].runable_powershell):
            print("=================================================\n"
                  "powershell不可用，无法自动更新，请检查powershell权限\n"
                  "详情请查看：https://yobot.xyz/p/648/\n"
                  "=================================================")

    def proc(self, msg: dict) -> str:
        if self.glo_setting.get("preffix_on", False):
            preffix = self.glo_setting.get("preffix_string", "")
            if not msg["raw_message"].startswith(preffix):
                return None
            else:
                msg["raw_message"] = (
                    msg["raw_message"][len(preffix):])
        if msg["sender"]["user_id"] in self.glo_setting.get("black-list", list()):
            return None
        if self.glo_setting.get("zht_in", False):
            msg["raw_message"] = self.cct2s.convert(msg["raw_message"])
        if msg["sender"].get("card", "") == "":
            msg["sender"]["card"] = msg["sender"]["nickname"]
        replys = []
        for pitem in self.plugins:
            func_num = pitem.match(msg["raw_message"])
            if func_num:
                res = pitem.execute(func_num, msg)
                replys.append(res["reply"])
                if res["block"]:
                    break
        reply_msg = "\n".join(replys)
        if self.glo_setting.get("zht_out", False):
            reply_msg = self.ccs2t.convert(reply_msg)
        return reply_msg

    def execute(self, cmd: str):
        if cmd == "update":
            res = self.plugins[0].execute(0x10)
        return res["reply"]
