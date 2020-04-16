import random
import string
import time
from hashlib import sha256
from urllib.parse import urljoin

from aiocqhttp.api import Api
from quart import (Quart, jsonify, make_response, redirect, request, session,
                   url_for)

from .templating import render_template
from .ybdata import User


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
                 bot_api: Api,
                 *args, **kwargs):
        self.setting = glo_setting
        self.api = bot_api

    @staticmethod
    def match(cmd: str):
        if cmd == '登录' or cmd == '登陆':
            return 1
        return 0

    def execute(self, match_num: int, ctx: dict) -> dict:
        if ctx['message_type'] != 'private':
            return {
                'reply': '请私聊使用',
                'block': True
            }

        login_code = _rand_string(6)
        if not self.setting['super-admin']:
            authority_group = 1
            self.setting['super-admin'].append(ctx['user_id'])
        elif ctx['user_id'] in self.setting['super-admin']:
            authority_group = 1
        else:
            authority_group = 100

        # 取出数据
        user = User.get_or_create(
            qqid = ctx['user_id'],
            defaults={
                'nickname': ctx['sender']['nickname'],
                'authority_group': authority_group,
            }
        )[0]
        user.login_code = login_code
        user.login_code_available = True
        user.login_code_expire_time = int(time.time())+60
        user.save()

        newurl = urljoin(
            self.setting['public_address'],
            '{}login/?qqid={}&key={}'.format(
                self.setting['public_basepath'],
                user.qqid,
                login_code,
            )
        )
        reply = '请在一分钟内点击链接登录：'+newurl
        if self.setting['web_mode_hint']:
            reply += '\n\n如果连接无法打开，请参考https://gitee.com/yobot/yobot/blob/master/documents/usage/cannot-open-webpage.md'
        return {
            'reply': reply,
            'block': True
        }

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'login/'),
            methods=['GET'])
        async def yobot_login():
            qqid = request.args.get('qqid')
            key = request.args.get('key')
            callback_page = request.args.get('callback', url_for('yobot_user'))
            now = int(time.time())
            login_failure_reason = '登录失败'
            login_failure_advice = '请私聊机器人“{}登录”重新获取地址'.format(
                self.setting['preffix_string'] if self.setting['preffix_on'] else ''
            )
            if qqid is not None and key is not None:
                user = User.get_or_none(User.qqid == qqid)
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
                        session['yobot_user'] = qqid
                        session['csrf_token'] = _rand_string(16)
                        session['last_login_time'] = user.last_login_time
                        session['last_login_ipaddr'] = user.last_login_ipaddr
                        user.login_code_available = False
                        user.last_login_time = now
                        user.last_login_ipaddr = request.headers.get(
                            'X-Real-IP', request.remote_addr)
                        user.auth_cookie = sha256(
                            (new_key+user.salt).encode()).hexdigest()
                        user.auth_cookie_expire_time = now+604800  # 7 days
                        user.save()

                        new_cookie = f'{qqid}:{new_key}'
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
                    qqid, auth = s
                    user = User.get_or_none(User.qqid == qqid)
                    if user is None:
                        login_failure_reason = '用户不存在'
                        login_failure_advice = '请先加入一个公会'
                    else:
                        auth = sha256((auth+user.salt).encode()).hexdigest()
                        if user.auth_cookie == auth:
                            if user.auth_cookie_expire_time > now:
                                # cookie有效
                                session['yobot_user'] = qqid
                                session['csrf_token'] = _rand_string(16)
                                session['last_login_time'] = user.last_login_time
                                session['last_login_ipaddr'] = user.last_login_ipaddr
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
            endpoint='yobot_user',
            methods=['GET'])
        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/'),
            endpoint='yobot_admin',
            methods=['GET'])
        async def yobot_user():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            return await render_template(
                'user.html',
                user=User.get_by_id(session['yobot_user']),
            )

        @app.route(
            urljoin(self.setting['public_basepath'], 'user/<int:qqid>/'),
            methods=['GET'])
        async def yobot_user_info(qqid):
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            if session['yobot_user'] == qqid:
                visited_user_info = User.get_by_id(session['yobot_user'])
            else:
                visited_user = User.get_or_none(User.qqid == qqid)
                if visited_user is None:
                    return '没有此用户', 404
                visited_user_info = visited_user
            return await render_template(
                'user-info.html',
                user=visited_user_info,
                visitor=User.get_by_id(session['yobot_user']),
            )

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'user/<int:qqid>/nickname/'),
            methods=['PUT'])
        async def yobot_user_info_nickname(qqid):
            if 'yobot_user' not in session:
                return jsonify(code=10, message='未登录')
            user = User.get_by_id(session['yobot_user'])
            if user.qqid != qqid and user.authority_group >= 100:
                return jsonify(code=11, message='权限不足')
            user_data = User.get_or_none(User.qqid == qqid)
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
