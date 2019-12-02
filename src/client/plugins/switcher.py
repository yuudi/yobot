import base64
import json
import os
import sys
from typing import Union

import requests

from plugins import setting


class Switcher:
    code_api = "http://api.yobot.xyz/v3/coding/?code="
    setting_url = "http://io.yobot.monster/3.0.0-s/settings/"

    def __init__(self, glo_setting: dict):
        self.setting = glo_setting

    def save_settings(self) -> None:
        save_setting = self.setting.copy()
        del save_setting["dirname"]
        del save_setting["version"]
        config_path = os.path.join(
            self.setting["dirname"], "yobot_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(save_setting, f, indent=4, ensure_ascii=False)

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
        # if cmd.startswith("打开"):
        #     f = 0x100
        # elif cmd.startswith("关闭"):
        #     f = 0x200
        if cmd == "设置":
            f = 0x300
        elif cmd.startswith("设置码"):
            f = 0x400
        elif cmd.startswith("设置"):
            f = 0x500
        else:
            f = 0
        return f

    def execute(self, match_num: int, msg: dict) -> dict:
        super_admins = self.setting.get("super-admin", list())
        restrict = self.setting.get("setting-restrict", 3)
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
            reply = "你的权限不足"
            return {"reply": reply, "block": True}

        cmd = msg["raw_message"]
        if match_num == 0x300:
            reply = self.setting_url + "\n请在此页进行设置，完成后发送设置码即可"
        elif match_num == 0x400:
            in_code = cmd[3:]
            res = self.get_url_content(self.code_api+in_code)
            if isinstance(res, int):
                reply = "服务器错误：{}".format(res)
            else:
                try:
                    new_setting = json.loads(res)
                except json.JSONDecodeError:
                    reply = "服务器返回值异常"
                if new_setting.get("version", 0) != 2999:
                    reply = "设置码版本错误"
                else:
                    self.setting.update(new_setting["settings"])
                    self.save_settings()
                    reply = "设置成功"
        elif match_num == 0x500:
            # 旧代码不想改，封装一下。。
            in_code = cmd[2:]
            setting_old = setting.Setting(self.setting)
            if in_code.startswith("卡池"):
                reply = setting_old.URL["pool"]
            elif in_code.startswith("邮箱"):
                reply = setting_old.URL["mail"] + "1"
            elif in_code.startswith("AAAA"):
                reply = setting_old.set_AAAA(in_code[:3:-1], 1)
            elif in_code.startswith("AAAB"):
                reply = setting_old.set_AAAB(in_code[:3:-1])
            else:
                reply = "未知的设置"

        return {
            "reply": reply,
            "block": True
        }
