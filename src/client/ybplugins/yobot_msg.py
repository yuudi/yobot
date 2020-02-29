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
        if (cmd == "报名公会战"
                or cmd == "公会战名单"
                or cmd == "清空公会"
                or cmd == "每日重置"
                or cmd.startswith("踢出公会")):
            return 1
        elif cmd == "下来吧" or cmd == "下树":
            return 2
        elif cmd == "十连抽图" or cmd == "检查卡池":
            return 3
        elif cmd == "台服活动" or cmd == "台服新闻" or cmd == "日服活动" or cmd == "日服新闻":
            return 5
        elif cmd == "ver" or cmd == "V" or cmd == "version":
            return 99
        elif cmd == "菜单" or cmd == "功能" or cmd == "帮助" or cmd == "help":
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
