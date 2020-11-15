from urllib.parse import urljoin


class Switcher:
    Passive = True
    Active = False
    Request = False

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting

    @staticmethod
    def match(cmd: str) -> int:
        if cmd == "设置":
            f = 0x300
        elif cmd.startswith("设置码"):
            f = 0x400
        elif cmd.startswith("设置"):
            if len(cmd) < 7:
                f = 0x500
            else:
                f = 0
        else:
            f = 0
        return f

    def execute(self, match_num: int, msg: dict) -> dict:
        super_admins = self.setting.get("super-admin", list())
        restrict = self.setting.get("setting-restrict", 3)
        cmd = msg["raw_message"]
        if msg["sender"]["user_id"] in super_admins:
            role = 0
        else:
            role_str = msg["sender"].get("role", None)
            if role_str == "owner":
                role = 1
            elif role_str == "admin":
                role = 2
            else:
                role = 3
        if role > restrict:
            if not cmd.startswith(("卡池", "邮箱", "新闻", "boss", "码"), 2):
                return None
            reply = "你的权限不足"
            return {"reply": reply, "block": True}

        if match_num == 0x300:
            return urljoin(
                self.setting['public_address'],
                '{}admin/setting/'.format(self.setting['public_basepath']))
        elif match_num == 0x400:
            return '设置码已弃用'
        elif match_num == 0x500:
            if cmd == "设置卡池":
                return urljoin(
                    self.setting['public_address'],
                    '{}admin/pool-setting/'.format(self.setting['public_basepath']))
            elif cmd == "设置邮箱":
                return '此设置不再可用'
            elif cmd == "设置新闻" or cmd == "设置日程":
                return '请机器人管理员在后台设置中进行设置'
            elif cmd == "设置boss":
                return '请机器人管理员后台设置中进行设置（boss设置在最下方折叠）'
            else:
                return
        else:
            return
