# coding=utf-8

import json
import os
import sys
import time

import requests


class Check():

    def __init__(self):
        self.__path = os.path.dirname(sys.argv[0])

    def check(self):
        if os.path.exists(os.path.join(self.__path, "version.json")):
            f = open(os.path.join(self.__path, "version.json"),
                     "r+", encoding="utf-8")
            try:
                ver = json.load(f)
            except json.decoder.JSONDecodeError:
                ver = {"checktime": 1, "localver": 2000,
                       "url": "https://yuudi.github.io/yobot/ver.json"}
                f.seek(0)
                f.truncate()
                json.dump(ver, f, indent=2)
        else:
            f = open(os.path.join(self.__path, "version.json"),
                     "w", encoding="utf-8")
            ver = {"checktime": 1, "localver": 2000,
                   "url": "https://yuudi.github.io/yobot/ver.json"}
        now = int(time.time())
        if ver["checktime"] == 1:  # 已经发现新版本
            f.close()
            return "有新的版本可用，发送“#更新”唤起更新程序"
        elif ver["checktime"] < now:  # 到检查时间
            response = requests.get(ver["url"])
            if response.status_code != 200:  # 网页返回错误
                ver["checktime"] = now + 80000  # 下次再检查
                f.seek(0)
                f.truncate()
                json.dump(ver, f, indent=2)
                f.close()
                return None
            latest = json.loads(response.text)
            if latest["version"] > ver["localver"]:
                ver["checktime"] = 1  # 已经发现新版本
                f.seek(0)
                f.truncate()
                json.dump(ver, f, indent=2)
                f.close()
                return "有新的版本可用，发送“#更新”唤起更新程序"
            else:
                ver["checktime"] = now + 80000  # 每8万秒检查一次
                f.seek(0)
                f.truncate()
                json.dump(ver, f, indent=2)
                f.close()
                return None
        else:
            f.close()
            return None

    def update(self):
        app = os.path.join(self.__path, "updater.exe")
        if os.path.exists(app):
            os.system("start "+app)
            return "更新程序已开始，由于使用了备用的更新方式，本次更新完成不会有提示"
        else:
            return "更新程序丢失"
