# coding=utf-8

import base64
import hashlib
import json
import os

import requests


class Setting:
    URL = {
        'shorten': 'http://io.yobot.monster/go/yourls-api.php',
        'pool': 'http://io.yobot.monster/go/pool',
        'mail': 'http://io.yobot.monster/v2/mail-conf/?qq='}

    def __init__(self, glo_setting: dict):
        self.setting = glo_setting
        self.mailfile = os.path.join(glo_setting["dirname"], "mailconf.json")
        self.poolfile = os.path.join(glo_setting["dirname"], "pool.json5")

    @staticmethod
    def match(cmd: str) -> int:
        if cmd.startswith("设置"):
            return 1
        else:
            return 0

    def excute(self, match_num: int, msg: dict) -> dict:
        cmd = msg['raw_message'][2:]
        qqid = msg['sender']['user_id']
        if cmd == '邮箱':
            data = {
                'signature': 'b7b55a841d',
                'action': 'shorturl',
                'url': self.URL['mail'] + str(qqid),
                'format': 'simple'
            }
            resp = requests.post(self.URL['shorten'], data=data)
            if resp.status_code == 200:
                url = resp.text
            else:
                url = self.URL['mail'] + str(qqid)
            reply = '请在此界面设置，然后将设置码发回群里\n' + url
        elif cmd == '卡池':
            reply = '请在此界面设置，然后将设置码发回群里\n' + self.URL['pool']
        elif cmd.startswith('AAAA'):
            reply = self.set_AAAA(cmd[:3:-1], qqid)
        elif cmd.startswith('AAAB'):
            reply = self.set_AAAB(cmd[:3:-1])
        else:
            reply = ("请发送你要设置的项目，目前可设置的有：\n"
                     "#设置邮箱\n#设置卡池")
        return reply
        # return {
        #     "reply": reply
        #     "block": True
        # }

    def set_AAAA(self, cmd: str, qqid: int) -> str:
        while cmd.startswith('='):
            cmd = cmd[1:]+'='
        try:
            raw = base64.b64decode(cmd)
            confirm = raw[:32].decode()
            data = raw[32:]
            md5 = hashlib.md5(data)
            assert confirm == md5.hexdigest()
            config = json.loads(data.decode())
        except:
            return '设置码不完整，请检查'
        if config['q'] != qqid:
            return '身份错误'
        if not os.path.exists(self.mailfile):
            return '未初始化'
        if config['s'] == '':
            config['s'] = 'smtp.' + config['m'].split('@')[1]
        if config['n'] == '':
            config['n'] = config['m']
        with open(self.mailfile, "r+") as f:
            mailconf = json.load(f)
            mailconf['sender'] = {
                "host": config['s'],
                "user": config['m'],
                "pswd": config['p'],
                "sender": config['n']
            }
            f.seek(0)
            f.truncate()
            json.dump(mailconf, f, indent=2)
        return '设置成功'

    def set_AAAB(self, cmd: str) -> str:
        while cmd.startswith('='):
            cmd = cmd[1:]+'='
        try:
            raw = base64.b64decode(cmd)
            config = json.loads(raw.decode())
        except:
            return '设置码不完整，请检查'
        config["info"] = {"name": "自定义卡池"}
        with open(self.poolfile, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return '设置成功'
