# coding=utf-8
import json
import os
import shutil
import sys
from functools import reduce
from typing import Any, Callable, Dict, Iterable, List, Tuple

from opencc import OpenCC

from plugins import (boss_dmg, char_consult, custom, gacha, jjc_consult,
                     push_news, switcher, updater, yobot_errors, yobot_msg)


class Yobot:
    Version = "v3.1.2"
    Commit = {"yuudi": 18}

    def __init__(self, *args, **kwargs):
        # self.send_msg = send_msg

        dirname = os.getcwd()
        config_f_path = os.path.join(dirname, "yobot_config.json")
        verinfo = updater.get_version(self.Version, self.Commit)
        inner_info = {
            "dirname": dirname,
            "verinfo": verinfo
        }

        if not os.path.exists(config_f_path):
            if verinfo["run-as"] == "exe":
                default_config_f_path = os.path.join(
                    sys._MEIPASS, "default_config.json")
            else:
                default_config_f_path = os.path.join(
                    dirname, "default_config.json")
            shutil.copyfile(default_config_f_path, config_f_path)
        with open(config_f_path, "r", encoding="utf-8") as config_file:
            try:
                self.glo_setting = json.load(config_file)
            except:
                raise yobot_errors.File_error(config_f_path + " been damaged")

        self.glo_setting.update(inner_info)

        self.ccs2t = OpenCC(self.glo_setting.get("zht_out_style", "s2t"))
        self.cct2s = OpenCC("t2s")

        updater_plugin = updater.Updater(self.glo_setting)

        plug_all = [
            updater_plugin,
            switcher.Switcher(self.glo_setting),
            yobot_msg.Message(self.glo_setting),
            gacha.Gacha(self.glo_setting),
            char_consult.Char_consult(self.glo_setting),
            jjc_consult.Consult(self.glo_setting),
            boss_dmg.Boss_dmg(self.glo_setting),
            push_news.News(self.glo_setting),
            custom.Custom(self.glo_setting)
        ]
        self.plug_passive = [p for p in plug_all if p.Passive]
        self.plug_active = [p for p in plug_all if p.Active]

    def active_jobs(self) -> List[Tuple[Any, Callable[[], Iterable[Dict[str, Any]]]]]:
        jobs = [p.jobs() for p in self.plug_active]
        return reduce(lambda x, y: x+y, jobs)

    def proc(self, msg: dict, *args, **kwargs) -> str:
        '''
        receive a message and return a reply
        '''
        # prefix
        if self.glo_setting.get("preffix_on", False):
            preffix = self.glo_setting.get("preffix_string", "")
            if not msg["raw_message"].startswith(preffix):
                return None
            else:
                msg["raw_message"] = (
                    msg["raw_message"][len(preffix):])

        # black-list
        if msg["sender"]["user_id"] in self.glo_setting.get("black-list", list()):
            return None

        # zht-zhs convertion
        if self.glo_setting.get("zht_in", False):
            msg["raw_message"] = self.cct2s.convert(msg["raw_message"])
        if msg["sender"].get("card", "") == "":
            msg["sender"]["card"] = msg["sender"]["nickname"]

        # run
        replys = []
        for pitem in self.plug_passive:
            func_num = pitem.match(msg["raw_message"])
            if func_num:
                res = pitem.execute(func_num, msg)
                replys.append(res["reply"])
                if res["block"]:
                    break
        reply_msg = "\n".join(replys)

        # zhs-zht convertion
        if self.glo_setting.get("zht_out", False):
            reply_msg = self.ccs2t.convert(reply_msg)

        return reply_msg

    def execute(self, cmd: str, *args, **kwargs):
        if cmd == "update":
            res = self.plug_passive[0].execute(0x30)
        return res["reply"]
