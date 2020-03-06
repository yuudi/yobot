from urllib.parse import urljoin

from quart import url_for


class Message:
    Passive = True
    Active = False
    Request = False

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.version = glo_setting["verinfo"]["ver_name"]
        if glo_setting["clan_battle_mode"] == "web":
            self.help_page = urljoin(
                glo_setting["public_address"],
                '{}help/'.format(glo_setting['public_basepath']))
        else:
            self.help_page = "http://h3.yobot.monster/"

    @staticmethod
    def match(cmd: str) -> int:
        if cmd == "ver" or cmd == "V" or cmd == "version":
            return 99
        elif cmd == "帮助" or cmd == "help":
            return 98
        else:
            return 0

    def execute(self, match_num: int, msg: dict) -> dict:
        if match_num == 99:
            reply = self.version
        elif match_num == 98:
            reply = "功能表："+self.help_page
        elif match_num == 2:
            reply = "boss被击败后我会提醒下树"
        else:
            reply = "此功能已经不再可用，请查看"+self.help_page
        return {
            "reply": reply,
            "block": True
        }
