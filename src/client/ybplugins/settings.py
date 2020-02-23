import json
import os
from urllib.parse import urljoin

from quart import Quart, jsonify, redirect, request, session, url_for

from .templating import render_template


class Setting:
    Passive = False
    Active = False
    Request = True

    def __init__(self,
                 glo_setting,
                 database_model,
                 bot_api,
                 *args, **kwargs):
        self.setting = glo_setting

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/setting/'),
            methods=['GET'])
        async def yobot_setting():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login'))
            return await render_template(
                'admin/setting.html',
                user=session['yobot_user'],
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
            if session['yobot_user']['authority_group'] >= 100:
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
                    message='Ok',
                    settings=settings,
                )
            elif request.method == 'PUT':
                new_setting = await request.get_json()
                if new_setting is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                self.setting.update(new_setting)
                save_setting = self.setting.copy()
                del save_setting["dirname"]
                del save_setting["verinfo"]
                config_path = os.path.join(
                    self.setting["dirname"], "yobot_config.json")
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(save_setting, f, indent=4, ensure_ascii=False)
                return jsonify(
                    code=0,
                    message='Ok',
                )

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/users/'),
            methods=['GET', 'PUT'])
        async def yobot_users_managing():
            return '建设中'

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/groups/'),
            methods=['GET', 'PUT'])
        async def yobot_groups_managing():
            return '建设中'
