import base64
import hashlib
import json
import os
from typing import Union
from urllib.parse import quote, urljoin

import requests

from . import shorten_url


class Switcher:
    Passive = True
    Active = False
    Request = False
    code_api = "http://api.yobot.xyz/v3/coding/?code="
    setting_url = {
        "global": "http://io.yobot.monster/3.1.7/settings/",
        'pool': 'http://io.yobot.monster/3.1.4-p/pool/',
        'mail': 'http://io.yobot.monster/3.1.0/mail/',
        'news': 'http://io.yobot.monster/3.1.8/news/',
        'boss': 'http://io.yobot.monster/3.1.15/boss/',
    }

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting

    def save_settings(self) -> None:
        save_setting = self.setting.copy()
        del save_setting["dirname"]
        del save_setting["verinfo"]
        config_path = os.path.join(
            self.setting["dirname"], "yobot_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(save_setting, f, indent=4)

    def get_url_content(self, url: str) -> Union[int, str]:
        try:
            res = requests.get(url)
        except requests.exceptions.ConnectionError:
            return -1
        if res.status_code != 200:
            return res.status_code
        else:
            return res.text

    @staticmethod
    def match(cmd: str) -> int:
        if cmd == "设置":
            f = 0x300
        elif cmd.startswith("设置码"):
            f = 0x400
        elif cmd.startswith("设置"):
            if len(cmd) < 7:
                f = 0x500
            else:
                f = 0
        else:
            f = 0
        return f

    def dump_url(self, keys, base) -> str:
        setting_dict = {}
        for k in keys:
            setting_dict[k] = self.setting.get(k, None)
        query = json.dumps(setting_dict, separators=(',', ':'))
        full_url = self.setting_url[base] + "?form=" + quote(query)
        return shorten_url.shorten(full_url)

    def get_setting_pool_url(self) -> str:
        poolfile = os.path.join(self.setting["dirname"], "pool3.json")
        with open(poolfile, "r", encoding="utf-8") as f:
            pool = json.load(f)
        query = json.dumps(pool, separators=(',', ':'), ensure_ascii=False)
        try:
            res = requests.post(self.code_api, data={"raw": query})
        except requests.exceptions.ConnectionError:
            return "服务器连接错误"
        if res.status_code != 200:
            return "异常的服务器返回值：{}".format(res.status_code)
        full_url = self.setting_url["pool"] + "?code=" + res.text
        return full_url

    def setting_pool(self, pool: dict) -> str:
        poolfile = os.path.join(self.setting["dirname"], "pool3.json")
        with open(poolfile, "w", encoding="utf-8") as f:
            json.dump(pool, f, indent=4, ensure_ascii=False)
        return "设置成功，重启后生效\n发送“重启”可重新启动"

    def setting_mail(self, code: str) -> str:
        while code.endswith('='):
            code = '=' + code[:-1]
        try:
            raw = base64.b64decode(code[::-1])
            confirm = raw[:32].decode()
            data = raw[32:]
            md5 = hashlib.md5(data)
            assert confirm == md5.hexdigest()
            config = json.loads(data.decode())
        except:
            return '设置码不完整，请检查'
        mailfile = os.path.join(self.setting["dirname"], "mailconf.json")
        if not os.path.exists(mailfile):
            return '未初始化'
        if config['s'] == '':
            config['s'] = 'smtp.' + config['m'].split('@')[1]
        if config['n'] == '':
            config['n'] = config['m']
        with open(mailfile, "r+") as f:
            mailconf = json.load(f)
            mailconf['sender'] = {
                "host": config['s'],
                "user": config['m'],
                "pswd": config['p'],
                "sender": config['n']
            }
            f.seek(0)
            f.truncate()
            json.dump(mailconf, f, indent=4)
        return '设置成功'

    def setting_boss(self, new_boss_info: dict) -> str:
        with open(os.path.join(self.setting["dirname"], "boss3.json"), "w", encoding="utf-8") as f:
            json.dump(new_boss_info, f, indent=4)
        return '设置成功'

    def execute(self, match_num: int, msg: dict) -> dict:
        super_admins = self.setting.get("super-admin", list())
        restrict = self.setting.get("setting-restrict", 3)
        cmd = msg["raw_message"]
        if msg["sender"]["user_id"] in super_admins:
            role = 0
        else:
            role_str = msg["sender"].get("role", None)
            if role_str == "owner":
                role = 1
            elif role_str == "admin":
                role = 2
            else:
                role = 3
        if role > restrict:
            if not cmd.startswith(("卡池", "邮箱", "新闻", "boss", "码"), 2):
                return None
            reply = "你的权限不足"
            return {"reply": reply, "block": True}

        if match_num == 0x300:
            if self.setting["clan_battle_mode"] != "chat":
                return urljoin(
                    self.setting['public_address'],
                    '{}admin/setting/'.format(self.setting['public_basepath']))
            keys = ("super-admin", "black-list", "setting-restrict", "auto_update",
                    "update-time", "show_jjc_solution", "gacha_on", "gacha_private_on",
                    "preffix_on", "preffix_string", "zht_in", "zht_out", "zht_out_style",
                    "calender_region")
            reply = (self.dump_url(keys, "global") + "\n请在此页进行设置，完成后发送设置码即可\n"
                     "其他设置请发送“设置卡池”、“设置邮箱”、“设置新闻”、“设置boss”")
            reply += "\n\n或使用新版设置：" + urljoin(
                self.setting['public_address'],
                '{}admin/setting/'.format(self.setting['public_basepath']))
        elif match_num == 0x400:
            in_code = cmd[3:]
            res = self.get_url_content(self.code_api+in_code)
            if isinstance(res, int):
                reply = "服务器错误：{}".format(res)
                return {"reply": reply, "block": True}
            try:
                new_setting = json.loads(res)
            except json.JSONDecodeError:
                reply = "服务器返回值异常"
                return {"reply": reply, "block": True}
            version = new_setting.get("version", 0)
            if version == 3107:  # 常规设置
                self.setting.update(new_setting["settings"])
                self.save_settings()
                reply = "设置成功"
            elif version == 3104:  # 卡池设置
                reply = self.setting_pool(new_setting["settings"])
            elif version == 3099:  # 邮箱设置
                reply = self.setting_mail(new_setting["settings"])
            elif version == 3108:  # 新闻设置
                self.setting.update(new_setting["settings"])
                self.save_settings()
                reply = "设置成功，重启后生效\n发送“重启”可重新启动"
            elif version == 3115:  # 邮箱设置
                reply = self.setting_boss(new_setting["settings"])
            else:
                reply = "设置码版本错误"
        elif match_num == 0x500:
            if cmd == "设置卡池":
                if self.setting["clan_battle_mode"] != "chat":
                    return urljoin(
                        self.setting['public_address'],
                        '{}admin/pool-setting/'.format(self.setting['public_basepath']))
                reply = self.get_setting_pool_url()
            elif cmd == "设置邮箱":
                if self.setting["clan_battle_mode"] != "chat":
                    return '此设置不再可用'
                reply = self.setting_url["mail"]
            elif cmd == "设置新闻" or cmd == "设置日程":
                if self.setting["clan_battle_mode"] != "chat":
                    return '请机器人管理员在后台设置中进行设置'
                keys = ("news_jp_official", "news_jp_twitter", "news_tw_official",
                        "news_tw_facebook", "news_cn_official", "news_cn_bilibili",
                        "news_interval_minutes", "notify_groups", "notify_privates",
                        "calender_on", "calender_time", "calender_region")
                reply = self.dump_url(keys, "news")
            elif cmd == "设置boss":
                if self.setting["clan_battle_mode"] != "chat":
                    return '请机器人管理员后台设置中进行设置（boss设置在最下方折叠）'
                with open(os.path.join(self.setting["dirname"], "boss3.json")) as f:
                    content = json.load(f)
                query = json.dumps(content, separators=(',', ':'))
                full_url = self.setting_url['boss'] + "?form=" + quote(query)
                reply = shorten_url.shorten(full_url)
            else:
                return

        return {
            "reply": reply,
            "block": True
        }
