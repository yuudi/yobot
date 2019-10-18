# coding=utf-8

import json
import os
import sys


class Switcher:
    func_list = ["抽卡", "jjc查询", "无效命令提示"]
    data = {}

    def __init__(self):
        self.path = os.path.join(os.path.dirname(sys.argv[0]), "switcher.json")
        self.txt_list = []
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def switch(self, func, sw):
        self.data[func] = sw
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def match(self, cmd):
        if cmd.startswith("打开"):
            f = 0x100
        elif cmd.startswith("关闭"):
            f = 0x200
        else:
            f = 0
        if f != 0:
            if cmd[2:] in self.func_list:
                f += self.func_list.index(cmd[2:])
            else:
                f = 1
        return f

    def sw(self, match_num):
        if match_num == 1:
            self.txt_list.append("没有此功能的开关，目前允许使用开关的功能有：" +
                                 "、".join(self.func_list))
            return
        func = self.func_list[match_num & 0xff]
        sw = (match_num & 0xf00 == 0x100)
        self.switch(func, sw)
        self.txt_list.append(func + "功能已" + ("打开" if sw else "关闭"))
