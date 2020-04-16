"""
后台模式的实验性功能，验证后台交互的可行性
"""
import random
import string
import time
from urllib.parse import urljoin

from aiocqhttp.api import Api
from quart import Quart, jsonify, make_response, request

from .templating import render_template
from .ybdata import Admin_key


def _rand_string(n=8):
    return ''.join(
        random.choice(
            string.ascii_uppercase +
            string.ascii_lowercase +
            string.digits)
        for _ in range(n)
    )


class Marionette:
    Passive = True
    Active = False
    Request = True

    def __init__(self,
                 glo_setting,
                 bot_api: Api,
                 *args, **kwargs):
        self.setting = glo_setting
        self.api = bot_api

    def _gen_key(self):
        newkey = _rand_string(6)
        Admin_key.create(
            key=newkey,
            valid=True,
            key_used=False,
            cookie=_rand_string(32),
            create_time=int(time.time()),
        )
        newurl = urljoin(
            self.setting['public_address'],
            '{}marionette/?key={}'.format(self.setting['public_basepath'], newkey))
        return newurl

    @staticmethod
    def match(cmd: str):
        if cmd == '人偶':
            return 1
        return 0

    def execute(self, match_num: int, ctx: dict) -> dict:
        if ctx['user_id'] not in self.setting['super-admin']:
            return {
                'reply': '只有主人可以使用这个功能',
                'block': True
            }
        if ctx['message_type'] != 'private':
            return {
                'reply': '请私聊使用',
                'block': True
            }
        newurl = self._gen_key()
        reply = '点击链接开始使用我：'+newurl
        if self.setting['web_mode_hint']:
            reply += '\n\n如果连接无法打开，请参考https://gitee.com/yobot/yobot/blob/master/documents/usage/cannot-open-webpage.md'
        return {
            'reply': reply,
            'block': True
        }

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'marionette/'),
            methods=['GET'])
        async def yobot_marionette():
            new_cookie = None
            key_used = False
            key = request.args.get('key')
            if key is not None:
                user = Admin_key.get_or_none(Admin_key.key == key)
                if user is None:
                    return '403 Forbidden', 403
                if user.key_used:
                    key = None
                    key_used = True
                else:
                    user.key_used = True
                    user.save()
                    new_cookie = user.cookie
            if key is None:
                auth = request.cookies.get('yobot_auth')
                if auth is None:
                    if key_used:
                        return '链接已过期', 410
                    else:
                        return '403 Forbidden', 403
                user = Admin_key.get_or_none(Admin_key.cookie == auth)
                if user is None:
                    return '403 Forbidden', 403
            if not user.valid:
                return '登录已过期', 410

            res = await make_response(await render_template('marionette.html'))
            if new_cookie is not None:
                res.set_cookie('yobot_auth', new_cookie, max_age=604800)
            return res

        @app.route(
            urljoin(self.setting['public_basepath'], 'marionette/api/'),
            methods=['POST'])
        async def yobot_marionette_api():
            auth = request.cookies.get('yobot_auth')
            if auth is None:
                return '403 Forbidden', 403
            user = Admin_key.get_or_none(Admin_key.cookie == auth)
            if user is None:
                return '403 Forbidden', 403
            req = await request.get_json()
            if req is None:
                return '406 Not Acceptable', 406
            try:
                await self.api.send_msg(**req)
            except Exception as e:
                return jsonify(code=1, message=str(e))
            return jsonify(code=0, message='success')
