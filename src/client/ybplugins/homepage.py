from urllib.parse import urljoin

from quart import Quart, send_from_directory

from .templating import render_template, static_folder, template_folder


class Index:
    Passive = False
    Active = False
    Request = True

    def __init__(self, glo_setting, *args, **kwargs):
        self.setting = glo_setting
        self.public_basepath = glo_setting["public_basepath"]

    def register_routes(self, app: Quart):

        @app.route(self.public_basepath, ["GET"])
        async def yobot_homepage():
            return await render_template(
                "homepage.html",
                verinfo=self.setting["verinfo"]["ver_name"],
            )

        @app.route("/favicon.ico", ["GET"])
        async def yobot_favicon():
            return await send_from_directory(static_folder, "small.ico")

        preffix = self.setting["preffix_string"] if self.setting["preffix_on"] else ""

        @app.route(
            urljoin(self.public_basepath, 'help/'),
            methods=['GET'])
        async def yobot_help():
            return await send_from_directory(template_folder, "help.html")
