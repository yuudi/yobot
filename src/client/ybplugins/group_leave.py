from typing import Any, Dict, Union

from aiocqhttp.api import Api
from .web_util import rand_string


class GroupLeave:
    def __init__(self,
                 glo_setting: Dict[str, Any],
                 bot_api: Api,
                 *args, **kwargs):
        self.setting = glo_setting
        self.api = bot_api
        self.verification = {}

    async def execute_async(self, ctx: Dict[str, Any]):
        cmd = ctx['raw_message']
        if cmd.startswith('退出此群'):
            if ctx['message_type'] != 'group':
                return '此功能仅可用于群聊'
            if ctx['sender']['role'] == 'member':
                return '只有群管理员可以这么做'
            code = cmd[4:]
            if code == self.verification.get(ctx['group_id']):
                await self.api.send_group_msg(
                    group_id=ctx['group_id'],
                    message='正在退群',
                )
                await self.api.set_group_leave(
                    group_id=ctx['group_id'],
                    is_dismiss=False,
                )
            else:
                code = rand_string(4)
                self.verification[ctx['group_id']] = code
                return f'警告：如果你确定要执行退群，请发送“退出此群{code}”'
