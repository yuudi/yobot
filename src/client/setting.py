# coding=utf-8

import base64
import hashlib
import json
import os

import requests


class Setting:
    URL = {
        'shorten': 'http://io.yobot.monster/go/yourls-api.php',
        'mail': 'http://io.yobot.monster/v2/mail-conf/?qq='}

    def __init__(self, glo_setting: dict):
        self.setting = glo_setting
        self.mailfile = os.path.join(glo_setting["dirname"], "mailconf.json")

    @staticmethod
    def match(cmd: str) -> int:
        if cmd.startswith("设置"):
            return 1
        else:
            return 0

    # def excute(self, match_num: int, msg: dcit) -> dict:
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
        elif cmd.startswith('AAAA'):
            cmd = cmd[:3:-1]
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
                reply = '设置成功'
        else:
            reply = '请发送你要设置的项目，目前可设置的有：\n#设置邮箱'
        return reply
        # return {
        #     "reply": reply
        #     "block": True
        # }
