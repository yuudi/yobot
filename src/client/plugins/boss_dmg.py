# 把不想改的祖传代码封装一下

from plugins import dmg_record, lock_boss, reserve


class Boss_dmg:
    def __init__(self, glo_setting: dict):
        pass

    @staticmethod
    def match(cmd: str) -> int:
        func = lock_boss.Lock.match(cmd)
        if func != 0:
            return func | 0x1000
        func = dmg_record.Record.match(cmd)
        if func != 0:
            return func | 0x2000
        func = reserve.Reserve.match(cmd)
        if func != 0:
            return func | 0x3000
        return 0

    def execute(self, match_num: int, msg: dict) -> dict:
        swit = match_num & 0xf000
        func = match_num & 0x0fff
        cmd_list = (str(msg["group_id"]),
                    str(msg["sender"]["user_id"]),
                    msg["sender"]["card"])
        cmd = msg["raw_message"]
        txt_list = []
        if swit == 0x1000:
            lockboss = lock_boss.Lock(cmd_list[:3])
            lockboss.lockboss(cmd, func, comment=cmt)
            txt_list.extend(lockboss.txt_list)
            # return txt_list
        # 记录伤害
        if swit == 0x2000:
            report = dmg_record.Record(cmd_list[:3])
            report.rep(cmd, func)
            txt_list.extend(report.txt_list)
            # if func == 3 or func == 400 or func == 401:
            #     pass  # 后面可能继续运行
            # else:
            #     return txt_list  # 后面不再运行
        # 预约boss
        if swit == 0x3000:
            rsv = reserve.Reserve(cmd_list[:3])
            rsv.rsv(cmd, func)
            txt_list.extend(rsv.txt_list)
            # return txt_list  # 后面不再运行
        return {
            "reply": "\n".join(txt_list),
            "block": True}
