# coding=utf-8

import sys

from dmg_record import Record
from lock_boss import Lock
from reserve import Reserve
from yobot_msg import Message
from check_ver import Check


def yobot(*cmd_list):
    txt_list = []
    if len(cmd_list) != 4:
        txt_list.append("100参数错误")
    else:
        u = Check()
        if cmd_list[3] == "更新":
            txt_list.append(u.update())
            return txt_list  # 后面不再运行
        r = u.check()
        if r != None:
            txt_list.append(r)
        del u
        func = Message.match(cmd_list[3])
        if func != 0:
            txt_list.append(Message.msg(func))
            return txt_list  # 后面不再运行
        func = Lock.match(cmd_list[3])
        if func != 0:
            lockboss = Lock(cmd_list[:3])
            lockboss.lockboss(cmd_list[3], func)
            txt_list.extend(lockboss.txt_list)
            return txt_list  # 后面不再运行
        func = Record.match(cmd_list[3])
        if func != 0:
            report = Record(cmd_list[:3])
            report.rep(cmd_list[3], func)
            txt_list.extend(report.txt_list)
            if func == 3 or func == 4:
                pass  # 后面可能继续运行
            else:
                return txt_list  # 后面不再运行
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
