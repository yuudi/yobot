import random
import string
import time
from hashlib import sha256
from urllib.parse import urljoin

import peewee
from quart import (Quart, jsonify, make_response, redirect, request, session,
                   url_for)

from .templating import render_template


def _rand_string(n=8):
    return ''.join(
        random.choice(
            string.ascii_uppercase +
            string.ascii_lowercase +
            string.digits)
        for _ in range(n)
    )


class Login:
    Passive = True
    Active = False
    Request = True

    def __init__(self,
                 glo_setting,
                 database_model: peewee.Model,
                 *args, **kwargs):
        self.setting = glo_setting

        class User(database_model):
            uid = peewee.AutoField(primary_key=True)
            authority_group = peewee.IntegerField(default=100)
            qqid = peewee.BigIntegerField(index=True, null=True)
            nickname = peewee.TextField(null=True)
            clan_group_id = peewee.BigIntegerField(null=True)
            last_login_time = peewee.BigIntegerField(default=0)
            last_login_ipaddr = peewee.IPField(default='0.0.0.0')
            login_code = peewee.FixedCharField(max_length=6, null=True)
            login_code_available = peewee.BooleanField(default=False)
            login_code_expire_time = peewee.BigIntegerField(default=0)
            auth_cookie = peewee.FixedCharField(max_length=32, null=True)
            auth_cookie_expire_time = peewee.BigIntegerField(default=0)

        if not User.table_exists():
            User.create_table()

        self.User = User

    @staticmethod
    def match(cmd: str):
        if cmd == '登录':
            return 1
        return 0

    def execute(self, match_num: int, ctx: dict) -> dict:
        if ctx['message_type'] != 'private':
            return {
                'reply': '请私聊使用',
                'block': True
            }

        login_code = _rand_string(6)
        if ctx['user_id'] in self.setting['super-admin']:
            authority_group = 1
        else:
            authority_group = 100

        # 取出数据
        user = self.User.get_or_none(self.User.qqid == ctx['user_id'])
        if user is None:
            user = self.User(
                qqid=ctx['user_id'],
                nickname=ctx['sender']['nickname'],
                authority_group=authority_group,
            )
        user.login_code = login_code
        user.login_code_available = True
        user.login_code_expire_time = int(time.time())+60
        user.save()

        newurl = urljoin(self.setting['public_address'],
                         f'login/?uid={user.uid}&key={login_code}')
        reply = '请在一分钟内点击链接登录：'+newurl
        return {
            'reply': reply,
            'block': True
        }

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'login/'),
            methods=['GET'])
        async def yobot_login():
            uid = request.args.get('uid')
            key = request.args.get('key')
            callback_page = request.args.get('callback', url_for('yobot_user'))
            now = int(time.time())
            login_failure_reason = '登录失败'
            login_failure_advice = '请私聊机器人“{}登录”重新获取地址'.format(
                self.setting['preffix_string'] if self.setting['preffix_on'] else ''
            )
            if uid is not None and key is not None:
                user = self.User.get_or_none(self.User.uid == uid)
                if user is None or user.login_code != key:
                    # 登录码错误
                    login_failure_reason = '无效的登录地址'
                    login_failure_advice = '请检查登录地址是否完整'
                else:
                    if user.login_code_expire_time < now:
                        # 登录码正确但超时
                        login_failure_reason = '这个登录地址已过期'
                    if not user.login_code_available:
                        # 登录码正确但已被使用
                        login_failure_reason = '这个登录地址已被使用'
                    else:
                        # 登录码有效
                        new_key = _rand_string(32)                        
                        session['yobot_user'] = {
                            'uid': uid,
                            'authority_group': user.authority_group,
                            'nickname': user.nickname,
                            'clan_group_id': user.clan_group_id,
                            'last_login_time': user.last_login_time,
                            'last_login_ipaddr': user.last_login_ipaddr,
                        }
                        user.login_code_available = False
                        user.last_login_time = now
                        user.last_login_ipaddr = request.remote_addr
                        user.auth_cookie = sha256(new_key.encode()).hexdigest()
                        user.auth_cookie_expire_time = now+604800  # 7 days
                        user.save()

                        new_cookie = f'{uid}:{new_key}'
                        res = await make_response(redirect(callback_page))
                        res.set_cookie(
                            'yobot_login', new_cookie, max_age=604800)
                        return res
            # 未提供登录码 & 登录码错误
            if 'yobot_user' in session:
                # 会话未过期
                return redirect(callback_page)
            # 会话已过期
            auth_cookie = request.cookies.get('yobot_login')
            if auth_cookie is not None:
                # 有cookie
                s = auth_cookie.split(':')
                if len(s) == 2:
                    uid, auth = s
                    auth = sha256(auth.encode()).hexdigest()
                    user = self.User.get_or_none(self.User.uid == uid)
                    if user is not None and user.auth_cookie == auth:
                        if user.auth_cookie_expire_time > now:
                            # cookie有效
                            session['yobot_user'] = {
                                'uid': uid,
                                'authority_group': user.authority_group,
                                'nickname': user.nickname,
                                'clan_group_id': user.clan_group_id,
                                'last_login_time': user.last_login_time,
                                'last_login_ipaddr': user.last_login_ipaddr,
                            }
                            user.last_login_time = now
                            user.last_login_ipaddr = request.remote_addr
                            user.save()

                            return redirect(callback_page)
                        else:
                            # cookie正确但过期
                            login_failure_reason = '登录已过期'
            # 无cookie & cookie错误
            return await render_template(
                'login-failure.html',
                reason=login_failure_reason,
                advice=login_failure_advice,
            )

        @app.route(
            urljoin(self.setting['public_basepath'], 'user/'),
            methods=['GET'])
        async def yobot_user():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            return await render_template(
                'user.html',
                user=session['yobot_user'],
            )

        @app.route(
            urljoin(self.setting['public_basepath'], 'user/<int:uid>/'),
            methods=['GET'])
        async def yobot_user_info(uid):
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            if session['yobot_user']['uid'] == uid:
                visited_user_info = session['yobot_user']
            else:
                visited_user = self.User.get_or_none(self.User.uid == uid)
                if visited_user is None:
                    return '没有此用户', 404
                visited_user_info = {
                    'uid': uid,
                    'authority_group': visited_user.authority_group,
                    'nickname': visited_user.nickname,
                    'clan_group_id': visited_user.clan_group_id,
                    'last_login_time': visited_user.last_login_time,
                    'last_login_ipaddr': visited_user.last_login_ipaddr,
                }
            return await render_template(
                'user-info.html',
                user=session['yobot_user'],
                visited_user=visited_user_info,
            )

        @app.route(
            urljoin(self.setting['public_basepath'], 'user/<int:uid>/nickname/'),
            methods=['PUT'])
        async def yobot_user_info_nickname(uid):
            if 'yobot_user' not in session:
                return jsonify(code=10, message='未登录')
            user = session['yobot_user']
            if user['uid'] != uid and user['authority_group'] >= 100:
                return jsonify(code=11, message='权限不足')
            user_data = self.User.get_or_none(self.User.uid == uid)
            if user_data is None:
                return jsonify(code=20, message='用户不存在')
            new_setting = await request.get_json()
            if new_setting is None:
                return jsonify(code=30, message='消息体格式错误')
            new_nickname = new_setting.get('nickname')
            if new_nickname is None:
                return jsonify(code=32, message='消息体内容错误')
            user_data.nickname = new_nickname
            user_data.save()
            return jsonify(code=0, message='success')
