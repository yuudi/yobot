from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart
from typing import Dict, Any

from ybplugins.login import _rand_string, Login, _add_salt_and_hash

FRONT_END_SALT = "14b492a3-a40a-42fc-a236-e9a9307b47d2"


class PwdResetPlugin:
    Passive = True
    Active = False
    Request = True

    def __init__(self, glo_setting,
                 bot_api: Api, *args, **kwargs):
        self.login = Login(glo_setting, bot_api, *args, **kwargs)

    @staticmethod
    def match(cmd: str):
        cmd = cmd.split(' ')[0]
        if cmd in ['重置密码', '忘记密码']:
            return 1
        return 0

    def execute(self, ctx: dict):
        if not self.match(ctx["raw_message"]):
            return

        if ctx['message_type'] != 'private':
            return '请私聊使用'

        raw_pwd = _rand_string(8)

        user = self.login._get_or_create_user_model(ctx)
        pwd = _add_salt_and_hash(raw_pwd, FRONT_END_SALT)
        pwd = _add_salt_and_hash(pwd, user.salt)
        user.password = pwd
        user.save()

        reply = '您的密码已重置为：' + raw_pwd

        return reply
