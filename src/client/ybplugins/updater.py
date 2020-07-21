import json
import os
import platform
import random
import shutil
import sys
import zipfile
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import aiohttp
from aiocqhttp.api import Api
from apscheduler.triggers.cron import CronTrigger


class Updater:
    Passive = True
    Active = True
    Request = False

    def __init__(self, glo_setting: dict, bot_api: Api, *args, **kwargs):
        self.evn = glo_setting["verinfo"]["run-as"]
        self.path = glo_setting["dirname"]
        self.working_path = os.path.abspath(".")
        self.ver = glo_setting["verinfo"]
        self.setting = glo_setting
        self.api = bot_api
        self.working = False

        with open(os.path.join(glo_setting['dirname'], 'yobot.pid'), 'w') as f:
            f.write(str(os.getpid()))

    async def send_reply(self, context: Dict[str, Any],
                         message: Union[str, Dict[str, Any], List[Dict[str, Any]]],
                         **kwargs) -> Optional[Dict[str, Any]]:
        context = context.copy()
        context['message'] = message
        context.update(kwargs)
        if 'message_type' not in context:
            if 'group_id' in context:
                context['message_type'] = 'group'
            elif 'discuss_id' in context:
                context['message_type'] = 'discuss'
            elif 'user_id' in context:
                context['message_type'] = 'private'

        return await self.api.send_msg(**context)

    async def windows_update_async(self, force: bool = False, test_ver: int = 0):
        test_version = ["stable", "beta", "alpha"][test_ver]
        if not os.path.exists(os.path.join(self.path, "temp")):
            os.mkdir(os.path.join(self.path, "temp"))
        server_available = False
        for url in self.ver["check_url"]:
            try:
                async with aiohttp.request('GET', url=url) as response:
                    if response.status == 200:
                        res = await response.text()
                        server_available = True
                        break
            except:
                continue
        if not server_available:
            return "无法连接服务器"
        verinfo = json.loads(res)
        verinfo = verinfo[test_version]
        if not (force or verinfo["version"] > self.ver["ver_id"]):
            return "已经是最新版本"
        try:
            async with aiohttp.request('GET', url=verinfo["url"]) as response:
                if response.status != 200:
                    return verinfo["url"] + " code: " + str(response.status)
                content = await response.read()
        except:
            return "下载失败：{}".format(verinfo["url"])
        fname = os.path.basename(verinfo["url"])
        with open(os.path.join(self.path, "temp", fname), "wb") as f:
            f.write(content)
        verstr = str(verinfo["version"])
        if not os.path.exists(os.path.join(self.path, "temp", verstr)):
            os.mkdir(os.path.join(self.path, "temp", verstr))
        with zipfile.ZipFile(os.path.join(self.path, "temp", fname), "r") as z:
            z.extractall(path=os.path.join(self.path, "temp", verstr))
        os.remove(os.path.join(self.path, "temp", fname))
        shutil.move(os.path.join(self.path, "temp", verstr, "yobot.exe"),
                    os.path.join(self.working_path, "yobot.new.exe"))
        cmd = '''
            cd '{}'
            ping 127.0.0.1 -n 2 >nul
            taskkill /pid {} /f >nul
            ping 127.0.0.1 -n 3 >nul
            del yobot.exe
            ren yobot.new.exe yobot.exe
            powershell Start-Process -FilePath "yobot.exe"
            '''.format(self.working_path, os.getpid())
        with open(os.path.join(self.path, "update.bat"), "w") as f:
            f.write(cmd)
        os.system("powershell Start-Process -FilePath '{}'".format(
            os.path.join(self.path, "update.bat")))
        sys.exit()

    async def windows_update_git_async(self, force: bool = False, test_ver: int = 0):
        test_version = ["stable", "beta", "alpha"][test_ver]
        pullcheck = self.check_commit(force)
        if pullcheck is not None:
            return pullcheck
        server_available = False
        for url in self.ver["check_url"]:
            try:
                async with aiohttp.request('GET', url=url) as response:
                    if response.status == 200:
                        res = await response.text()
                        server_available = True
                        break
            except:
                continue
        if not server_available:
            return "无法连接服务器"
        verinfo = json.loads(res)
        verinfo = verinfo[test_version]
        if not (force or verinfo["version"] > self.ver["ver_id"]):
            return "已经是最新版本"
        git_dir = os.path.dirname(os.path.dirname(self.working_path))
        cmd = '''
        cd '{}'
        taskkill /pid {} /f
        git pull
        ping 127.0.0.1 -n 3 >nul
        powershell Start-Process -FilePath "python.exe" -ArgumentList '{}'
        '''.format(self.path, os.getpid(), os.path.join(self.working_path, "main.py"))
        with open(os.path.join(git_dir, "update.bat"), "w") as f:
            f.write(cmd)
        os.system("powershell Start-Process -FilePath '{}'".format(
            os.path.join(git_dir, "update.bat")))
        sys.exit()

    async def linux_update_async(self, force: bool = False, test_ver: int = 0):
        if self.evn == "linux-exe":
            return "Linux 便携版暂时无法自动更新"
        test_version = ["stable", "beta", "alpha"][test_ver]
        pullcheck = self.check_commit(force)
        if pullcheck is not None:
            return pullcheck
        for url in self.ver["check_url"]:
            try:
                async with aiohttp.request('GET', url=url) as response:
                    if response.status == 200:
                        res = await response.text()
                        server_available = True
                        break
            except:
                continue
        if not server_available:
            return "无法连接服务器"
        verinfo = json.loads(res)
        verinfo = verinfo[test_version]
        if not (force or verinfo["version"] > self.ver["ver_id"]):
            return "已经是最新版本"
        git_dir = os.path.dirname(os.path.dirname(self.working_path))
        os.system(f'cd "{git_dir}" ; git pull')
        open('.YOBOT_RESTART', 'w').close()
        sys.exit(10)

    def check_commit(self, force: bool = False):
        if not self.ver["commited"]:
            if self.ver["ver_name"] == "无法检测版本":
                return "没有版本信息，无法更新"
            return "存在未提交的修改，无法自动更新"
        if not force and self.ver["extra_commit"]:
            return "存在额外的提交，建议手动更新\n发送“强制更新”以忽略检查"
        return None

    def restart(self):
        self_pid = os.getpid()
        if platform.system() == "Windows":
            if self.evn == "exe":
                cmd = '''
                    ping 127.0.0.1 -n 2 >nul
                    taskkill /pid {} /f >nul
                    ping 127.0.0.1 -n 3 >nul
                    powershell Start-Process -FilePath '{}'
                    '''.format(self_pid, os.path.join(self.working_path, "yobot.exe"))
            elif self.evn == "py" or self.evn == "python":
                cmd = '''
                    ping 127.0.0.1 -n 2 >nul
                    taskkill /pid {} /f >nul
                    ping 127.0.0.1 -n 3 >nul
                    powershell Start-Process -FilePath "python.exe" -ArgumentList '{}'
                    '''.format(self_pid, os.path.join(self.working_path, "main.py"))
            with open(os.path.join(self.path, "restart.bat"), "w") as f:
                f.write(cmd)
            os.system("powershell Start-Process -FilePath '{}'".format(
                      os.path.join(self.path, "restart.bat")))
            sys.exit(10)
        else:
            open('.YOBOT_RESTART', 'w').close()
            sys.exit(10)

    @staticmethod
    def match(cmd: str) -> int:
        if cmd.startswith("更新"):
            para = cmd[2:]
            match = 0x10
        elif cmd.startswith("强制更新"):
            para = cmd[4:]
            match = 0x20
        elif cmd == "重启" or cmd == "重新启动":
            return 0x40
        else:
            return 0
        para = para.replace(" ", "")
        if para == "alpha":
            ver = 0
        elif para == "beta":
            ver = 0
        elif para == "":
            ver = 0
        else:
            return 0
        return match | ver

    async def execute_v2(self, match_num: int, msg: dict = {}) -> dict:
        if self.evn == "nonebot-plugin":
            return "作为插件无法这么做"

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

        if match_num == 0x40:
            if self.evn == "nonebot-plugin":
                return "作为插件无法这么做"
            await self.send_reply(msg, '正在重新启动yobot')
            reply = self.restart()
            return {"reply": reply, "block": True}
        match = match_num & 0xf0
        ver = match_num & 0x0f
        if match == 0x10:
            force = False
        elif match == 0x20:
            force = True
        if platform.system() == "Windows":
            if self.evn == "exe":
                await self.send_reply(msg, '开始自动下载更新')
                reply = await self.windows_update_async(force, ver)
            elif self.evn == "py" or self.evn == "python":
                await self.send_reply(msg, '开始自动拉取git更新')
                reply = await self.windows_update_git_async(force, ver)
        else:
            await self.send_reply(msg, '开始自动拉取git更新')
            reply = await self.linux_update_async(force, ver)
        return {
            "reply": reply,
            "block": True
        }

    async def execute_async(self, *args, **kwargs):
        if self.working:
            return '正在更新中，请稍等'
        self.working = True
        try:
            return await self.execute_v2(*args, **kwargs)
        except Exception as e:
            raise e from e
            print(e)
        finally:
            self.working = False

    async def update_auto_async(self) -> List[Dict[str, Any]]:
        print("自动检查更新...")
        if self.working:
            print('正在更新中')
        self.working = True
        try:
            if platform.system() == "Windows":
                if self.evn == "exe":
                    reply = await self.windows_update_async()
                elif self.evn == "py" or self.evn == "python":
                    reply = await self.windows_update_git_async()
            else:
                reply = await self.linux_update_async()
        except Exception as e:
            print(e)
        finally:
            self.working = False
        print(reply)
        return []

    def jobs(self) -> Iterable[Tuple[CronTrigger, Callable[[], List[Dict[str, Any]]]]]:
        if not self.setting.get("auto_update", True):
            return tuple()
        time = self.setting.get("update-time", "03:30")
        hour, minute = time.split(":")
        trigger = CronTrigger(hour=hour, minute=minute)
        job = (trigger, self.update_auto_async)
        return (job,)


