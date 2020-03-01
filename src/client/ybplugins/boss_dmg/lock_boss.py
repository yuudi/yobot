# coding=utf-8

# todo:这个文件还没有为3.0修改过

# 屎山改不动了，放弃了😫

import json
import os.path
import time


class Lock():

    txt_list = []

    def __init__(self, baseinfo, basepath):
        """
        baseinfo=[群号，QQ号, 群名片]（字符串）
        """
        self._groupid = baseinfo[0]
        self._qqid = baseinfo[1]
        self._nickname = baseinfo[2]
        self._path = basepath
        if os.path.exists(os.path.join(self._path, "bosslock.json")):
            with open(os.path.join(self._path, "bosslock.json"), "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}
        self.txt_list = []

    def __del__(self):
        pass

    def _save(self):
        with open(os.path.join(self._path, "bosslock.json"), "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _apply_lock(self, comment=None):
        now = int(time.time())
        if self._data.get(self._groupid, [0])[0] == 0:
            self._data[self._groupid] = [
                1,  # 0无锁，1有锁
                self._qqid,
                self._nickname,
                now,
                comment]
            self.txt_list.append(self._nickname+"已锁定boss")
            self._save()
        else:
            bef = now - self._data[self._groupid][3]
            self.txt_list.append("申请失败，{}在{}分{}秒前锁定了boss".format(
                self._data[self._groupid][2],
                bef // 60,
                bef % 60))
            if len(self._data[self._groupid]) == 5 and self._data[self._groupid][4] != None:
                self.txt_list.append("留言："+self._data[self._groupid][4])

    def _cancel_lock(self):
        if self._data.get(self._groupid, [0])[0] == 0:
            self.txt_list.append("boss没有被锁定")
        else:
            if self._data[self._groupid][1] == self._qqid:
                del self._data[self._groupid]
                self.txt_list.append("boss已解锁")
                self._save()
            else:
                bef = int(time.time()) - self._data[self._groupid][3]
                self.txt_list.append("{}在{}分{}秒前锁定了boss".format(
                    self._data[self._groupid][2],
                    bef // 60,
                    bef % 60))
                if bef > 180:
                    self.txt_list.append("你可以发送“踢出队列”将其踢出")
                else:
                    self.txt_list.append("{}秒后你可以将其踢出".format(180-bef))

    def _delete_lock(self):
        if self._data.get(self._groupid, [0])[0] == 0:
            self.txt_list.append("boss没有被锁定")
        else:
            bef = int(time.time()) - self._data[self._groupid][3]
            if bef > 180:
                del self._data[self._groupid]
                self.txt_list.append("boss已解锁")
                self._save()
            else:
                self.txt_list.append(
                    "{}在{}分{}秒前锁定了boss，{}秒后你才可以将其踢出".format(
                        self._data[self._groupid][2],
                        bef // 60,
                        bef % 60,
                        180 - bef))

    def boss_challenged(self):
        if self._data.get(self._groupid, [0])[0] == 0:
            return
        elif self._data.get(self._groupid, [0, 0])[1] == self._qqid:
            # 只能解锁自己申请出刀的boss
            del self._data[self._groupid]
            self.txt_list.append("boss已解锁")
            self._save()
            return
    
    def on_tree(self):
        # 如果锁定boss的人挂树了就解锁boss
        if self._data.get(self._groupid, [0])[0] == 0:
            return
        elif self._data.get(self._groupid, [0, 0])[1] == self._qqid:
            del self._data[self._groupid]
            self.txt_list.append("boss已解锁")
            self._save()

    @staticmethod
    def match(cmd):
        cmd = cmd.split("//")[0]
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
            self._apply_lock(comment)
        elif func_num == 2:
            self._cancel_lock()
        elif func_num == 3:
            self._delete_lock()
        elif func_num == 0:
            self.txt_list.append("lok参数错误")

    def text(self):
        return "\n".join(self.txt_list)
