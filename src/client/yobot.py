# coding=utf-8
import json
import mimetypes
import os
import random
import shutil
import socket
import sys
from functools import reduce
from typing import Any, Callable, Dict, Iterable, List, Tuple
from urllib.parse import urljoin

import requests
from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from opencc import OpenCC
from quart import Quart, send_file

if __package__:
    from .ybplugins import (boss_dmg, calender, clan_battle, gacha, homepage,
                            jjc_consult, login, marionette, push_news, settings,
                            switcher, templating, updater, web_util, ybdata,
                            yobot_msg, custom, miner, group_leave)
else:
    from ybplugins import (boss_dmg, calender, clan_battle, gacha, homepage,
                           jjc_consult, login, marionette, push_news, settings,
                           switcher, templating, updater, web_util, ybdata,
                           yobot_msg, custom, miner, group_leave)

# 本项目构建的框架非常粗糙，不建议各位把时间浪费本项目上
# 如果想开发自己的机器人，建议直接使用 nonebot 框架
# https://nonebot.cqp.moe/


class Yobot:
    Version = "[v3.6.4-beta.1]"
    Version_id = 202
    #  "git rev-list --count HEAD"

    def __init__(self, *,
                 data_path: str,
                 scheduler: AsyncIOScheduler,
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
                os.path.dirname(__file__), "packedfiles", "default_config.json")
        with open(default_config_f_path, "r", encoding="utf-8") as config_file:
            self.glo_setting = json.load(config_file)
        if not os.path.exists(config_f_path):
            shutil.copyfile(default_config_f_path, config_f_path)
            print("设置已初始化，发送help获取帮助")
        boss_filepath = os.path.join(dirname, "boss3.json")
        if not os.path.exists(boss_filepath):
            if is_packaged:
                default_boss_filepath = os.path.join(
                    sys._MEIPASS, "packedfiles", "default_boss.json")
            else:
                default_boss_filepath = os.path.join(
                    os.path.dirname(__file__), "packedfiles", "default_boss.json")
            shutil.copyfile(default_boss_filepath, boss_filepath)
        pool_filepath = os.path.join(dirname, "pool3.json")
        if not os.path.exists(pool_filepath):
            if is_packaged:
                default_pool_filepath = os.path.join(
                    sys._MEIPASS, "packedfiles", "default_pool.json")
            else:
                default_pool_filepath = os.path.join(
                    os.path.dirname(__file__), "packedfiles", "default_pool.json")
            shutil.copyfile(default_pool_filepath, pool_filepath)
        with open(config_f_path, "r", encoding="utf-8-sig") as config_file:
            cfg = json.load(config_file)
            for k in self.glo_setting.keys():
                if k in cfg:
                    self.glo_setting[k] = cfg[k]

        if verinfo is None:
            verinfo = updater.get_version(self.Version, self.Version_id)
            print(verinfo['ver_name'])

        # initialize database
        ybdata.init(os.path.join(dirname, 'yobotdata.db'))

        # initialize web path
        if not self.glo_setting.get("public_address"):
            try:
                res = requests.get("http://ip-api.com/json/?fields=8192")
                ipaddr = res.json()["query"]
            except:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 53))
                    ipaddr = s.getsockname()[0]
            self.glo_setting["public_address"] = "http://{}:{}/".format(
                ipaddr,
                self.glo_setting["port"],
            )

        if not self.glo_setting["public_address"].endswith("/"):
            self.glo_setting["public_address"] += "/"

        if not self.glo_setting["public_basepath"].startswith("/"):
            self.glo_setting["public_basepath"] = "/" + \
                self.glo_setting["public_basepath"]

        if not self.glo_setting["public_basepath"].endswith("/"):
            self.glo_setting["public_basepath"] += "/"

        # initialize update time
        if self.glo_setting["update-time"] == "random":
            self.glo_setting["update-time"] = "{:02d}:{:02d}".format(
                random.randint(2, 4),
                random.randint(0, 59)
            )

        # initialize client salt
        if self.glo_setting["client_salt"] is None:
            self.glo_setting["client_salt"] = web_util.rand_string(16)

        # save initialization
        with open(config_f_path, "w", encoding="utf-8") as config_file:
            json.dump(self.glo_setting, config_file, indent=4)

        # initialize utils
        templating.Ver = self.Version[2:-1]

        # generate random secret_key
        if(quart_app.secret_key is None):
            quart_app.secret_key = bytes(
                (random.randint(0, 255) for _ in range(16)))

        # add mimetype
        mimetypes.init()
        mimetypes.add_type('application/javascript', '.js')
        mimetypes.add_type('image/webp', '.webp')

        # add route for static files
        @quart_app.route(
            urljoin(self.glo_setting["public_basepath"],
                    "assets/<path:filename>"),
            methods=["GET"])
        async def yobot_static(filename):
            return await send_file(
                os.path.join(os.path.dirname(__file__), "public", "static", filename))

        # add route for output files
        if not os.path.exists(os.path.join(dirname, "output")):
            os.mkdir(os.path.join(dirname, "output"))

        @quart_app.route(
            urljoin(self.glo_setting["public_basepath"],
                    "output/<path:filename>"),
            methods=["GET"])
        async def yobot_output(filename):
            return await send_file(os.path.join(dirname, "output", filename))

        # openCC
        self.ccs2t = OpenCC(self.glo_setting.get("zht_out_style", "s2t"))
        self.cct2s = OpenCC("t2s")

        # filter
        self.black_list = set(self.glo_setting["black-list"])
        self.black_list_group = set(self.glo_setting["black-list-group"])
        self.white_list_group = set(self.glo_setting["white-list-group"])

        # update runtime variables
        self.glo_setting.update({
            "dirname": dirname,
            "verinfo": verinfo
        })
        kwargs = {
            "glo_setting": self.glo_setting,
            "bot_api": bot_api,
            "scheduler": scheduler,
            "app": quart_app,
        }

        # load plugins
        plug_all = [
            updater.Updater(**kwargs),
            switcher.Switcher(**kwargs),
            yobot_msg.Message(**kwargs),
            gacha.Gacha(**kwargs),
            jjc_consult.Consult(**kwargs),
            boss_dmg.Boss_dmg(**kwargs),
            push_news.News(**kwargs),
            calender.Event(**kwargs),
            homepage.Index(**kwargs),
            marionette.Marionette(**kwargs),
            login.Login(**kwargs),
            settings.Setting(**kwargs),
            web_util.WebUtil(**kwargs),
            clan_battle.ClanBattle(**kwargs),
        ]
        self.plug_passive = [p for p in plug_all if p.Passive]
        self.plug_active = [p for p in plug_all if p.Active]

        for p in plug_all:
            if p.Request:
                p.register_routes(quart_app)

        # load new plugins
        self.plug_new = [
            miner.Miner(**kwargs),
            group_leave.GroupLeave(**kwargs),
            custom.Custom(**kwargs),
        ]

    def active_jobs(self) -> List[Tuple[Any, Callable[[], Iterable[Dict[str, Any]]]]]:
        jobs = [p.jobs() for p in self.plug_active]
        return reduce(lambda x, y: x+y, jobs)

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
        if msg["sender"]["user_id"] in self.black_list:
            return None
        if msg["message_type"] == "group":
            if self.glo_setting["white_list_mode"]:
                if msg["group_id"] not in self.white_list_group:
                    return None
            else:
                if msg["group_id"] in self.black_list_group:
                    return None

        # zht-zhs convertion
        if self.glo_setting.get("zht_in", False):
            msg["raw_message"] = self.cct2s.convert(msg["raw_message"])
        if msg["sender"].get("card", "") == "":
            msg["sender"]["card"] = msg["sender"].get("nickname", "无法获取昵称")

        # run new
        reply_msg = None
        for plug in self.plug_new:
            ret = await plug.execute_async(msg)
            if ret is None:
                continue
            elif isinstance(ret, bool):
                if ret:
                    break
                else:
                    continue
            elif isinstance(ret, str):
                reply_msg = ret
                break
            else:
                raise ValueError('unsupport return type: {}'.format(type(ret)))

        if reply_msg:
            if self.glo_setting.get("zht_out", False):
                reply_msg = self.ccs2t.convert(reply_msg)
            return reply_msg

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
                if res is None:
                    continue
                if isinstance(res, str):
                    replys.append(res)
                    break
                if res is None:
                    break
                if res["reply"]:
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
