import csv
import json
import os
import time

import requests

from .yobot_errors import Server_error
from . import gen_pic, shorten_url


class Consult:
    Passive = True
    Active = False
    URL = "http://api.yobot.xyz/v2/nicknames/?type=csv"
    Feedback_URL = "http://api.yobot.xyz/v2/nicknames/?type=feedback&name="
    ShowSolution_URL = "http://io.yobot.monster/3.0.0-b/jjc_consult_solution/?s="

    def __init__(self, glo_setting: dict, *args, refresh_nickfile=False,  **kwargs):
        self.setting = glo_setting
        self.nickname = {}
        self.number = {}
        nickfile = os.path.join(glo_setting["dirname"], "nickname.csv")
        if refresh_nickfile or not os.path.exists(nickfile):
            res = requests.get(self.URL)
            if res.status_code != 200:
                raise Server_error(
                    "bad server response. code: "+str(res.status_code))
            with open(nickfile, "w", encoding="utf-8-sig") as f:
                f.write(res.text)
        with open(nickfile, encoding="utf-8-sig") as f:
            f_csv = csv.reader(f)
            for row in f_csv:
                for col in row[1:]:
                    self.nickname[col] = int(row[0])
                self.number[int(row[0])] = row[1]
        if glo_setting.get("show_jjc_solution", None) == "image":
            photopath = os.path.join(glo_setting["dirname"], "static", "pics")
            if not os.path.exists(photopath):
                os.makedirs(photopath)
                char_list = [charid + offset
                             for charid in self.number.keys()
                             for offset in (10, 30)]
                gen_pic.download_pics(char_list, photopath)

    def user_input(self, cmd: str, is_retry=False) -> dict:
        def_set = set()
        in_list = cmd.split()
        if len(in_list) == 1:
            return {"code": 2, "msg": "请将5个名称以空格分隔"}
        if len(in_list) > 5:
            return {"code": 5, "msg": "防守人数过多"}
        for index in in_list:
            item = self.nickname.get(index.lower(), None)
            if item is None:
                if is_retry:
                    try:
                        requests.get(self.Feedback_URL+index)
                    except requests.exceptions.ConnectionError:
                        msg = "没有找到【{}】，自动反馈失败，目前昵称表：{}".format(index, self.URL)
                    else:
                        msg = "没有找到【{}】，已自动反馈，目前昵称表：{}".format(index, self.URL)
                    return {
                        "code": 1,
                        "msg": msg}
                else:
                    self.__init__(self.setting, refresh_nickfile=True)
                    return self.user_input(cmd, True)
            def_set.add(item)
            def_lst = list(def_set)
        if len(def_lst) < 3:
            return {"code": 3, "msg": "防守人数过少"}
        return {"code": 0, "def_lst": def_lst}

    def jjcsearch(self, def_lst: list) -> str:
        key = self.setting.get('jjc_auth_key', None)
        if not key:
            return "此功能已失效"
        header = {
            'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/78.0.3904.87 Safari/537.36'),
            'authorization': key,
        }
        payload = {"_sign": "a", "def": def_lst, "nonce": "a",
                   "page": 1, "sort": 1, "ts": int(time.time()), "region": 1}
        try:
            data = requests.post('https://api.pcrdfans.com/x/v1/search',
                                 headers=header,
                                 data=json.dumps(payload))
        except requests.exceptions.ConnectionError:
            return "无法连接服务器"
        if data.status_code >= 400:
            return "无法处理的服务器状态码：{}".format(data.status_code)
        res = json.loads(data.text)
        if(res["code"] == 0):
            show_jjc_solution = self.setting.get("show_jjc_solution", "url")
            if show_jjc_solution == "url":
                reply = self.dump_url(res)
            elif show_jjc_solution == "text":
                reply = self.dump_text(res)
            elif show_jjc_solution == "image":
                reply = self.dump_photo(res)
        else:
            return ("error code: {}, message : {}".format(
                res["code"], res["message"]))
        return reply

    def dump_text(self, res: dict) -> str:
        reply = ""
        reply += "从pcrdfans.com找到{}条记录\n".format(
            len(res["data"]["result"]))
        line = "\n=======\n"
        for result in res["data"]["result"]:
            reply += line
            line = "\n-------\n"
            text = ""
            for atker in result["atk"]:
                text += self.number.get(
                    atker["id"], "unknown:{}".format(atker["id"]))
                if atker["equip"] or atker["star"]:
                    cmt = ""
                    if atker["star"]:
                        cmt += str(atker["star"])
                    if atker["equip"]:
                        cmt += "专"
                    text += "("+cmt+")"
                text += " "
            text += "({},{}赞{}踩)".format(
                result["updated"][2:10],
                result["up"],
                result["down"])
            reply += text
        return reply

    def dump_url(self, res: dict) -> str:
        if len(res["data"]["result"]) == 0:
            return "从pcrdfans.com没有找到解法"
        solution = []
        for result in res["data"]["result"]:
            team = []
            team.append("{}.{}.{}".format(
                result["up"],
                result["down"],
                result["updated"][0:10].replace("-", ".")
            ))
            for atker in result["atk"]:
                char_id = atker["id"]+(
                    30 if atker["star"] < 6 else 60)
                team.append("{}.{}.{}".format(
                    char_id,
                    atker["star"],
                    (1 if atker["equip"] else 0)
                ))
            solution.append("_".join(team))
        url = self.ShowSolution_URL + "-".join(solution)
        url = shorten_url.shorten(url)
        return "找到解法：" + url

    def dump_photo(self, res: dict) -> str:
        if len(res["data"]["result"]) == 0:
            return "从pcrdfans.com没有找到解法"
        pic_file = gen_pic.teams_pic(res["data"]["result"])
        return "[CQ:image,file=file:///{}]".format(pic_file)

    @staticmethod
    def match(cmd: str) -> int:
        if cmd == "jjc查询":
            return 1
        elif cmd.startswith("jjc查询"):
            return 2
        else:
            return 0

    def execute(self, match_num: int, msg: dict) -> dict:
        if self.setting.get("jjc_consult", True) == False:
            reply = "此功能未启用"
        elif match_num == 1:
            reply = "请接5个昵称，空格分隔"
        else:
            anlz = self.user_input(msg["raw_message"][5:])
            if anlz["code"] == 0:
                reply = self.jjcsearch(anlz["def_lst"])
            else:
                reply = anlz["msg"]
        return {
            "reply": reply,
            "block": True
        }
