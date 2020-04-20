# 把不想改的祖传代码封装一下

from . import dmg_record, lock_boss, reserve
import re


class Boss_dmg:
    Passive = True
    Active = False
    Request = False

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting
        self.prog = re.compile(r"^((\[CQ:at,qq=\d{5,10}\])|(@.+[:：]))? ?(尾刀|收尾|收掉|击败)$")

    def match(self, cmd: str) -> int:
        if self.setting["clan_battle_mode"] != "chat":
            return 0
        func = lock_boss.Lock.match(cmd)
        if func != 0:
            return func | 0x1000
        func = dmg_record.Record.match(cmd)
        if func != 0:
            return func | 0x2000
        func = reserve.Reserve.match(cmd)
        if func != 0:
            return func | 0x3000
        if re.match(r'^创建(?:([日台韩国])服)?[公工行]会$', cmd):
            return -1
        return 0

    def execute(self, match_num: int, msg: dict) -> dict:
        if msg["message_type"] != "group":
            reply = "此功能仅可用于群聊"
            return {"reply": reply, "block": True}
        if match_num == -1:
            reply = "群聊模式下无需创建（如需网页模式，请登录后台切换）"
            return {"reply": reply, "block": True}
        swit = match_num & 0xf000
        func = match_num & 0x0fff
        cmd_list = (str(msg["group_id"]),
                    str(msg["sender"]["user_id"]),
                    msg["sender"]["card"])
        cmdi = msg["raw_message"].split("//", 1)
        cmd = cmdi[0]
        if len(cmdi) == 1:
            cmt = None
        else:
            cmt = cmdi[1]
        if (cmd.startswith("重新开始") or cmd.startswith("选择") or cmd.startswith("切换")
                or cmd.startswith("修正") or cmd.startswith("修改") or cmd == "上传报告"):
            super_admins = self.setting.get("super-admin", list())
            restrict = self.setting.get("setting-restrict", 3)
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
                reply = "你的权限不足"
                return {"reply": reply, "block": True}
        txt_list = []
        basepath = self.setting["dirname"]
        if swit == 0x1000:
            lockboss = lock_boss.Lock(cmd_list[:3], basepath)
            lockboss.lockboss(cmd, func, comment=cmt)
            txt_list.extend(lockboss.txt_list)
        if swit == 0x2000:
            report = dmg_record.Record(cmd_list[:3], basepath)
            report.rep(cmd, func)
            txt_list.extend(report.txt_list)
            if re.match(self.prog, cmd):
                rsv = reserve.Reserve(cmd_list[:3], basepath)
                rsv.rsv(cmd, 0x20)
                txt_list.extend(rsv.txt_list)
            if func == 2 or func == 3 or func == 400 or func == 401:
                lockboss = lock_boss.Lock(cmd_list[:3], basepath)
                lockboss.boss_challenged()
                txt_list.extend(lockboss.txt_list)
        if swit == 0x3000:
            rsv = reserve.Reserve(cmd_list[:3], basepath)
            rsv.rsv(cmd, func)
            txt_list.extend(rsv.txt_list)
            if rsv.is_on_tree:
                lockboss = lock_boss.Lock(cmd_list[:3], basepath)
                lockboss.on_tree()
                txt_list.extend(lockboss.txt_list)
        return {
            "reply": "\n-------\n".join(txt_list),
            "block": True}
