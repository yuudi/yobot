from urllib.parse import urljoin

from quart import Quart, session

from .templating import render_template


class Setting:
    Passive = False
    Active = False
    Request = True

    def __init__(self,
                 glo_setting,
                 database_model,
                 send_msg_func,
                 *args, **kwargs):
        self.setting = glo_setting

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'setting/'),
            methods=['GET'])
        async def yobot_setting():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login'))
            return await render_template(
                'setting.html',
                user=session['yobot_user'],
            )
