import random
import string
import time
from urllib.parse import urljoin

import peewee
from quart import Quart, make_response, request, send_from_directory, jsonify, url_for

from .templating import render_template, static_folder


def rand_string(n=8):
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
                 database_model: peewee.Model,
                 send_msg_func,
                 *args, **kwargs):
        self.setting = glo_setting
        self.public_basepath = glo_setting['public_basepath']
        self.send_msg = send_msg_func
        Databasemodel = database_model

        class Admin_key(Databasemodel):
            key = peewee.TextField(primary_key=True)
            valid = peewee.BooleanField()
            key_used = peewee.BooleanField()
            cookie = peewee.TextField(index=True)
            create_time = peewee.TimestampField()

        if not Admin_key.table_exists():
            Admin_key.create_table()

        self.Data = Admin_key

    def _gen_key(self):
        newkey = rand_string(6)
        self.Data.create(
            key=newkey,
            valid=True,
            key_used=False,
            cookie=rand_string(32),
            create_time=int(time.time()),
        )
        newurl = urljoin(
            self.setting['public_addr'], 'marionette?key='+newkey)
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
        return {
            'reply': reply,
            'block': True
        }

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'marionette'),
            methods=['GET'])
        async def yobot_marionette():
            new_cookie = None
            key_used = False
            key = request.args.get('key')
            if key is not None:
                user = self.Data.get_or_none(self.Data.key == key)
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
                user = self.Data.get_or_none(self.Data.cookie == auth)
                if user is None:
                    return '403 Forbidden', 403
            if not user.valid:
                return '登录已过期', 410

            res = await make_response(await render_template(
                'marionette.html',
                jsfile=url_for('yobot_static', filename='marionette.js'),
                api_path=url_for('yobot_marionette_api')))
            if new_cookie is not None:
                res.set_cookie('yobot_auth', new_cookie, max_age=604800)
            return res

        @app.route(
            urljoin(self.setting['public_basepath'], 'marionette/api'),
            methods=['POST'])
        async def yobot_marionette_api():
            auth = request.cookies.get('yobot_auth')
            if auth is None:
                return '403 Forbidden', 403
            user = self.Data.get_or_none(self.Data.cookie == auth)
            if user is None:
                return '403 Forbidden', 403
            req = await request.get_json()
            if req is None:
                return '406 Not Acceptable', 406
            try:
                await self.send_msg(**req)
            except Exception as e:
                return jsonify(code=1, message=str(e))
            return jsonify(code=0, message='success')
