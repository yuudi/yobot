# coding=utf-8

# 祖传代码，写得稀烂，不想改了

# 屎山改不动了，放弃了😫

import json
import os
import pickle
import random
import re
import time

from .dmg_report import Report


class Re_cache:
    def __init__(self):
        self.prog = {}

    def get(self, pattern):
        cache = self.prog.get(pattern)
        if cache is None:
            cache = re.compile(pattern)
            self.prog[pattern] = cache
        return cache

recache = Re_cache()
boss_health_cache = None

class Record():
    """
    这个类用于记录出刀伤害
    """

    Boss_health = {
        "jp": [
            [6000000, 8000000, 10000000, 12000000, 15000000],
            [6000000, 8000000, 10000000, 12000000, 15000000],
            [7000000, 9000000, 13000000, 14000000, 17000000],
            [7000000, 9000000, 13000000, 15000000, 20000000]
        ],
        "tw": [
            [6000000, 8000000, 10000000, 12000000, 15000000],
        ]*3
    }
    txt_list = []

    def __init__(self, baseinfo, basepath):
        """
        baseinfo=[群号, QQ号, 群名片]（字符串）
        """
        self._groupid = baseinfo[0]
        self._qqid = baseinfo[1]
        self._nickname = baseinfo[2]
        self._path = basepath
        self._show_status = True
        self._data = []
        self._comment = ""
        self.txt_list = []
        global boss_health_cache
        if boss_health_cache is None:
            with open(os.path.join(self._path, "boss3.json")) as f:
                self.Boss_health=json.load(f)
                boss_health_cache = self.Boss_health
        else:
            self.Boss_health = boss_health_cache
        # self._time_offset = time.timezone + 28800  # GMT+8
        if os.path.exists(os.path.join(self._path, "conf.json")):
            with open(os.path.join(self._path, "conf.json"), "r", encoding="utf-8") as f:
                self._conf = json.load(f)
        else:
            self._conf = {}
        if not os.path.exists(os.path.join(self._path, "data")):
            os.mkdir(os.path.join(self._path, "data"))
        if not os.path.exists(os.path.join(self._path, "mailconf.json")):
            with open(os.path.join(self._path, "mailconf.json"), "w", encoding="utf-8") as f:
                initmailconf = {
                    "sender": {
                        "host": "smtp.163.com",
                        "user": "unknown",
                        "pswd": "unknown",
                        "sender": "unknown"},
                    "subscriber": {}}
                json.dump(initmailconf, f, ensure_ascii=False, indent=2)
        if not(self._groupid in self._conf.keys()):
            self._conf[self._groupid] = {
                "area": "unknown",
                "lap": 1,
                "boss": 1,
                "remain": 0}
            self._data = [[], {}]
            with open(os.path.join(self._path, "mailconf.json"), "r+", encoding="utf-8") as f:
                mailcfg = json.load(f)
                mailcfg["subscriber"][self._groupid] = []
                f.seek(0)
                f.truncate()
                json.dump(mailcfg, f, ensure_ascii=False, indent=2)
            self.txt_list.append("本群第一次使用，数据已初始化，请仔细阅读说明https://gitee.com/yobot/yobot/blob/master/documents/features/old.md")
        else:
            with open(os.path.join(self._path, "data", self._groupid+".dat"), "rb") as f:
                self._data = pickle.load(f)

    def __del__(self):
        pass

    def _lap2stage(self, lap):
        if lap <= 3:
            return 0
        elif lap <= 10:
            return 1
        else:
            if len(self.Boss_health[self._conf[self._groupid]["area"]]) > 3:
                if lap >= 35:
                    return 3
            return 2

    def _boss_status(self):
        self.txt_list.append("现在{}周目，{}号boss，剩余血量{:,}".format(
            self._conf[self._groupid]["lap"],
            self._conf[self._groupid]["boss"],
            self._conf[self._groupid]["remain"]))

    def _cmdtoint(self, cmd):
        cmd = cmd.replace("k", "000")
        cmd = cmd.replace("K", "000")
        cmd = cmd.replace("w", "0000")
        cmd = cmd.replace("W", "0000")
        cmd = cmd.replace("万", "0000")
        if not cmd.isdigit():
            return None
        return int(cmd)

    def _save(self):
        with open(os.path.join(self._path, "conf.json"), "w", encoding="utf-8") as f:
            json.dump(self._conf, f, ensure_ascii=False, indent=2)
        with open(os.path.join(self._path, "data", self._groupid+".dat"), "wb") as f:
            pickle.dump(self._data, f)

    def _creat_mem(self):
        if not self._qqid in self._data[1].keys():
            self._data[1][self._qqid] = [
                self._nickname,
                0,  # 0完整刀,1尾刀,2余刀,3余尾刀
                0,  # 最后一刀的时间
                0]  # 今日刀数
        else:
            # self._qqid = "unknown"
            # self.txt_list.append("你还没有报名公会战")
            pass

    def _write_log(self, cmd, comment=None):
        if comment != None:
            self._comment += ("//"+comment)
        with open(os.path.join(self._path, "data", self._groupid+".log"), "a", encoding="utf-8-sig") as f:
            if self._show_status:
                f.writelines("{} {}({}) {} [{},{},{}] ({})\n".format(
                    time.strftime("%Y/%m/%d %H:%M:%S(GMT%z)",
                                  time.localtime()),
                    self._qqid,
                    self._nickname,
                    cmd,
                    self._conf[self._groupid]["lap"],
                    self._conf[self._groupid]["boss"],
                    self._conf[self._groupid]["remain"],
                    self._comment))
            else:
                f.writelines("{} {}({}) {} ({})\n".format(
                    time.strftime("%Y/%m/%d %H:%M:%S(GMT%z)",
                                  time.localtime()),
                    self._qqid,
                    self._nickname,
                    cmd,
                    self._comment))

    def _damage(self, cmd, comment = None):
        dmg = self._cmdtoint(cmd)
        if dmg == None:
            return        
        remain = self._conf[self._groupid]["remain"]
        if(dmg >= remain):
            self._comment += "未记录"
            self.txt_list.append("报刀无效，伤害量必须小于剩余血量，如果击败boss请发送“尾刀”")
            self._boss_status()
        else:
            if not (self._qqid in self._data[1].keys()):
                self._creat_mem()
                if self._qqid == "unknown":
                    self._comment += "未记录"
                    return
            if self._nickname != self._qqid:
                self._data[1][self._qqid][0] = self._nickname
            now = int(time.time())
            self._conf[self._groupid]["remain"] = remain - dmg
            self._data[0].append([
                True,
                now,
                self._qqid,
                self._conf[self._groupid]["lap"],
                self._conf[self._groupid]["boss"],
                dmg,
                self._data[1][self._qqid][1],
                remain - dmg,
                comment])
            time_offset = 14400 if self._conf[self._groupid]["area"] == "jp" \
                else 10800  # GMT偏移：日服4小时，台服国服3小时
            if time.gmtime(self._data[1][self._qqid][2]+time_offset)[0:3] \
                    == time.gmtime(now+time_offset)[0:3]:  # 如果此刀与上一刀在同一个“pcr日”中
                if self._data[1][self._qqid][1] == 0:
                    self._data[1][self._qqid][3] += 1
            else:  # 否则
                self._data[1][self._qqid][3] = 1
            self.txt_list.append("{}对boss造成{:,}点伤害(今日第{}刀，{})".format(
                self._data[1][self._qqid][0],
                dmg,
                self._data[1][self._qqid][3],
                "完整刀" if self._data[1][self._qqid][1] == 0 else "余刀"))
            self._data[1][self._qqid][1] = 0
            self._data[1][self._qqid][2] = now
            self._save()
            self._comment += "已记录"
            self._boss_status()

    def _eliminate(self, comment = None):
        if not (self._qqid in self._data[1].keys()):
            self._creat_mem()
            if self._qqid == "unknown":
                self._comment += "未记录"
                return
        if self._data[1][self._qqid][0] == self._qqid:
            self._data[1][self._qqid][0] = self._nickname
        now = int(time.time())
        self._data[0].append([
            True,
            now,
            self._qqid,
            self._conf[self._groupid]["lap"],
            self._conf[self._groupid]["boss"],
            self._conf[self._groupid]["remain"],
            self._data[1][self._qqid][1]+1,
            0,
            comment])
        time_offset = 14400 if self._conf[self._groupid]["area"] == "jp" \
            else 10800  # GMT偏移：日服+4小时，台服国服+3小时
        if time.gmtime(self._data[1][self._qqid][2]+time_offset)[0:3] \
                == time.gmtime(now+time_offset)[0:3]:  # 如果此刀与上一刀在同一个“pcr日”中
            if self._data[1][self._qqid][1] == 0:  # 如果上一刀不是尾刀
                self._data[1][self._qqid][3] += 1
        else:  # 否则
            self._data[1][self._qqid][3] = 1
        self.txt_list.append("{}对boss造成{:,}点伤害，击败了boss(今日第{}刀，{})".format(
            self._data[1][self._qqid][0],
            self._conf[self._groupid]["remain"],
            self._data[1][self._qqid][3],
            "尾刀" if self._data[1][self._qqid][1] == 0 else "尾余刀"))
        self._data[1][self._qqid][1] ^= 2  # 2变0,0变2
        self._data[1][self._qqid][2] = now
        if (self._conf[self._groupid]["boss"] == 5):
            self._conf[self._groupid]["boss"] = 1
            self._conf[self._groupid]["lap"] = \
                self._conf[self._groupid]["lap"]+1
        else:
            self._conf[self._groupid]["boss"] = \
                self._conf[self._groupid]["boss"]+1
        self._conf[self._groupid]["remain"] = (
            self.Boss_health[self._conf[self._groupid]["area"]]
            [self._lap2stage(self._conf[self._groupid]["lap"])]
            [self._conf[self._groupid]["boss"]-1])
        self._save()
        self._comment += "已记录"
        self._boss_status()

    def _undo(self):
        if len(self._data[0]) == 0:
            self._comment += "未撤销"
            self.txt_list.append("没有记录无法撤销")
        else:
            opt = self._data[0].pop()
            if opt[0]:  # 报刀
                if (opt[6] == 0 or opt[6] == 2):  # 非尾刀
                    self._conf[self._groupid]["remain"] = opt[5] + opt[7]
                else:  # 尾刀
                    self._conf[self._groupid]["lap"] = opt[3]
                    self._conf[self._groupid]["boss"] = opt[4]
                    self._conf[self._groupid]["remain"] = opt[5]
                if (opt[6] == 2 or opt[6] == 3):  # 余刀
                    self._data[1][opt[2]][1] = 2  # 上一刀为尾刀
                else:  # 非余刀
                    self._data[1][opt[2]][1] = 0  # 上一刀非尾刀
                    self._data[1][opt[2]][3] -= 1  # 本日刀数-1
                self._save()
                self._comment += "已撤销"
                self.txt_list.append("{}在{}对{}周目{}号boss造成的{:,}伤害已撤销".format(
                    self._data[1][opt[2]][0],
                    time.strftime("%m/%d %H:%M:%S", time.gmtime(opt[1]+28800)),
                    opt[3],
                    opt[4],
                    opt[5]))
                self._boss_status()
            else:  # 修正
                self._conf[self._groupid]["lap"] = opt[3]
                self._conf[self._groupid]["boss"] = opt[4]
                self._conf[self._groupid]["remain"] = opt[5]
                self._save()
                self._comment += "已撤销"
                self.txt_list.append("{}在{}的修改已撤销".format(
                    self._data[1][opt[2]][0],
                    time.strftime("%m/%d %H:%M:%S", time.gmtime(opt[1]+28800))))
                self._boss_status()

    def _mod(self, cmd):
        match = re.match(recache.get(r"修[改正](.{1,4})=(\d+[wWkK万]?)$"), cmd)
        if match == None:
            self._comment += "未修正"
            self.txt_list.append("400参数错误")
        else:
            b = self._cmdtoint(match.group(2))
            if match.group(1) in ["血量", "生命", "生命值", "体力", "hp"]:
                if b >= 1 and b <= (self.Boss_health[self._conf[self._groupid]["area"]]
                                    [self._lap2stage(
                                        self._conf[self._groupid]["lap"])]
                                    [self._conf[self._groupid]["boss"]-1]):
                    self._data[0].append([
                        False,
                        int(time.time()),
                        self._qqid,
                        self._conf[self._groupid]["lap"],
                        self._conf[self._groupid]["boss"],
                        self._conf[self._groupid]["remain"]])
                    self._conf[self._groupid]["remain"] = b
                    self._save()
                    self._comment += "已修正"
                    self.txt_list.append("boss状态已更新")
                    self._boss_status()
                else:
                    self._comment += "未修正"
                    self.txt_list.append("402参数错误")
            elif match.group(1) in ["体目", "boss"]:
                if b <= 5 and b >= 1:
                    self._data[0].append([
                        False,
                        int(time.time()),
                        self._qqid,
                        self._conf[self._groupid]["lap"],
                        self._conf[self._groupid]["boss"],
                        self._conf[self._groupid]["remain"]])
                    self._conf[self._groupid]["boss"] = b
                    self._conf[self._groupid]["remain"] = (
                        self.Boss_health[self._conf[self._groupid]["area"]]
                        [self._lap2stage(self._conf[self._groupid]["lap"])]
                        [b-1])
                    self._save()
                    self._comment += "已修正"
                    self.txt_list.append("boss状态已更新")
                    self._boss_status()
                else:
                    self._comment += "未修正"
                    self.txt_list.append("403参数错误")
            elif match.group(1) in ["周目", "圈", "圈数", "周数"]:
                if b >= 1:
                    self._data[0].append([
                        False,
                        int(time.time()),
                        self._qqid,
                        self._conf[self._groupid]["lap"],
                        self._conf[self._groupid]["boss"],
                        self._conf[self._groupid]["remain"]])
                    self._conf[self._groupid]["lap"] = b
                    self._save()
                    self._comment += "已修正"
                    self.txt_list.append("boss状态已更新")
                    self._boss_status()
                else:
                    self._comment += "未修正"
                    self.txt_list.append("404参数错误")
            else:
                self._comment += "未修正"
                self.txt_list.append("401参数错误")

    def _clear(self, cmd):
        cf = self._conf[self._groupid].get("res", None)
        if cf == cmd[4:]:
            del self._conf[self._groupid]
            self._save()
            os.remove(os.path.join(self._path, "data", self._groupid+".dat"))
            self._comment += "已重置"
            self.txt_list.append("数据已清空")
        else:
            self._conf[self._groupid]["res"] = "{0:04d}".format(
                random.randint(0, 9999))
            self._save()
            self._comment += "未重置"
            self.txt_list.append("注意：此操作将删除所有记录，公会战期间小心使用，如果确定重新开始请发送“重新开始{}”"
                                 .format(self._conf[self._groupid]["res"]))

    def _mailopt(self, opt, addr=""):
        self._show_status = False
        with open(os.path.join(self._path, "mailconf.json"), "r", encoding="utf-8") as f:
            mailcfg = json.load(f)
        if opt == "add":
            if re.match(recache.get(r"\w+@\w+\.\w+"), addr):
                if addr in mailcfg["subscriber"][self._groupid]:
                    self._comment += "已存在"
                    self.txt_list.append("你已经订阅过了")
                else:
                    mailcfg["subscriber"][self._groupid].append(addr)
                    with open(os.path.join(self._path, "mailconf.json"), "w") as f:
                        json.dump(mailcfg, f, ensure_ascii=False, indent=2)
                    self._comment += "成功订阅"
                    self.txt_list.append("订阅成功")
            else:
                self.txt_list.append("500邮件格式错误")
        elif opt == "del":
            if re.match(recache.get(r"\w+@\w+\.\w+"), addr):
                if addr in mailcfg["subscriber"][self._groupid]:
                    mailcfg["subscriber"][self._groupid].remove(addr)
                    with open(os.path.join(self._path, "mailconf.json"), "w") as f:
                        json.dump(mailcfg, f, ensure_ascii=False, indent=2)
                    self._comment += "已取消"
                    self.txt_list.append("取消订阅成功")
                else:
                    self._comment += "未订阅"
                    self.txt_list.append("你并没有订阅")
            else:
                self.txt_list.append("500邮件格式错误")
        elif opt == "show":
            self.txt_list.append(
                "订阅人数：" +
                str(len(mailcfg["subscriber"][self._groupid])))
            for a in mailcfg["subscriber"][self._groupid]:
                self.txt_list.append(a)
            self._comment += "查询成功"

    def _sendmail(self):
        r = Report(self._groupid, self._path)
        r.report(mathod="sendmail")
        self.txt_list.extend(r.txt_list)

    def _uploadfile(self):
        r = Report(self._groupid, self._path)
        r.report(mathod="uploadfile")
        self.txt_list.extend(r.txt_list)

    def _uploaddaily(self, cmd):
        if cmd == "" or cmd == "今日"or cmd == "今天":
            date = "today"
        elif cmd == "昨日"or cmd == "昨天":
            date = "yesterday"
        else:
            match = re.match(recache.get(r"(\d{1,2})[月/\-](\d{1,2})[日号]?"), cmd)
            if match:
                date = "{:02d}/{:02d}".format(int(match.group(1)),
                                              int(match.group(2)))
            else:
                self._comment += "参数错误"
                self.txt_list.append("600参数错误")
                return
        r = Report(self._groupid, self._path)
        r.report(mathod="uploaddaily", date=date)
        self.txt_list.extend(r.txt_list)

    @staticmethod
    def match(incmd):
        """
        匹配命令，返回触发功能的序号
        """
        cmd = incmd.replace(" ", "")
        if re.match(recache.get(r"^报刀\d+[wWkK万]?$"), cmd):
            return 2
        elif (cmd == "尾刀" or cmd == "收尾" or cmd == "收掉" or cmd == "击败"):
            return 3
        elif re.match(recache.get(r"^\[CQ:at,qq=\d{5,10}\] ?(\d+[wWkK万]?|尾刀|收尾|收掉|击败)$"), cmd):
            return 400
        elif re.match(recache.get(r"^@.+[:：].+"), cmd):
            return 401
        elif cmd == "撤销":
            return 5
        elif cmd == "状态":
            return 6
        elif cmd.startswith("修正") or cmd.startswith("修改"):
            return 7
        elif cmd == "选择日服" or cmd == "切换日服":
            return 8
        elif cmd == "选择台服" or cmd == "切换台服":
            return 9
        elif cmd == "选择国服" or cmd == "切换国服":
            return 91
        elif cmd.startswith("重新开始"):
            return 10
        elif cmd.startswith("订阅邮件") or cmd.startswith("增加邮箱") or cmd.startswith("添加邮箱"):
            return 11
        elif cmd.startswith("删除邮箱"):
            return 12
        elif cmd == "查看邮箱" or cmd == "显示邮箱" or cmd == "邮箱列表":
            return 13
        elif cmd == "发送报告":
            return 14
        elif cmd == "上传报告":
            return 15
        elif cmd.endswith("报告"):
            return 16
        elif cmd == "查刀":
            return 160
        else:
            return 0

    def rep(self, incmd, func_num=None, comment=None):
        """
        实施命令
        """
        cmd = incmd.replace(" ", "")
        if func_num == None:
            func_num = self.match(cmd)
        if not os.path.exists(os.path.join(self._path, "data", self._groupid+".dat")):
            if cmd == "选择日服":
                self._conf[self._groupid]["area"] = "jp"
                self._conf[self._groupid]["remain"] = self.Boss_health["jp"][0][0]
                self._save()
                self._boss_status()
                self._comment += "已成功选择"
            elif cmd == "选择台服" or cmd == "选择国服":
                self._conf[self._groupid]["area"] = "tw"
                self._conf[self._groupid]["remain"] = self.Boss_health["tw"][0][0]
                self._save()
                self._boss_status()
                self._comment += "已成功选择"
            else:
                self.txt_list.append(
                    "由于日服、台服、国服boss血量不同、每日重置时间不同，"
                    "请发送“选择日服”或“选择台服”或“选择国服”")
                self._comment += "未选择"
        elif func_num == 2:
            if cmd.startswith("报刀"):
                cmd = cmd[2:]
            self._damage(cmd, comment)
        elif func_num == 3:
            self._eliminate(comment)
        elif func_num == 400 or func_num == 401:
            self._comment += "由{}代报,".format(self._qqid)
            if func_num == 400:
                match = re.match(recache.get(r"\[CQ:at,qq=(\d{5,10})\] *(.+)"), cmd)
            else:
                match = re.match(recache.get(r"@(.+)[:：] *(.+)"), cmd)
            self._qqid = match.group(1)
            self._nickname = self._qqid
            cmd = match.group(2)
            if re.match(recache.get(r"\d+[wWkK万]?$"), cmd):
                self._damage(cmd, comment)
            elif (cmd == "尾刀" or cmd == "收尾" or cmd == "收掉" or cmd == "击败"):
                self._eliminate(comment)
            # else:
            #     self._comment += "参数错误"
            #     self.txt_list.append("300参数错误")
        elif func_num == 5:
            self._undo()
        elif func_num == 6:
            self._comment += "查询"
            self._boss_status()
        elif func_num == 7:
            self._mod(cmd)
        elif func_num == 8:
            self._conf[self._groupid]["area"] = "jp"
            self._save()
            self.txt_list.append("已切换为日服")
            self._comment += "已切换"
        elif func_num == 9:
            self._conf[self._groupid]["area"] = "tw"
            self._save()
            self.txt_list.append("已切换为台服")
            self._comment += "已切换"
        elif func_num == 91:
            self._conf[self._groupid]["area"] = "cn"
            self._save()
            self.txt_list.append("已切换为国服")
            self._comment += "已切换"
        elif func_num == 10:
            self._show_status = False
            self._clear(cmd)
        elif func_num == 11:
            self._mailopt("add", cmd[4:])
        elif func_num == 12:
            self._mailopt("del", cmd[4:])
        elif func_num == 13:
            self._mailopt("show")
        elif func_num == 14:
            self._sendmail()
        elif func_num == 15:
            self._uploadfile()
        elif func_num == 16:
            self._uploaddaily(cmd[:-2])
        elif func_num == 160:
            self._uploaddaily("")
        elif func_num == 0:
            self._comment += "参数错误"
            self.txt_list.append("200参数错误")
        self._write_log(cmd, comment)

    def text(self):
        return "\n".join(self.txt_list)