def rand_vername(seed, length=2):
    try:
        myrandom = random.Random(seed)
        word = ''
        for _ in range(length):
            a = myrandom.randint(0xb0, 0xd7)
            if a == 0xd7:
                b = myrandom.randint(0xa1, 0xf9)
            else:
                b = myrandom.randint(0xa1, 0xfe)
            val = f'{a:x}{b:x}'
            word += bytes.fromhex(val).decode('gb2312')
        return word
    except Exception as e:
        print(e)
        return str(seed)


def get_version(base_version: str, base_commit:  int) -> dict:
    if "_MEIPASS" in dir(sys):
        return {
            "run-as": "exe" if platform.system() == "Windows" else "linux-exe",
            "ver_name": "yobot{}便携版".format(base_version),
            "ver_id": 3300 + base_commit,
            "check_url": [
                "https://gitee.com/yobot/yobot/raw/master/docs/v3/ver.json",
            ]
        }
    try:
        with os.popen("git diff HEAD --stat") as r:
            text = r.read()
        if text != "":
            return {
                "run-as": "python",
                "commited": False,
                "ver_name": "yobot{}源码版\n存在未提交的修改".format(base_version)
            }
    except Exception as e:
        print(e)
        return {
            "run-as": "python",
            "commited": False,
            "ver_name": f"无法检测版本{base_version}"
        }
    try:
        vername = "yobot{}源码版".format(base_version)
        with os.popen("git rev-list --count HEAD") as r:
            summary = r.read()
        extra_commit = int(summary.strip())-base_commit
        if extra_commit:
            vername += "\n额外的提交：" + str(extra_commit)
            with os.popen("git rev-parse HEAD") as r:
                hash_ = r.read().strip()
            # vername += "\nhash: {}".format(hash_)
            vername += "\n哈希名: " + rand_vername(seed=hash_, length=2)
        return {
            "run-as": "python",
            "commited": True,
            "extra_commit": extra_commit,
            "ver_name": vername,
            "ver_id": 3300 + base_commit,
            "check_url": [
                "https://gitee.com/yobot/yobot/raw/master/docs/v3/ver.json",
            ],
        }
    except Exception as e:
        print(e)
        return {
            "run-as": "python",
            "commited": False,
            "ver_name": f"无法检测版本{base_version}"
        }
