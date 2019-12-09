import asyncio
import json
import sys

from aiocqhttp import CQHttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import yobot

print("正在初始化...")

rcnb = CQHttp(access_token='your-token',
              enable_http_post=False)

bot = yobot.Yobot()


@rcnb.on_message
async def handle_msg(context):
    if context["message_type"] == "group" or context["message_type"] == "private":
        reply = bot.proc(context)
    else:
        reply = None
    if reply != "" and reply is not None:
        return {'reply': reply,
                'at_sender': False}
    else:
        return None


async def send_it(func):
    if asyncio.iscoroutinefunction(func):
        to_sends = await func()
    else:
        to_sends = func()
    tasks = [rcnb.send_msg(**kwargs) for kwargs in to_sends]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        host, port = sys.argv[2].split(":")
        port = int(port)
    else:
        with open("yobot_config.json", "r") as f:
            config = json.load(f)
        host = config.get("host", "127.0.0.1")
        port = config.get("port", 9222)

    jobs = bot.active_jobs()
    if jobs:
        sche = AsyncIOScheduler()
        for trigger, job in jobs:
            sche.add_job(send_it, trigger=trigger, args=(job,))
        sche.start()

    print("初始化完成，启动服务...")

    rcnb.run(host=host, port=port)
