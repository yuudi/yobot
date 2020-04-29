'''
自定义功能：

在这里可以编写自定义的功能，
编写完毕后记得 git commit，
（只接收pcr相关功能，最好发到GitHub，我不怎么看Gitee）

这个模块只是为了快速编写小功能，如果想编写完整插件可以使用：
https://github.com/richardchien/python-aiocqhttp
或者
https://github.com/richardchien/nonebot
'''

import asyncio
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart

from ybplugins.login import _rand_string, _add_salt_and_hash, Login

FRONT_END_SALT = "14b492a3-a40a-42fc-a236-e9a9307b47d2"


class Custom:
    Passive = True
    Active = False
    Request = True

    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 app: Quart,
                 bot_api: Api,
                 *args, **kwargs):
        '''
        初始化，只在启动时执行一次

        参数：
            glo_setting 包含所有设置项，具体见default_config.json
            bot_api 是调用机器人API的接口，具体见<https://python-aiocqhttp.cqp.moe/>
            scheduler 是与机器人一同启动的AsyncIOScheduler实例
            app 是机器人后台Quart服务器实例
        '''
        # 注意：这个类加载时，asyncio事件循环尚未启动，且bot_api没有连接
        # 此时不要调用bot_api，如需初始化请使用api_init
        # 此时没有running_loop，不要直接使用await或asyncio.creat_task

        # 如果需要使用，请注释掉下面一行
        # return

        self.setting = glo_setting
        self.api = bot_api
        self.login = Login(glo_setting, bot_api, *args, **kwargs)

        # # 注册定时任务，详见apscheduler文档
        # @scheduler.scheduled_job('cron', hour=8)
        # async def good_morning():
        #     await bot_api.send_group_msg(group_id=123456, message='早上好')

        # # 注册web路由，详见flask与quart文档
        # @app.route('/is-bot-running', methods=['GET'])
        # async def check_bot():
        #     return 'yes, bot is running'

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
