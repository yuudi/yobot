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
    python3 main.py -g
    if [ -f .YOBOT_RESTART ]
    then
        loop=true
        rm .YOBOT_RESTART
    fi
done
""")
        print('请通过"sh yobotg.sh"启动')
        sys.exit()
    if os.path.exists('.YOBOT_RESTART'):
        os.remove('.YOBOT_RESTART')

import asyncio
import json

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

    if os.path.exists("yobot_config.json"):
        with open("yobot_config.json", "r") as f:
            config = json.load(f)
        token = config.get("access_token", None)
        if token is None:
            print("警告：没有设置access_token，这会直接暴露机器人接口")
            print("详见https://yobot.win/usage/access-token/")
    else:
        token = None

    cqbot = CQHttp(access_token=token,
                   enable_http_post=False)
    sche = AsyncIOScheduler()
    bot = yobot.Yobot(data_path=".",
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
        tasks = [cqbot.send_msg(**kwargs) for kwargs in to_sends]
        await asyncio.gather(*tasks)

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
