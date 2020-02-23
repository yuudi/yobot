# coding=utf-8
import json
import os
import random
import shutil
import socket
import sys
from functools import reduce
from typing import Any, Callable, Dict, Iterable, List, Tuple
from urllib.parse import urljoin

import peewee
import requests
from aiocqhttp.api import Api
from opencc import OpenCC
from quart import Quart, send_file

if __package__:
    from .ybplugins import (switcher, yobot_msg, gacha, jjc_consult, boss_dmg,
                            updater,  char_consult, push_news, calender, custom,
                            homepage, marionette, login, settings, web_api)
else:
    from ybplugins import (switcher, yobot_msg, gacha, jjc_consult, boss_dmg,
                           updater,  char_consult, push_news, calender, custom,
                           homepage, marionette, login, settings, web_api)


class Yobot:
    Version = "[v3.2.2]"
    Commit = {"yuudi": 39, "sunyubo": 1}

    def __init__(self, *,
                 data_path: str,
                 quart_app: Quart,
                 bot_api: Api,
                 verinfo: str = None):

        # initialize config
        is_packaged = "_MEIPASS" in dir(sys)
        if is_packaged:
            basepath = os.path.dirname(sys.argv[0])
        else:
            basepath = os.path.dirname(__file__)

        dirname = os.path.abspath(os.path.join(basepath, data_path))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        config_f_path = os.path.join(dirname, "yobot_config.json")
        if is_packaged:
            default_config_f_path = os.path.join(
                sys._MEIPASS, "packedfiles", "default_config.json")
        else:
            default_config_f_path = os.path.join(
                os.path.dirname(__file__), "default_config.json")
        with open(default_config_f_path, "r", encoding="utf-8") as config_file:
            self.glo_setting = json.load(config_file)
        if not os.path.exists(config_f_path):
            shutil.copyfile(default_config_f_path, config_f_path)
        boss_filepath = os.path.join(dirname, "boss3.json")
        if not os.path.exists(boss_filepath):
            if is_packaged:
                default_boss_filepath = os.path.join(
                    sys._MEIPASS, "packedfiles", "default_boss.json")
            else:
                default_boss_filepath = os.path.join(
                    os.path.dirname(__file__), "default_boss.json")
            shutil.copyfile(default_boss_filepath, boss_filepath)
        with open(config_f_path, "r+", encoding="utf-8") as config_file:
            self.glo_setting.update(json.load(config_file))
            config_file.seek(0)
            config_file.truncate()
            json.dump(self.glo_setting, config_file,
                      ensure_ascii=False, indent=4)

        if verinfo is None:
            verinfo = updater.get_version(self.Version, self.Commit)

        # initialize database
        self.database = peewee.SqliteDatabase(os.path.join(dirname, 'data.db'))

        class database_model(peewee.Model):
            class Meta:
                database = self.database

        # initialize web path
        modified = False
        if self.glo_setting.get("public_address") is None:
            try:
                res = requests.get("http://members.3322.org/dyndns/getip")
                ipaddr = res.text.strip()
            except:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 53))
                    ipaddr = s.getsockname()[0]
            self.glo_setting["public_address"] = "http://{}:{}/{}/".format(
                ipaddr,
                self.glo_setting["port"],
                self.glo_setting["public_basepath"].strip("/")
            )
            modified = True
        if not self.glo_setting["public_address"].endswith("/"):
            self.glo_setting["public_address"] += "/"
            modified = True
        if modified:
            with open(config_f_path, "w", encoding="utf-8") as config_file:
                json.dump(self.glo_setting, config_file,
                          ensure_ascii=False, indent=4)

        # generate random secret_key
        if(quart_app.secret_key is None):
            quart_app.secret_key = bytes(
                (random.randint(0, 255) for _ in range(16)))

        # add route for static files
        @quart_app.route(
            urljoin(self.glo_setting["public_basepath"], "assets/<filename>"),
            methods=["GET"])
        async def yobot_static(filename):
            return await send_file(
                os.path.join(os.path.dirname(__file__), "public/static", filename))

        # openCC
        self.ccs2t = OpenCC(self.glo_setting.get("zht_out_style", "s2t"))
        self.cct2s = OpenCC("t2s")

        # update runtime variables
        self.glo_setting.update({
            "dirname": dirname,
            "verinfo": verinfo
        })
        kwargs = {
            "glo_setting": self.glo_setting,
            "database_model": database_model,
            "bot_api": bot_api,
        }

        # load plugins
        plug_all = [
            updater.Updater(**kwargs),
            switcher.Switcher(**kwargs),
            yobot_msg.Message(**kwargs),
            gacha.Gacha(**kwargs),
            char_consult.Char_consult(**kwargs),
            jjc_consult.Consult(**kwargs),
            boss_dmg.Boss_dmg(**kwargs),
            push_news.News(**kwargs),
            calender.Event(**kwargs),
            homepage.Index(**kwargs),
            marionette.Marionette(**kwargs),
            login.Login(**kwargs),
            settings.Setting(**kwargs),
            web_api.WebApi(**kwargs),
            custom.Custom(**kwargs),
        ]
        self.plug_passive = [p for p in plug_all if p.Passive]
        self.plug_active = [p for p in plug_all if p.Active]

        for p in plug_all:
            if p.Request:
                p.register_routes(quart_app)

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
            if hasattr(pitem, 'match'):
                func_num = pitem.match(msg["raw_message"])
            else:
                func_num = True
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

    async def proc_async(self, msg: dict, *args, **kwargs) -> str:
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
            if hasattr(pitem, 'match'):
                func_num = pitem.match(msg["raw_message"])
            else:
                func_num = True
            if func_num:
                if hasattr(pitem, "execute_async"):
                    res = await pitem.execute_async(func_num, msg)
                else:
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
