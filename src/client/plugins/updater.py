import json
import os
import platform
import shutil
import sys
import zipfile

import requests


class Updater:
    def __init__(self, glo_setting: dict):
        self.evn = glo_setting["run-as"]
        self.path = glo_setting["dirname"]
        self.ver = glo_setting["version"]
        self.runable_powershell = self.get_runable_powershell()

    def check_ver(self) -> bool:
        return True

    def windows_update(self, force: bool = False, test_ver: int = 0):
        if not self.runable_powershell:
            return "无法更新，没有powershell权限，帮助页面https://yobot.xyz/p/648/"
        test_version = ["stable", "beta", "alpha"][test_ver]
        if not os.path.exists(os.path.join(self.path, "temp")):
            os.mkdir(os.path.join(self.path, "temp"))
        server_available = False
        for url in self.ver["check_url"]:
            try:
                response = requests.get(url)
            except requests.ConnectionError:
                continue
            if response.status_code == 200:
                server_available = True
                break
        if not server_available:
            return "无法连接服务器"
        verinfo = json.loads(response.text)
        verinfo = verinfo[test_version]
        if not (force or verinfo["version"] > self.ver["ver_id"]):
            return "已经是最新版本"
        try:
            download_file = requests.get(verinfo["url"])
        except:
            return "无法连接到{}".format(verinfo["url"])
        if download_file.status_code != 200:
            return verinfo["url"] + "code:" + str(download_file.status_code)
        fname = os.path.basename(verinfo["url"])
        with open(os.path.join(self.path, "temp", fname), "wb") as f:
            f.write(download_file.content)
        verstr = str(verinfo["version"])
        if not os.path.exists(os.path.join(self.path, "temp", verstr)):
            os.mkdir(os.path.join(self.path, "temp", verstr))
        with zipfile.ZipFile(os.path.join(self.path, "temp", fname), "r") as z:
            z.extractall(path=os.path.join(self.path, "temp", verstr))
        os.remove(os.path.join(self.path, "temp", fname))
        shutil.move(os.path.join(self.path, "temp", verstr, "yobot.exe"),
                    os.path.join(self.path, "yobot.new.exe"))
        cmd = '''
            start-sleep 2
            kill -processname yobot
            start-sleep 2
            Remove-Item "yobot.exe"
            rename-Item "yobot.new.exe" -NewName "yobot.exe"
            Start-Process -FilePath "yobot.exe"
            '''
        with open(os.path.join(self.path, "update.ps1"), "w") as f:
            f.write(cmd)
        os.system("powershell -file " + os.path.join(self.path, "update.ps1"))
        exit()

    def windows_update_git(self, force: bool = False, test_ver: int = 0):
        if not self.runable_powershell:
            return "无法更新，没有powershell权限，帮助页面https://yobot.xyz/p/648/"
        git_dir = os.path.dirname(os.path.dirname(self.path))
        cmd = '''
        git pull
        start-sleep 1
        Start-Process -FilePath "python.exe" -ArgumentList "{}"
        '''.format(os.path.join(self.path, "main.py"))
        with open(os.path.join(git_dir, "update.ps1"), "w") as f:
            f.write(cmd)
        os.system('powershell -file "'
                  + os.path.join(git_dir, "update.ps1") + '"')
        exit()

    def linux_update(self, force: bool = False, test_ver: int = 0):
        git_dir = os.path.dirname(os.path.dirname(self.path))
        cmd = '''
        cd "{}"
        git pull
        sleep 1s
        cd src/client
        python3 main.py
        '''.format(git_dir)
        with open(os.path.join(git_dir, "update.sh"), "w") as f:
            f.write(cmd)
        os.system("chmod u+x {0} && {0}".format(
            os.path.join(git_dir, "update.sh")))
        exit()

    @staticmethod
    def get_runable_powershell() -> bool:
        r = os.popen("powershell Get-ExecutionPolicy")
        text = r.read()
        if text == "Bypass\n" or text == "RemoteSigned\n" or text == "Unrestricted\n":
            return True
        else:
            # try:
            #     os.system("powershell Set-ExecutionPolice RemoteSigned")
            # r = os.popen("powershell Get-ExecutionPolicy")
            # text = r.read()
            # if text == "Bypass\n" or text == "RemoteSigned\n" or text == "Unrestricted\n":
            #     return True
            return False

    @staticmethod
    def match(cmd: str) -> int:
        if cmd.startswith("更新"):
            para = cmd[2:]
            match = 0x10
        elif cmd.startswith("强制更新"):
            para = cmd[4:]
            match = 0x20
        else:
            return 0
        para = para.replace(" ", "")
        if para == "alpha":
            ver = 2
        elif para == "beta":
            ver = 1
        else:
            ver = 0
        return match | ver

    def execute(self, match_num: int, msg: dict = {}) -> dict:
        super_admins = self.setting.get("super-admin", list())
        restrict = self.setting.get("setting-restrict", 3)
        if msg["sender"]["user_id"] in super_admins:
            role = 0
        else:
            role_str = msg["sender"].get("role", None)
            if role_str == "owner":
                role = 1
            elif role_str == "admin":
                role = 2
            else:
                role = 3
        if role > restrict:
            reply = "你的权限不足"
            return {"reply": reply, "block": True}

        match = match_num & 0xf0
        ver = match_num & 0x0f
        if match == 0x10:
            force = False
        elif match == 0x20:
            force = True
        if platform.system() == "Windows":
            if self.evn == "exe":
                reply = self.windows_update(force, ver)
            elif self.evn == "py" or self.evn == "python":
                reply = self.windows_update_git(force, ver)
        else:
            reply = self.linux_update(force, ver)
        return {
            "reply": reply,
            "block": True
        }
