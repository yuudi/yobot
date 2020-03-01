# coding=utf-8

# todo:这个文件还没有为3.0修改过

# 屎山改不动了，放弃了😫

import json
import os.path
import re

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

class Reserve():

    txt_list = []

    def __init__(self, baseinfo, basepath):
        """
        baseinfo=[群号，QQ号, 群名片]（字符串）
        """
        self._groupid = baseinfo[0]
        self._qqid = baseinfo[1]
        self._nickname = baseinfo[2]
        self._path = basepath
        if os.path.exists(os.path.join(self._path, "reservation.json")):
            with open(os.path.join(self._path, "reservation.json"), "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}
        self.txt_list = []
        self.is_on_tree = False

    def __del__(self):
        pass

    def _save(self):
        with open(os.path.join(self._path, "reservation.json"), "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _res_boss(self, boss):
        if not self._groupid in self._data:
            self._data[self._groupid] = {}
        if not boss in self._data[self._groupid]:
            self._data[self._groupid][boss] = {}
        if self._qqid in self._data[self._groupid][boss]:
            self.txt_list.append(
                self._nickname +
                ("已经在树上了" if boss == "0" else "已经预约过了"))
        else:
            self._data[self._groupid][boss][self._qqid] = self._nickname
            self.txt_list.append(
                self._nickname +
                ("挂树了，目前挂树人数：" if boss == "0" else "预约成功，目前预约人数：") +
                str(len(self._data[self._groupid][boss])))
            self._save()
            if boss == "0":
                self.is_on_tree = True

    def _notify(self, boss):
        trig = (boss == "0")  # 被动触发
        if trig:  # 查找boss号
            with open(os.path.join(self._path, "conf.json"), "r", encoding="utf-8") as f:
                conf = json.load(f)
            if not self._groupid in conf:
                return  # 被动触发且没有数据
            boss = str(conf[self._groupid]["boss"])
        output = self._data.get(self._groupid, {}).get(boss, {})
        tree = self._data.get(self._groupid, {}).get("0", {})
        if tree != {}:  # 如果树上有人
            self.txt_list.append("boss已被击败")
            ats = ["[CQ:at,qq="+qq+"]" for qq in tree]
            self.txt_list.append(" ".join(ats))
            del self._data[self._groupid]["0"]
            self._save()
        if output == {} and trig:
            return  # 被动触发且没有数据
        self.txt_list.append(boss+"号boss已出现")
        if output != {}:
            ats = ["[CQ:at,qq="+qq+"]" for qq in output]
            self.txt_list.append(" ".join(ats))
            del self._data[self._groupid][boss]
            self._save()

    def _canc_res(self, boss):
        if self._groupid in self._data:
            if boss in self._data[self._groupid]:
                if self._qqid in self._data[self._groupid][boss]:
                    del self._data[self._groupid][boss][self._qqid]
                    self.txt_list.append(
                        self._nickname +
                        "已取消预约")
                    self._save()
                    return
        self.txt_list.append(self._nickname + "没有预约")

    def _list_res(self, boss):
        if self._groupid in self._data:
            if boss in self._data[self._groupid]:
                self.txt_list.append(
                    ("挂树人数：" if boss =="0" else "预约人数：")
                    +str(len(self._data[self._groupid][boss])))
                for name in self._data[self._groupid][boss].values():
                    self.txt_list.append(name)
                return
        self.txt_list.append("挂树人数：0" if boss =="0" else "预约人数：0")

    @staticmethod
    def match(cmd):
        num = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
               "1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
        match = re.match(recache.get(r"^[预預][订约定訂約][ABCabc老]?([一二三四五12345])[号王]?$"), cmd)
        if match:
            return 0x10 + num[match.group(1)]
        match = re.match(recache.get(r"^我?[挂上]树上?了?$"), cmd)
        if match:
            return 0x10
        match = re.match(recache.get(r"^((\[CQ:at,qq=\d{5,10}\])|(@.+[:：]))? ?(尾刀|收尾|收掉|击败)$"), cmd)
        if match:
            return 0x20
        match = re.match(recache.get(r"^[到打该]?[ABCabc老]?([一二三四五12345])[号王]?了$"), cmd)
        if match:
            return 0x20 | num[match.group(1)]
        match = re.match(recache.get(r"^[ABCabc老]?([一二三四五12345])[号王]?死了$"), cmd)
        if match:
            return 0x21 + (num[match.group(1)] % 5)
        match = re.match(recache.get(r"^取消[预預]?[订约定訂約]?[ABCabc老]?([一二三四五12345])[号王]?$"), cmd)
        if match:
            return 0x30 | num[match.group(1)]
        match = re.match(recache.get(r"^查询?[预預]?[订约定訂約]?[ABCabc老]?([一二三四五12345])[号王]?$"), cmd)
        if match:
            return 0x40 | num[match.group(1)]
        if cmd == "查树":
            return 0x40
        return 0

    def rsv(self, cmd, func_num=None):
        if func_num == None:
            func_num = self.match(cmd)
        func = func_num & 0xF0
        para = str(func_num & 0x0F)
        if func == 0x10:
            self._res_boss(para)
        elif func == 0x20:
            self._notify(para)
        elif func == 0x30:
            self._canc_res(para)
        elif func == 0x40:
            self._list_res(para)
        elif func == 0:
            self.txt_list.append("rev参数错误")

    def text(self):
        return "\n".join(self.txt_list)
