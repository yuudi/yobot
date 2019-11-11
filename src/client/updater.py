import json
import os
import platform
import shutil
import sys
import time
import zipfile

import requests


class Updater:
    def __init__(self, glo_setting: dict):
        self.path = glo_setting["dirname"]
        self.ver = glo_setting["version"]

    def check_ver(self) -> bool:
        return True

    def windows_update(self, force: bool = False):
        if not os.path.exists(os.path.join(self.path, "temp")):
            os.mkdir(os.path.join(self.path, "temp"))
        for url in self.ver["check_url"]:
            response = requests.get(url)
            if response.status_code == 200:
                break
        if response.status_code != 200:
            return 1
        verinfo = json.loads(response.text)
        if not (force or verinfo["version"] > ver["localver"]):
            return 2

        try:
            download_file = requests.get(verinfo["url"])
        except:
            print("无法连接到{}".format(verinfo["url"]))
            return 3
        if download_file.status_code != 200:
            print(verinfo["url"], "code:", download_file.status_code)
            return 4
        fname = os.path.basename(verinfo["url"])
        with open(os.path.join(self.path, "temp", fname), "wb") as f:
            f.write(download_file.content)
        verstr = str(verinfo["version"])
        if not os.path.exists(os.path.join(self.path, "temp", verstr)):
            os.mkdir(os.path.join(self.path, "temp", verstr))
        with zipfile.ZipFile(os.path.join(self.path, "temp", fname), "r") as z:
            z.extractall(path=os.path.join(self.path, "temp", verstr))
        os.remove(os.path.join(path, "temp", fname))
        shutil.move(os.path.join(path, "temp", verstr, "yobot.exe"),
                    os.path.join(path, "yobot.new.exe"))
        cmd = '''@echo off
            taskkill /f /im yobot.exe
            del yobot.exe
            ren yobot.new.exe yobot.exe
            yobot.exe
            '''
        with open(os.path.join(self.path,update.bat),"w") as f:
            f.write(cmd)
        os.system("ping 127.0.0.1>nul && start {}\\update.bat".format(self.path))
        exit()

    def linux_update(self, force: bool = False):
        git_dir = os.path.dirname(os.path.dirname(self.path))
        os.system("{}/update.sh".format(git_dir))
        exit()

    @staticmethod
    def match(cmd: str) -> int:
        if cmd == "更新":
            return 1
        elif cmd == "强制更新":
            return 2
        return 0

    def execute(self, match_num: int, msg: dict) -> dict:
        if match_num == 1:
            force = False
        elif match_num == 2:
            force = True
        if platform.system() == "Windows":
            reply = self.windows_update(force)
        else:
            reply = self.linux_update(force)
        return {
            "reply": reply,
            "block": True
        }
