# coding=utf-8

# todo:这个文件还没有为3.0修改过

import json
import os.path
import re
import sys


class Reserve():

    txt_list = []

    def __init__(self, baseinfo):
        """
        baseinfo=[群号，QQ号, 群名片]（字符串）
        """
        self.__groupid = baseinfo[0]
        self.__qqid = baseinfo[1]
        self.__nickname = baseinfo[2]
        self.__path = os.path.dirname(sys.argv[0])
        if os.path.exists(os.path.join(self.__path, "reservation.json")):
            with open(os.path.join(self.__path, "reservation.json"), "r", encoding="utf-8") as f:
                self.__data = json.load(f)
        else:
            self.__data = {}
        self.txt_list = []

    def __del__(self):
        pass

    def __save(self):
        with open(os.path.join(self.__path, "reservation.json"), "w", encoding="utf-8") as f:
            json.dump(self.__data, f, ensure_ascii=False, indent=2)

    def __res_boss(self, boss):
        if not self.__groupid in self.__data:
            self.__data[self.__groupid] = {}
        if not boss in self.__data[self.__groupid]:
            self.__data[self.__groupid][boss] = {}
        if self.__qqid in self.__data[self.__groupid][boss]:
            self.txt_list.append(
                self.__nickname +
                ("已经在树上了" if boss == "0" else "已经预约过了"))
        else:
            self.__data[self.__groupid][boss][self.__qqid] = self.__nickname
            self.txt_list.append(
                self.__nickname +
                ("挂树了，目前挂树人数：" if boss == "0" else "预约成功，目前预约人数：") +
                str(len(self.__data[self.__groupid][boss])))
            self.__save()

    def __notify(self, boss):
        trig = (boss == "0")  # 被动触发
        if trig:  # 查找boss号
            with open(os.path.join(self.__path, "conf.json"), "r", encoding="utf-8") as f:
                conf = json.load(f)
            if not self.__groupid in conf:
                return  # 被动触发且没有数据
            boss = str(conf[self.__groupid]["boss"])
        output = self.__data.get(self.__groupid, {}).get(boss, {})
        tree = self.__data.get(self.__groupid, {}).get("0", {})
        if tree != {}:  # 如果树上有人
            self.txt_list.append("boss已被击败")
            ats = ["[CQ:at,qq="+qq+"]" for qq in tree]
            self.txt_list.append(" ".join(ats))
            del self.__data[self.__groupid]["0"]
            self.__save()
        if output == {} and trig:
            return  # 被动触发且没有数据
        self.txt_list.append(boss+"号boss已出现")
        if output != {}:
            ats = ["[CQ:at,qq="+qq+"]" for qq in output]
            self.txt_list.append(" ".join(ats))
            del self.__data[self.__groupid][boss]
            self.__save()

    def __canc_res(self, boss):
        if self.__groupid in self.__data:
            if boss in self.__data[self.__groupid]:
                if self.__qqid in self.__data[self.__groupid][boss]:
                    del self.__data[self.__groupid][boss][self.__qqid]
                    self.txt_list.append(
                        self.__nickname +
                        "已取消预约")
                    self.__save()
                    return
        self.txt_list.append(self.__nickname + "没有预约")

    def __list_res(self, boss):
        if self.__groupid in self.__data:
            if boss in self.__data[self.__groupid]:
                self.txt_list.append(
                    ("挂树人数：" if boss =="0" else "预约人数：")
                    +str(len(self.__data[self.__groupid][boss])))
                for name in self.__data[self.__groupid][boss].values():
                    self.txt_list.append(name)
                return
        self.txt_list.append("挂树人数：0" if boss =="0" else "预约人数：0")

    @staticmethod
    def match(cmd):
        num = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
               "1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
        match = re.match(r"^[预預][订约定訂約][ABCabc老]?([一二三四五12345])[号王]?$", cmd)
        if match:
            return 0x10 + num[match.group(1)]
        match = re.match(r"^我?[挂上]树上?了?$", cmd)
        if match:
            return 0x10
        if (cmd.endswith("尾刀") or cmd.endswith("收尾") or cmd.endswith("收掉") or cmd.endswith("击败")):
            return 0x20
        match = re.match(r"^[到打该]?[ABCabc老]?([一二三四五12345])[号王]?了$", cmd)
        if match:
            return 0x20 | num[match.group(1)]
        match = re.match(r"^[ABCabc老]?([一二三四五12345])[号王]?死了$", cmd)
        if match:
            return 0x21 + (num[match.group(1)] % 5)
        match = re.match(r"^取消[预預]?[订约定訂約]?[ABCabc老]?([一二三四五12345])[号王]?$", cmd)
        if match:
            return 0x30 | num[match.group(1)]
        match = re.match(r"^查询?[预預]?[订约定訂約]?[ABCabc老]?([一二三四五12345])[号王]?$", cmd)
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
            self.__res_boss(para)
        elif func == 0x20:
            self.__notify(para)
        elif func == 0x30:
            self.__canc_res(para)
        elif func == 0x40:
            self.__list_res(para)
        elif func == 0:
            self.txt_list.append("rev参数错误")

    def text(self):
        return "\n".join(self.txt_list)
