import asyncio
import json
import sys

from aiocqhttp import CQHttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import yobot

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
    to_sends = func()
    tasks = [rcnb.send_msg(**kwargs) for kwargs in to_sends]
    await asyncio.gather(*tasks)


def ask_for_input(msg: str, default: str = "",
                  convert: callable = None, check: callable = None):
    flag = True
    while flag:
        print(msg, end="")
        instr = input()
        if instr == "":
            instr = default
        if check is not None:
            if check(instr):
                flag = False
            else:
                print("输入无效")
        else:
            flag = False
    if convert is not None:
        return convert(instr)
    else:
        return instr


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

    rcnb.run(host=host, port=port)
