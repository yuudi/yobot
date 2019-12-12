import json
import os
import pickle
import random
import re
import sqlite3
import time
from typing import List, Union

import requests

from plugins.yobot_errors import Coding_error, Server_error


class Gacha:
    Passive = True
    Active = False
    URL = "http://api.yobot.xyz/3.1.4/pool.json"

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting
        self.pool_file_path = os.path.join(
            self.setting["dirname"], "pool3.json")
        self.pool_checktime = 0
        if not os.path.exists(self.pool_file_path):
            try:
                res = requests.get(self.URL)
            except requests.exceptions.ConnectionError:
                raise Server_error("连接服务器失败")
            if res.status_code != 200:
                raise Server_error(
                    "bad server response. code: "+str(res.status_code))
            with open(self.pool_file_path, "w", encoding="utf-8") as f:
                f.write(res.text)
            self._pool = json.loads(res.text)
        else:
            with open(self.pool_file_path, "r", encoding="utf-8") as f:
                try:
                    self._pool = json.load(f)
                except json.JSONDecodeError:
                    raise Coding_error("卡池文件解析错误，请检查卡池文件语法")

    def result(self) -> List[str]:
        prop = 0.
        result_list = []
        for p in self._pool["pool"].values():
            prop += p["prop"]
        for i in range(self._pool["settings"]["combo"] - 1):
            resu = random.random() * prop
            for p in self._pool["pool"].values():
                resu -= p["prop"]
                if resu < 0:
                    result_list.append(p.get("prefix", "") +
                                       random.choice(p["pool"]))
                    break
        for p in self._pool["pool"].values():
            prop += p["prop_last"]
        for i in range(self._pool["settings"]["combo"] - 1):
            resu = random.random() * prop
            for p in self._pool["pool"].values():
                resu -= p["prop_last"]
                if resu < 0:
                    result_list.append(p.get("prefix", "") +
                                       random.choice(p["pool"]))
                    break
        if self._pool["settings"]["shuffle"]:
            random.shuffle(result_list)
        return result_list

    def gacha(self, qqid: int, nickname: str) -> str:
        self.check_ver()
        db_exists = os.path.exists(os.path.join(
            self.setting["dirname"], "collections.db"))
        db_conn = sqlite3.connect(os.path.join(
            self.setting["dirname"], "collections.db"))
        db = db_conn.cursor()
        if not db_exists:
            db.execute(
                '''CREATE TABLE Colle(
                qqid INT PRIMARY KEY,
                colle BLOB,
                times SMALLINT,
                last_day CHARACTER(4),
                day_times TINYINT)''')
        today = time.strftime("%m%d")
        sql_info = list(db.execute(
            "SELECT colle,times,last_day,day_times FROM Colle WHERE qqid=?", (qqid,)))
        mem_exists = (len(sql_info) == 1)
        if mem_exists:
            info = pickle.loads(sql_info[0][0])
            times, last_day, day_times = sql_info[0][1:]
        else:
            info = {}
            times, last_day, day_times = 0, "", 0
        day_limit = self._pool["settings"]["day_limit"]
        if today != last_day:
            last_day = today
            day_times = 0
        if day_limit != 0 and day_times >= day_limit:
            return "{}今天已经抽了{}次了，明天再来吧".format(nickname, day_times)
        result = self.result()
        times += 1
        day_times += 1
        reply = ""
        reply += "{}第{}抽：".format(nickname, times)
        for char in result:
            if char in info:
                info[char] += 1
                reply += "\n{}({})".format(char, info[char])
            else:
                info[char] = 1
                reply += "\n{}(new)".format(char)
        sql_info = pickle.dumps(info)
        if mem_exists:
            db.execute("UPDATE Colle SET colle=?, times=?, last_day=?, day_times=? WHERE qqid=?",
                       (sql_info, times, last_day, day_times, qqid))
        else:
            db.execute("INSERT INTO Colle (qqid,colle,times,last_day,day_times) VALUES(?,?,?,?,?)",
                       (qqid, sql_info, times, last_day, day_times))
        db_conn.commit()
        db_conn.close()
        return reply

    def show_colle(self, qqid, nickname, cmd: Union[None, str] = None) -> str:
        if not os.path.exists(os.path.join(self.setting["dirname"], "collections.db")):
            return "没有仓库"
        moreqq_list = []
        if cmd != None:
            pattern = r"(?<=\[CQ:at,qq=)\d+(?=\])"
            moreqq_list = [int(x) for x in re.findall(pattern, cmd)]
        db_conn = sqlite3.connect(os.path.join(
            self.setting["dirname"], "collections.db"))
        db = db_conn.cursor()
        sql_info = list(db.execute(
            "SELECT colle FROM Colle WHERE qqid=?", (qqid,)))
        if len(sql_info) != 1:
            db_conn.close()
            return nickname + "的仓库为空"
        colle = pickle.loads(sql_info[0][0])
        more_colle = []
        for other_qq in moreqq_list:
            sql_info = list(db.execute(
                "SELECT colle FROM Colle WHERE qqid=?", (other_qq,)))
            if len(sql_info) != 1:
                db_conn.close()
                return "[CQ:at,qq={}]的仓库为空".format(other_qq)
            more_colle.append(pickle.loads(sql_info[0][0]))
        if not os.path.exists(os.path.join(self.setting["dirname"], "temp")):
            os.mkdir(os.path.join(self.setting["dirname"], "temp"))
        colle_file = os.path.join(
            self.setting["dirname"], "temp",
            str(qqid)+time.strftime("_%Y%m%d_%H%M%S", time.localtime())+".csv")
        showed_colle = set(colle)
        for item in more_colle:
            showed_colle = showed_colle.union(item)
        with open(colle_file, "w", encoding="utf-8-sig") as f:
            f.write("角色,"+nickname)
            for memb in moreqq_list:
                f.write(",")
                try:
                    # 使用老李api
                    res = requests.get(
                        "http://laoliapi.cn/king/qq.php?qq=" + str(memb))
                    if res.status_code == 200:
                        f.write(json.loads(res.text).get("name", str(memb)))
                    else:
                        f.write(str(memb))
                except requests.exceptions.ConnectionError:
                    f.write(str(memb))
            f.write("\n")
            for char in sorted(showed_colle):
                f.write(char + "," + str(colle.get(char, 0)))
                for item in more_colle:
                    f.write("," + str(item.get(char, 0)))
                f.write("\n")
        with open(colle_file, 'rb') as f:
            files = {'file': f}
            try:
                response = requests.post(
                    'http://api.yobot.xyz/v2/reports/', files=files)
            except requests.exceptions.ConnectionError as c:
                error = "无法连接到{}，错误信息：{}".format('api.yobot.xyz', c)
                print(error)
                return error
        p = response.text
        reply = (nickname + "的仓库：" + p)
        db_conn.close()
        return reply

    def check_ver(self) -> None:
        auto_update = self._pool["settings"]["auto_update"]
        if not auto_update:
            return
        now = int(time.time())
        if self.pool_checktime < now:
            try:
                res = requests.get(self.URL)
            except requests.exceptions.ConnectionError as c:
                print("无法连接到{}，错误信息：{}".format(self.URL, c))
                return
            if res.status_code == 200:
                online_ver = json.loads(res.text)
                if self._pool["info"]["name"] != online_ver["info"]["name"]:
                    self._pool = online_ver
                    with open(self.pool_file_path, "w", encoding="utf-8") as pf:
                        pf.write(res.text)
                    print("卡池已自动更新，目前卡池：" + self._pool["info"]["name"])
                self.pool_checktime = now + 80000

    @staticmethod
    def match(cmd: str) -> int:
        if cmd == "十连" or cmd == "十连抽":
            return 1
        elif cmd.startswith("仓库"):
            return 4
        else:
            return 0

    def execute(self, func_num: int, msg: dict):
        if ((
                msg["message_type"] == "group"
                and not self.setting.get("gacha_on", True))
            or (
                msg["message_type"] == "private"
                and not self.setting.get("gacha_private_on", True))):
            reply = "功能已关闭"
        elif func_num == 1:
            reply = self.gacha(
                qqid=msg["sender"]["user_id"],
                nickname=msg["sender"]["card"])
        elif func_num == 4:
            reply = self.show_colle(
                qqid=msg["sender"]["user_id"],
                nickname=msg["sender"]["card"],
                cmd=msg["raw_message"][2:])
        return {
            "reply": reply,
            "block": True
        }
