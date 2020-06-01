"""
实例1：利用aiocqhttp作为httpapi的服务端
"""

import platform
import os
import sys

if platform.system() == "Linux":
    if "-g" not in sys.argv[1:]:
        with open("yobotg.sh", "w") as g:
            g.write("""
echo $$ > yobotg.pid
loop=true
while $loop
do
    loop=false
    {} -g
    if [ -f .YOBOT_RESTART ]
    then
        loop=true
        rm .YOBOT_RESTART
    fi
done
""".format('./yobot' if '_MEIPASS' in dir(sys) else 'python3 main.py'))
        print('请通过"sh yobotg.sh"启动')
        sys.exit()
    if os.path.exists('.YOBOT_RESTART'):
        os.remove('.YOBOT_RESTART')

import asyncio
import json
import time

import tzlocal
from aiocqhttp import CQHttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import yobot


def main():
    print("""==============================
              _           _
             | |         | |
  _   _  ___ | |__   ___ | |_
 | | | |/ _ \| '_ \ / _ \| __|
 | |_| | (_) | |_) | (_) | |_
  \__, |\___/|_.__/ \___/ \__|
   __/ |
  |___/
==============================""")
    print("正在初始化...")

    if os.path.exists('yobot_config.json'):
        basedir = "."
    else:
        basedir = "./yobot_data"
    if os.path.exists(os.path.join(basedir, "yobot_config.json")):
        try:
            with open(os.path.join(basedir, "yobot_config.json"), "r", encoding="utf-8-sig") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print('配置文件格式错误，请检查配置文件。三秒后关闭')
            time.sleep(3)
            raise e from e
        token = config.get("access_token", None)
        if token is None:
            print("警告：没有设置access_token，这会直接暴露机器人接口")
            print("详见https://yobot.win/usage/access-token/")
    else:
        token = None

    try:
        tzlocal.get_localzone()
    except:
        print("无法获取系统时区，请将系统时区设置为北京/上海时区")
        sys.exit()

    cqbot = CQHttp(access_token=token,
                   enable_http_post=False)
    sche = AsyncIOScheduler()
    bot = yobot.Yobot(data_path=basedir,
                      scheduler=sche,
                      quart_app=cqbot.server_app,
                      bot_api=cqbot._api,
                      )
    host = bot.glo_setting.get("host", "0.0.0.0")
    port = bot.glo_setting.get("port", 9222)

    @cqbot.on_message
    async def handle_msg(context):
        if context["message_type"] == "group" or context["message_type"] == "private":
            reply = await bot.proc_async(context)
        else:
            reply = None
        if isinstance(reply, str) and reply != "":
            return {'reply': reply,
                    'at_sender': False}
        else:
            return None

    async def send_it(func):
        if asyncio.iscoroutinefunction(func):
            to_sends = await func()
        else:
            to_sends = func()
        if to_sends is None:
            return
        for kwargs in to_sends:
            await asyncio.sleep(5)
            await cqbot.send_msg(**kwargs)

    jobs = bot.active_jobs()
    if jobs:
        for trigger, job in jobs:
            sche.add_job(func=send_it,
                         args=(job,),
                         trigger=trigger,
                         coalesce=True,
                         max_instances=1,
                         misfire_grace_time=60)
        sche.start()

    print("初始化完成，启动服务...")

    cqbot.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        loop=asyncio.get_event_loop(),
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCtrl-C")
        sys.exit(0)
