# coding=utf-8
import json
import os.path
import sys
import time


class Lock():

    txt_list = []

    def __init__(self, baseinfo):
        """
        baseinfo=[群号，QQ号, 群名片]（字符串）
        """
        self.__groupid = baseinfo[0]
        self.__qqid = baseinfo[1]
        self.__nickname = baseinfo[2]
        self.__path = os.path.dirname(sys.argv[0])
        if os.path.exists(os.path.join(self.__path, "bosslock.json")):
            with open(os.path.join(self.__path, "bosslock.json"), "r", encoding="utf-8") as f:
                self.__data = json.load(f)
        else:
            self.__data = {}
        self.txt_list = []

    def __del__(self):
        pass

    def __save(self):
        with open(os.path.join(self.__path, "bosslock.json"), "w", encoding="utf-8") as f:
            json.dump(self.__data, f, ensure_ascii=False, indent=2)

    def __apply_lock(self, comment=None):
        now = int(time.time())
        if self.__data.get(self.__groupid, [0])[0] == 0:
            self.__data[self.__groupid] = [
                1,  # 0无锁，1有锁
                self.__qqid,
                self.__nickname,
                now,
                comment]
            self.txt_list.append(self.__nickname+"已锁定boss")
            self.__save()
        else:
            bef = now - self.__data[self.__groupid][3]
            self.txt_list.append("申请失败，{}在{}分{}秒前锁定了boss".format(
                self.__data[self.__groupid][2],
                bef // 60,
                bef % 60))
            if len(self.__data[self.__groupid]) == 5 and self.__data[self.__groupid][4] != None:
                self.txt_list.append("留言："+self.__data[self.__groupid][4])

    def __cancel_lock(self):
        if self.__data.get(self.__groupid, [0])[0] == 0:
            self.txt_list.append("boss没有被锁定")
        else:
            if self.__data[self.__groupid][1] == self.__qqid:
                del self.__data[self.__groupid]
                self.txt_list.append("boss已解锁")
                self.__save()
            else:
                bef = int(time.time()) - self.__data[self.__groupid][3]
                self.txt_list.append("{}在{}分{}秒前锁定了boss".format(
                    self.__data[self.__groupid][2],
                    bef // 60,
                    bef % 60))
                if bef > 180:
                    self.txt_list.append("你可以发送“#踢出队列”将其踢出")
                else:
                    self.txt_list.append("{}秒后你可以将其踢出".format(180-bef))

    def __delete_lock(self):
        if self.__data.get(self.__groupid, [0])[0] == 0:
            self.txt_list.append("boss没有被锁定")
        else:
            bef = int(time.time()) - self.__data[self.__groupid][3]
            if bef > 180:
                del self.__data[self.__groupid]
                self.txt_list.append("boss已解锁")
                self.__save()
            else:
                self.txt_list.append(
                    "{}在{}分{}秒前锁定了boss，{}秒后你才可以将其踢出".format(
                        self.__data[self.__groupid][2],
                        bef // 60,
                        bef % 60,
                        180 - bef))

    @staticmethod
    def match(cmd):
        if cmd == "申请boss" or cmd == "锁定boss" or cmd == "申请出刀" or cmd == "申请撞刀" or cmd == "开始撞刀":
            return 1  # 加锁
        elif cmd == "解锁boss" or cmd == "出刀完毕" or cmd == "取消撞刀":
            return 2  # 自己解锁
        elif cmd == "踢出队列" or cmd == "强制解锁":
            return 3  # 他人解锁
        return 0

    def lockboss(self, cmd, func_num=None, comment=None):
        if func_num == None:
            func_num = self.match(cmd)
        if func_num == 1:
            self.__apply_lock(comment)
        elif func_num == 2:
            self.__cancel_lock()
        elif func_num == 3:
            self.__delete_lock()
        elif func_num == 0:
            self.txt_list.append("lok参数错误")

    def text(self):
        return "\n".join(self.txt_list)
