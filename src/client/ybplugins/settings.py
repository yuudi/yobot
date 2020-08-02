import asyncio
import json
import os
from urllib.parse import urljoin

from playhouse.shortcuts import model_to_dict
from quart import Quart, jsonify, redirect, request, session, url_for

from .templating import render_template
from .ybdata import Clan_group, User

_returned_query_fileds = [
    User.qqid,
    User.nickname,
    User.clan_group_id,
    User.authority_group,
    User.last_login_time,
    User.last_login_ipaddr,
]


class Setting:
    Passive = False
    Active = False
    Request = True

    def __init__(self,
                 glo_setting,
                 bot_api,
                 *args, **kwargs):
        self.setting = glo_setting

    def _get_users_json(self, req_querys: dict):
        querys = []
        if req_querys.get('qqid'):
            querys.append(
                User.qqid == req_querys['qqid']
            )
        if req_querys.get('clan_group_id'):
            querys.append(
                User.clan_group_id == req_querys['clan_group_id']
            )
        if req_querys.get('authority_group'):
            querys.append(
                User.authority_group == req_querys['authority_group']
            )
        users = User.select(
            User.qqid,
            User.nickname,
            User.clan_group_id,
            User.authority_group,
            User.last_login_time,
            User.last_login_ipaddr,
        ).where(
            User.deleted == False,
            *querys,
        ).paginate(
            page=req_querys['page'],
            paginate_by=req_querys['page_size']
        )
        return json.dumps({
            'code': 0,
            'data': [model_to_dict(u, only=_returned_query_fileds) for u in users],
        })

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/setting/'),
            methods=['GET'])
        async def yobot_setting():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                if not user.authority_group >= 100:
                    uathname = '公会战管理员'
                else:
                    uathname = '成员'
                return await render_template(
                    'unauthorized.html',
                    limit='主人',
                    uath=uathname,
                )
            return await render_template(
                'admin/setting.html',
            )

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/setting/api/'),
            methods=['GET', 'PUT'])
        async def yobot_setting_api():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 100:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            if request.method == 'GET':
                settings = self.setting.copy()
                del settings['dirname']
                del settings['verinfo']
                del settings['host']
                del settings['port']
                del settings['access_token']
                return jsonify(
                    code=0,
                    message='success',
                    settings=settings,
                )
            elif request.method == 'PUT':
                req = await request.get_json()
                if req.get('csrf_token') != session['csrf_token']:
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                new_setting = req.get('setting')
                if new_setting is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                self.setting.update(new_setting)
                save_setting = self.setting.copy()
                del save_setting['dirname']
                del save_setting['verinfo']
                config_path = os.path.join(
                    self.setting['dirname'], 'yobot_config.json')
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(save_setting, f, indent=4)
                return jsonify(
                    code=0,
                    message='success',
                )

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/pool-setting/'),
            methods=['GET'])
        async def yobot_pool_setting():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                if not user.authority_group >= 100:
                    uathname = '公会战管理员'
                else:
                    uathname = '成员'
                return await render_template(
                    'unauthorized.html',
                    limit='主人',
                    uath=uathname,
                )
            return await render_template('admin/pool-setting.html')

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'admin/pool-setting/api/'),
            methods=['GET', 'PUT'])
        async def yobot_pool_setting_api():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            if request.method == 'GET':
                with open(os.path.join(self.setting['dirname'], 'pool3.json'),
                          'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return jsonify(
                    code=0,
                    message='success',
                    settings=settings,
                )
            elif request.method == 'PUT':
                req = await request.get_json()
                if req.get('csrf_token') != session['csrf_token']:
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                new_setting = req.get('setting')
                if new_setting is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                with open(os.path.join(self.setting['dirname'], 'pool3.json'),
                          'w', encoding='utf-8') as f:
                    json.dump(new_setting, f, ensure_ascii=False, indent=2)
                return jsonify(
                    code=0,
                    message='success',
                )

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/users/'),
            methods=['GET'])
        async def yobot_users_managing():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                if not user.authority_group >= 100:
                    uathname = '公会战管理员'
                else:
                    uathname = '成员'
                return await render_template(
                    'unauthorized.html',
                    limit='主人',
                    uath=uathname,
                )
            return await render_template('admin/users.html')

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/users/api/'),
            methods=['POST'])
        async def yobot_users_api():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            try:
                req = await request.get_json()
                if req is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                if req.get('csrf_token') != session['csrf_token']:
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                action = req['action']
                if action == 'get_data':
                    return await asyncio.get_event_loop().run_in_executor(
                        None,
                        self._get_users_json,
                        req['querys'],
                    )

                elif action == 'modify_user':
                    data = req['data']
                    m_user: User = User.get_or_none(qqid=data['qqid'])
                    if ((m_user.authority_group <= user.authority_group) or
                            (data.get('authority_group', 999)) <= user.authority_group):
                        return jsonify(code=12, message='Exceed authorization is not allowed')
                    if data.get('authority_group') == 1:
                        self.setting['super-admin'].append(data['qqid'])
                        save_setting = self.setting.copy()
                        del save_setting['dirname']
                        del save_setting['verinfo']
                        config_path = os.path.join(
                            self.setting['dirname'], 'yobot_config.json')
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(save_setting, f, indent=4)
                    if m_user is None:
                        return jsonify(code=21, message='user not exist')
                    for key in data.keys():
                        setattr(m_user, key, data[key])
                    m_user.save()
                    return jsonify(code=0, message='success')
                elif action == 'delete_user':
                    user = User.get_or_none(qqid=req['data']['qqid'])
                    if user is None:
                        return jsonify(code=21, message='user not exist')
                    user.clan_group_id = None
                    user.authority_group = 999
                    user.password = None
                    user.deleted = True
                    user.save()
                    return jsonify(code=0, message='success')
                else:
                    return jsonify(code=32, message='unknown action')
            except KeyError as e:
                return jsonify(code=31, message=str(e))

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/groups/'),
            methods=['GET'])
        async def yobot_groups_managing():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                if not user.authority_group >= 100:
                    uathname = '公会战管理员'
                else:
                    uathname = '成员'
                return await render_template(
                    'unauthorized.html',
                    limit='主人',
                    uath=uathname,
                )
            return await render_template('admin/groups.html')

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/groups/api/'),
            methods=['POST'])
        async def yobot_groups_api():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            try:
                req = await request.get_json()
                if req is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                if req.get('csrf_token') != session['csrf_token']:
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                action = req['action']
                if action == 'get_data':
                    groups = []
                    for group in Clan_group.select().where(
                        Clan_group.deleted == False,
                    ):
                        groups.append({
                            'group_id': group.group_id,
                            'group_name': group.group_name,
                            'game_server': group.game_server,
                        })
                    return jsonify(code=0, data=groups)
                if action == 'drop_group':
                    User.update({
                        User.clan_group_id: None,
                    }).where(
                        User.clan_group_id == req['group_id'],
                    ).execute()
                    Clan_group.delete().where(
                        Clan_group.group_id == req['group_id'],
                    ).execute()
                    return jsonify(code=0, message='ok')
                else:
                    return jsonify(code=32, message='unknown action')
            except KeyError as e:
                return jsonify(code=31, message=str(e))
