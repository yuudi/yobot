# coding=utf-8

import sys

from check_ver import Check
from dmg_record import Record
from jjc_consult import Consult
from lock_boss import Lock
from reserve import Reserve
from yobot_msg import Message


def yobot(*cmd_list):
    txt_list = []
    if len(cmd_list) != 4:
        txt_list.append("100参数错误")
    else:
        # 版本信息
        if cmd_list[3] == "ver":
            txt_list.append("yobot [ver 2.1.0.0]")
            return txt_list
        # 检查更新
        u = Check()
        if cmd_list[3] == "更新":
            txt_list.append(u.update())
            return txt_list
        r = u.check()
        if r != None:
            txt_list.append(r)
        del u
        # 提示信息
        func = Message.match(cmd_list[3])
        if func != 0:
            txt_list.append(Message.msg(func))
            return txt_list
        # jjc查询
        if cmd_list[3].startswith("jjc查询"):
            c = Consult()
            r = c.user_input(cmd_list[3][5:])
            if r == 0:
                c.jjcsearch()
            txt_list.extend(c.txt_list)
            return txt_list
        # 锁定boss
        func = Lock.match(cmd_list[3])
        if func != 0:
            lockboss = Lock(cmd_list[:3])
            lockboss.lockboss(cmd_list[3], func)
            txt_list.extend(lockboss.txt_list)
            return txt_list
        # 记录伤害
        func = Record.match(cmd_list[3])
        if func != 0:
            report = Record(cmd_list[:3])
            report.rep(cmd_list[3], func)
            txt_list.extend(report.txt_list)
            if func == 3 or func == 4:
                pass  # 后面可能继续运行
            else:
                return txt_list  # 后面不再运行
        # 预约boss
        func = Reserve.match(cmd_list[3])
        if func != 0:
            rsv = Reserve(cmd_list[:3])
            rsv.rsv(cmd_list[3], func)
            txt_list.extend(rsv.txt_list)
            return txt_list  # 后面不再运行
    if txt_list == []:
        txt_list.append("101无效命令")
    return txt_list


# 这是一个示例，也是现在正在使用的入口
if __name__ == "__main__":
    # 主程序用法如下：
    # yobot(groupid,qqid,nickname,msg)
    txtlist = yobot(*sys.argv[1:])  # 获得输出文本的list
    # 返回值时一个list，包含若干个字符串

    # 下一行是直接将内容输出到屏幕上
    print("\n".join(txtlist))  # 随便怎么用，这里是直接连接并输出
