import json
import os
import time
from hashlib import sha256
from typing import Dict, Union
from urllib.parse import urljoin

from aiocqhttp.api import Api
from apscheduler.triggers.cron import CronTrigger
from quart import (Quart, Response, jsonify, make_response, redirect, request,
                   send_from_directory, session, url_for)

from .templating import render_template, template_folder
from .web_util import rand_string
from .ybdata import MAX_TRY_TIMES, Clan_group, Clan_member, User, User_login

EXPIRED_TIME = 7 * 24 * 60 * 60  # 7 days
LOGIN_AUTH_COOKIE_NAME = 'yobot_login'
# this need be same with static/password.js
FRONTEND_SALT = '14b492a3-a40a-42fc-a236-e9a9307b47d2'


class ExceptionWithAdvice(RuntimeError):

    def __init__(self, reason: str, advice=''):
        super(ExceptionWithAdvice, self).__init__(reason)
        self.reason = reason
        self.advice = advice


def _add_salt_and_hash(raw: str, salt: str):
    return sha256((raw + salt).encode()).hexdigest()


class Login:
    Passive = True
    Active = True
    Request = True

    def __init__(self,
                 glo_setting,
                 bot_api: Api,
                 *args, **kwargs):
        self.setting = glo_setting
        self.api = bot_api

    def jobs(self):
        trigger = CronTrigger(hour=5)
        return ((trigger, self.drop_expired_logins),)

    def drop_expired_logins(self):
        # 清理过期cookie
        now = int(time.time())
        User_login.delete().where(
            User_login.auth_cookie_expire_time < now,
        ).execute()

    @staticmethod
    def match(cmd: str):
        cmd = cmd.split(' ')[0]
        if cmd in ['登录', '登陆']:
            return 1
        if cmd == '重置密码':
            return 3
        return 0

    def execute(self, match_num: int, ctx: dict) -> dict:
        if ctx['message_type'] != 'private':
            return {
                'reply': '请私聊使用',
                'block': True
            }
        reply = ''
        if match_num == 1:
            reply = self._get_login_code_url(ctx)
            if self.setting['web_mode_hint']:
                reply += '\n\n如果无法打开，请仔细阅读教程中《链接无法打开》的说明'
        elif match_num == 3:
            reply = f'您的临时密码是：{self._reset_pwd(ctx)}'
        else:
            assert False, f"没有实现匹配码{match_num}对应的操作"

        return {
            'reply': reply,
            'block': True
        }

    def _get_or_create_user_model(self, ctx: dict) -> User:
        first_admin_login = False
        if not self.setting['super-admin']:
            first_admin_login = True
            authority_group = 1
            self.setting['super-admin'].append(ctx['user_id'])
            save_setting = self.setting.copy()
            del save_setting['dirname']
            del save_setting['verinfo']
            config_path = os.path.join(
                self.setting['dirname'], 'yobot_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(save_setting, f, indent=4)
        elif ctx['user_id'] in self.setting['super-admin']:
            authority_group = 1
        else:
            authority_group = 100

        # 取出数据
        user = User.get_or_create(
            qqid=ctx['user_id'],
            defaults={
                'nickname': ctx['sender']['nickname'],
                'authority_group': authority_group,
                'privacy': 0
            }
        )[0]
        if first_admin_login:
            user.authority_group = 1
        return user

    def _get_login_code_url(self, ctx: Dict) -> str:
        """
        获取新的登录链接
        :param ctx: 本次消息事件的ctx对象
        :return: 登录链接
        """
        login_code = rand_string(6)

        user = self._get_or_create_user_model(ctx)
        user.login_code = login_code
        user.login_code_available = True
        user.login_code_expire_time = int(time.time()) + 60
        user.deleted = False
        user.save()

        # 链接登录
        url = urljoin(
            self.setting['public_address'],
            '{}login/c/#qqid={}&key={}'.format(
                self.setting['public_basepath'],
                user.qqid,
                login_code,
            )
        )
        return url

    # def _reset_privacy(self, ctx: Dict) -> str:
    #     """
    #     重置用户的登录次数
    #     :param ctx: 本次消息事件的ctx对象
    #     :return:
    #     """
    #     user = self._get_or_create_user_model(ctx)
    #     user.privacy = 0
    #     user.deleted = False
    #     user.save()
    #     return "您的账号锁定已解除"

    def _reset_pwd(self, ctx: Dict) -> str:
        """
        随机生成一个密码
        :param ctx: 本次消息事件的ctx对象
        :return: 新的密码
        """
        raw_pwd = rand_string(8)

        user = self._get_or_create_user_model(ctx)
        frontend_salted_pwd = _add_salt_and_hash(
            raw_pwd + str(ctx['user_id']), FRONTEND_SALT)
        user.password = _add_salt_and_hash(frontend_salted_pwd, user.salt)
        user.privacy = 0
        user.deleted = False
        user.must_change_password = True
        user.save()
        # 踢掉过去的登录
        User_login.delete().where(
            User_login.qqid == ctx['user_id'],
        ).execute()
        return raw_pwd

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
                f'请私聊机器人“{self._get_prefix()}登录”后，再次选择[修改密码]修改'
            )
        if user.privacy >= MAX_TRY_TIMES:
            raise ExceptionWithAdvice(
                '您的密码错误次数过多，账号已锁定',
                f'请私聊机器人“{self._get_prefix()}重置密码”后，重新登录'
            )
        if not user.password == _add_salt_and_hash(pwd, user.salt):
            user.privacy += 1  # 密码错误次数+1
            user.save()
            raise ExceptionWithAdvice(
                '您的密码不正确',
                f'如果忘记密码，请私聊机器人“{self._get_prefix()}登录”后，再次选择[修改密码]修改，'
                f'或私聊机器人“{self._get_prefix()}重置密码”'
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

    def _recall_from_cookie(self, auth_cookie) -> User:
        """
        检测cookie中的登录状态是否正确，如果cookie有误 会抛出异常
        :return User: 返回找回的user对象
        """
        advice = f'请私聊机器人“{self._get_prefix()}登录”或重新登录'
        if not auth_cookie:
            raise ExceptionWithAdvice('登录已过期', advice)
        s = auth_cookie.split(':')
        if len(s) != 2:
            raise ExceptionWithAdvice('Cookie异常', advice)
        qqid, auth = s

        user = User.get_or_none(User.qqid == qqid)
        advice = f'请先加入一个公会 或 私聊机器人“{self._get_prefix()}登录”'
        if user is None:
            # 有有效Cookie但是数据库没有，怕不是删库跑路了
            raise ExceptionWithAdvice('用户不存在', advice)
        if user.deleted:
            raise ExceptionWithAdvice('用户已被删除', '请咨询管理员')
        salty_cookie = _add_salt_and_hash(auth, user.salt)
        userlogin = User_login.get_or_none(
            qqid=qqid,
            auth_cookie=salty_cookie,
        )
        if userlogin is None:
            raise ExceptionWithAdvice('Cookie异常', advice)
        now = int(time.time())
        if userlogin.auth_cookie_expire_time < now:
            raise ExceptionWithAdvice('登录已过期', advice)

        userlogin.last_login_time = now
        userlogin.last_login_ipaddr = request.headers.get(
            'X-Real-IP', request.remote_addr)
        userlogin.save()

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
        session['csrf_token'] = rand_string(16)
        session['last_login_time'] = user.last_login_time
        session['last_login_ipaddr'] = user.last_login_ipaddr
        user.last_login_time = now
        user.last_login_ipaddr = request.headers.get(
            'X-Real-IP', request.remote_addr)
        if res:
            new_key = rand_string(32)
            userlogin = User_login.create(
                qqid=user.qqid,
                auth_cookie=_add_salt_and_hash(new_key, user.salt),
                auth_cookie_expire_time=now + EXPIRED_TIME,
            )
            new_cookie = f'{user.qqid}:{new_key}'
            res.set_cookie(LOGIN_AUTH_COOKIE_NAME,
                           new_cookie, max_age=EXPIRED_TIME)
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

            def get_params(k: str) -> str:
                return request.args.get(k) \
                    if request.method == "GET" \
                    else (form and k in form and form[k])

            try:
                qqid = get_params('qqid')
                key = get_params('key')
                pwd = get_params('pwd')
                callback_page = get_params('callback') or url_for('yobot_user')
                auth_cookie = request.cookies.get(LOGIN_AUTH_COOKIE_NAME)

                if not qqid and not auth_cookie:
                    # 普通登录
                    return await render_template(
                        'login.html',
                        advice=f'请私聊机器人“{self._get_prefix()}登录”获取登录地址 ',
                        prefix=self._get_prefix()
                    )

                key_failure = None
                if qqid:
                    user = User.get_or_none(User.qqid == qqid)
                    if key:
                        try:
                            self._check_key(user, key)
                        except ExceptionWithAdvice as e:
                            if auth_cookie:
                                qqid = None
                                key_failure = e
                            else:
                                raise e from e
                    if pwd:
                        self._check_pwd(user, pwd)

                if auth_cookie and not qqid:
                    # 可能用于用cookie寻回session

                    if 'yobot_user' in session:
                        # 会话未过期
                        return redirect(callback_page)
                    try:
                        user = self._recall_from_cookie(auth_cookie)
                    except ExceptionWithAdvice as e:
                        if key_failure is not None:
                            raise key_failure
                        else:
                            raise e from e
                    self._set_auth_info(user)
                    if user.must_change_password:
                        callback_page = url_for('yobot_reset_pwd')
                    return redirect(callback_page)

                if not key and not pwd:
                    raise ExceptionWithAdvice("无效的登录地址", "请检查登录地址是否完整")

                if user.must_change_password:
                    callback_page = url_for('yobot_reset_pwd')
                res = await make_response(redirect(callback_page))
                self._set_auth_info(user, res, save_user=False)
                user.login_code_available = False
                user.save()
                return res

            except ExceptionWithAdvice as e:
                return await render_template(
                    'login.html',
                    reason=e.reason,
                    advice=e.advice or f'请私聊机器人“{self._get_prefix()}登录”获取登录地址 ',
                    prefix=prefix
                )

        @app.route(
            urljoin(self.setting['public_basepath'], 'login/c/'),
            methods=['GET', 'POST'])
        async def yobot_login_code():
            return await send_from_directory(template_folder, "login-code.html")

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
            clan_groups = Clan_member.select(
                Clan_member.group_id,
                Clan_group.group_name,
            ).join(
                Clan_group,
                on=(Clan_member.group_id == Clan_group.group_id),
                attr='info',
            ).where(
                Clan_member.qqid == session['yobot_user']
            )
            return await render_template(
                'user.html',
                user=User.get_by_id(session['yobot_user']),
                clan_groups=[{
                    'group_id': g.group_id,
                    'group_name': (getattr(getattr(g, 'info', None), 'group_name', None) or g.group_id)
                } for g in clan_groups],
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

        @app.route(
            urljoin(self.setting['public_basepath'], 'user/reset-password/'),
            methods=['GET', 'POST'])
        async def yobot_reset_pwd():
            try:
                if 'yobot_user' not in session:
                    return redirect(url_for('yobot_login', callback=request.path))
                if request.method == "GET":
                    return await render_template('password.html')

                qq = session['yobot_user']
                user = User.get_or_none(User.qqid == qq)
                if user is None:
                    raise Exception("请先加公会")
                form = await request.form
                pwd = form["pwd"]
                # self._validate_pwd(pwd)
                user.password = _add_salt_and_hash(pwd, user.salt)
                user.privacy = 0
                user.must_change_password = False
                user.save()
                # 踢掉过去的登录
                User_login.delete().where(
                    User_login.qqid == qq,
                ).execute()
                return await render_template(
                    'password.html',
                    success="密码设置成功",
                )
            except Exception as e:
                return await render_template(
                    'password.html',
                    error=str(e)
                )
