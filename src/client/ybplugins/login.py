import random
import string
import time
import re
from hashlib import sha256
from urllib.parse import urljoin

from aiocqhttp.api import Api
from quart import (Quart, jsonify, make_response, redirect, request, session,
                   url_for, Response)
from typing import Union, Coroutine

from .templating import render_template
from .ybdata import User


EXPIRED_TIME = 7 * 24 * 60 * 60  # 7 days
LOGIN_AUTH_COOKIE_NAME = 'yobot_login'


def _rand_string(n=8):
    return ''.join(
        random.choice(
            string.ascii_uppercase +
            string.ascii_lowercase +
            string.digits)
        for _ in range(n)
    )


class ExceptionWithAdvice(Exception):

    def __init__(self, reason: str, advice=''):
        super(ExceptionWithAdvice, self).__init__(reason)
        self.reason = reason
        self.advice = advice


def _add_salt_and_hash(raw: str, salt: str):
    return sha256((raw + salt).encode()).hexdigest()


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
        cmd = cmd.split(' ')[0]
        if cmd in ['登录', '登陆']:
            return 1
        elif cmd in ['验证', '验证码']:
            return 2
        elif cmd in ['设密码', '密码', '改密码', '设置密码', '修改密码', '重置密码', '找回密码']:
            return 3
        return 0

    def execute(self, match_num: int, ctx: dict) -> dict:
        if ctx['message_type'] != 'private':
            return {
                'reply': '请私聊使用',
                'block': True
            }

        if match_num == 3:
            return self._set_pwd(ctx)

        login_code = _rand_string(6)

        user = self._get_or_create_user_model(ctx)
        user.login_code = login_code
        user.login_code_available = True
        user.login_code_expire_time = int(time.time())+60
        user.save()

        if match_num == 1:
            # 链接登录
            newurl = urljoin(
                self.setting['public_address'],
                '{}login/?qqid={}&key={}'.format(
                    self.setting['public_basepath'],
                    user.qqid,
                    login_code,
                )
            )
            reply = '请在一分钟内点击链接登录：'+newurl

        elif match_num == 2:
            # 验证码登录
            reply = f'您的验证码为【{login_code}】，请在一分钟内使用。'
        else:
            raise Exception(f"发现未设定的match状态：{match_num}")

        if self.setting['web_mode_hint']:
            reply += '\n\n如果连接无法打开，请参考https://gitee.com/yobot/yobot/blob/master/documents/usage/cannot-open-webpage.md'

        return {
            'reply': reply,
            'block': True
        }

    def _get_or_create_user_model(self, ctx: dict) -> User:
        if not self.setting['super-admin']:
            authority_group = 1
            self.setting['super-admin'].append(ctx['user_id'])
        elif ctx['user_id'] in self.setting['super-admin']:
            authority_group = 1
        else:
            authority_group = 100

        # 取出数据
        return User.get_or_create(
            qqid = ctx['user_id'],
            defaults={
                'nickname': ctx['sender']['nickname'],
                'authority_group': authority_group,
            }
        )[0]

    @staticmethod
    def _validate_pwd(pwd: str) -> Union[str, bool]:
        """
        验证用户密码是否合乎硬性条件
        :return: 合法返回True，不合法返回原因
        """
        if len(pwd) < 8:
            return '密码至少需要8位'
        char_regex = re.compile(r'[0-9a-zA-Z!\-\\/@#$%^&*?_.()+=\[\]{}|;:<>`~]+')
        if not char_regex.match(pwd):
            return '密码不能含有中文或密码中含有特殊符号'
        return True

    def _set_pwd(self, ctx: dict) -> dict:
        """
        检查并设置密码
        :return: 返回回复格式的设置结果
        """
        cmd = ctx['raw_message']
        cmds = cmd.split(" ")
        if len(cmds) < 2:
            return {
                'reply': '请在命令后输入密码',
                'block': True
            }
        if len(cmds) > 2:
            return {
                'reply': '密码中不能包含空格',
                'block': True
            }
        pwd = cmds[1]
        if self._validate_pwd(pwd) != True:  # 这里不能简写，因为可能会返回str
            return {
                'reply': self._validate_pwd(pwd),  # 我需要海象表达式！
                'block': True
            }
        
        user = self._get_or_create_user_model(ctx)
        user.password = _add_salt_and_hash(pwd, user.salt)
        user.save()

        return {
            'reply': '密码设置成功！',
            'block': True
        }

    def _get_prefix(self):
        return self.setting['preffix_string'] if self.setting['preffix_on'] else ''

    def _check_pwd(self, user: User, pwd: str) -> bool:
        """
        检查是否设置密码且密码是否正确，
        :return: 成功返回True，失败抛出异常。
        """
        if not user or not user.password or not user.salt:
            raise ExceptionWithAdvice(
                'QQ号错误 或 您尚未设置密码',
                f'请私聊机器人“{self._get_prefix()}密码 [您的密码]”设置'
            )
        if not user.password == _add_salt_and_hash(pwd, user.salt):
            raise ExceptionWithAdvice(
                '您的密码不正确',
                f'如果忘记密码，请私聊机器人“{self._get_prefix()}密码 [您的密码]”修改'
            )
        return True

    def _check_key(self, user: User, key: str) -> Union[bool, str]:
        """
        检查登录码是否正确且在有效期内
        :return: 成功返回True，失败抛出异常
        """
        now = int(time.time())
        if user is None or user.login_code != key:
            # 登录码错误
            raise ExceptionWithAdvice(
                '无效的登录地址',
                f'请检查登录地址是否完整且为最新。'
            )
        if user.login_code_expire_time < now:
            # 登录码正确但超时
            raise ExceptionWithAdvice(
                '这个登录地址已过期',
                f'私聊机器人“{self._get_prefix()}登录”获取新登录地址'
            )
        if not user.login_code_available:
            # 登录码正确但已被使用
            raise ExceptionWithAdvice(
                '这个登录地址已被使用',
                f'私聊机器人“{self._get_prefix()}登录”获取新登录地址'
            )
        return True

    def _recall_from_cookie(self) -> User:
        """
        检测cookie中的登录状态是否正确，如果cookie有误 会抛出异常
        :return User: 返回找回的user对象
        """
        auth_cookie = request.cookies.get(LOGIN_AUTH_COOKIE_NAME)
        advice = f'请私聊机器人"{self._get_prefix()}登录"或重新登录'
        if not auth_cookie:
            raise ExceptionWithAdvice('登录已过期', advice)
        s = auth_cookie.split(':')
        if len(s) != 2:
            raise ExceptionWithAdvice('Cookie异常', advice)
        qqid, auth = s

        user = User.get_or_none(User.qqid == qqid)
        advice = f'请先加入一个公会 或 私聊机器人"{self._get_prefix()}登录"'
        if user is None:
            # 有有效Cookie但是数据库没有，怕不是删库跑路了
            raise ExceptionWithAdvice('用户不存在', advice)
        if user.auth_cookie != _add_salt_and_hash(auth, user.salt):
            raise ExceptionWithAdvice('Cookie异常', advice)
        now = int(time.time())
        if user.auth_cookie_expire_time < now:
            raise ExceptionWithAdvice('登录已过期', advice)
        return user

    @staticmethod
    def _set_auth_info(user: User, res: Response = None, save_user=True):
        """
        为某用户设置session中的授权信息
        并自动修改中的上次登录的信息
        :param user: 用户模型
        :param save_user: 是否自动执行user.save()
        :param res: 如果需要自动更新cookie，请传入返回的response
        """
        now = int(time.time())
        session['yobot_user'] = user.qqid
        session['csrf_token'] = _rand_string(16)
        session['last_login_time'] = user.last_login_time
        session['last_login_ipaddr'] = user.last_login_ipaddr
        user.last_login_time = now
        user.last_login_ipaddr = request.headers.get(
            'X-Real-IP', request.remote_addr)
        if res:
            new_key = _rand_string(32)
            user.auth_cookie = _add_salt_and_hash(new_key, user.salt)
            user.auth_cookie_expire_time = now + EXPIRED_TIME
            new_cookie = f'{user.qqid}:{new_key}'
            res.set_cookie(LOGIN_AUTH_COOKIE_NAME, new_cookie, max_age=EXPIRED_TIME)
        if save_user:
            user.save()

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'login/'),
            methods=['GET', 'POST'])
        async def yobot_login():
            prefix = self.setting['preffix_string'] if self.setting['preffix_on'] else ''
            if request.method == "POST":
                form = await request.form

            def get_params(k: str):
                return request.args.get(k) \
                    if request.method == "GET" \
                    else (form and k in form and form[k])

            try:
                qqid = get_params('qqid')
                key = get_params('key')
                pwd = get_params('pwd')
                callback_page = get_params('callback')

                if not qqid and not callback_page:
                    # 普通登录
                    return await render_template(
                        'login.html',
                        advice=f'请私聊机器人“{self._get_prefix()}登录”获取登录地址 '
                               f'或 私聊机器人“{self._get_prefix()}密码 [您的密码]”设置登录密码',
                        prefix=self._get_prefix()
                    )

                if callback_page and not qqid:
                    # 可能用于用cookie寻回session

                    if 'yobot_user' in session:
                        # 会话未过期
                        return redirect(callback_page)

                    user = self._recall_from_cookie()
                    self._set_auth_info(user)
                    return redirect(callback_page)

                if not key and not pwd:
                    raise ExceptionWithAdvice("无效的登录地址", "请检查登录地址是否完整")

                user = User.get_or_none(User.qqid == qqid)
                if key:
                    self._check_key(user, key)
                if pwd:
                    self._check_pwd(user, pwd)

                res = await make_response(redirect(callback_page or url_for('yobot_user')))
                self._set_auth_info(user, res, save_user=False)
                user.login_code_available = False
                user.save()
                return res

            except ExceptionWithAdvice as e:
                return await render_template(
                    'login.html',
                    reason=e.reason,
                    advice=e.advice or f'请私聊机器人“{self._get_prefix()}登录”获取登录地址 '
                                       f'或 私聊机器人“{self._get_prefix()}密码 [您的密码]”设置登录密码',
                    prefix=prefix
                )

        @app.route(
            urljoin(self.setting['public_basepath'], 'logout/'),
            methods=['GET', 'POST'])
        async def yobot_logout():
            session.clear()
            res = await make_response(redirect(url_for('yobot_login')))
            res.delete_cookie(LOGIN_AUTH_COOKIE_NAME)
            return res

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
