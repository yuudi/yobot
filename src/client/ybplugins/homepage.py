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
                show_icp=self.setting["show_icp"],
                icp_info=self.setting["icp_info"],
                gongan_info=self.setting["gongan_info"],
            )

        @app.route(
            urljoin(self.public_basepath, 'about/'),
            methods=['GET'])
        async def yobot_about():
            return await render_template(
                "about.html",
                verinfo=self.setting["verinfo"]["ver_name"],
            )

        @app.route("/favicon.ico", ["GET"])
        async def yobot_favicon():
            return await send_from_directory(static_folder, "small.ico")

        @app.route(
            urljoin(self.public_basepath, 'help/'),
            methods=['GET'])
        async def yobot_help():
            return await send_from_directory(template_folder, "help.html")
