"""
实例2：利用flask作为网页聊天室
（过于简陋，仅用作测试与参考）

未适配3.2版本
"""

import asyncio
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart, request

from yobot import Yobot


class Borad:
    head = '<!DOCTYPE html><html><head><style>.guest{color:blue}.admin{color:red}</style><script src="https://cdn.staticfile.org/jquery/3.4.1/jquery.min.js"></script><script>$(document).ready(function(){$("#send").click(function(){let send=$("#text").val();window.location.href=send})})</script></head><body><input type="text"id="text"><input type="button"value="发送"id="send">'
    foot = "</body></html>"

    def __init__(self):
        self.board = []

    def add_msg(self, usr, role, msg):
        taim = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        self.board.append((usr, role, taim, msg))
        if len(self.board) > 100:
            record = self.board[:-50]
            self.board = self.board[-50:]
            filename = "record_{}.txt".format(
                time.strftime("%Y%m%d_%H%M%S", time.localtime()))
            with open(filename, "w", encoding="utf-8") as f:
                for (usr, role, taim, msg) in record:
                    f.write("{} {} {}:\n{}\n\n".format(role, usr, taim, msg))

    def get_chat(self):
        content = ""
        for (usr, role, taim, msg) in self.board:
            content = '<p><usr class="{}">{}</usr>({}):<br>{}</p>'.format(
                role, usr, taim, msg
            ) + content
        return (self.head + content + self.foot)


app = Quart("chatroom")
bot = Yobot()
room = Borad()


@app.route("/room/<msg>")
async def _(msg):
    ip = request.remote_addr
    if msg != "view":
        room.add_msg(ip, "guest", msg)
    context = {
        "group_id": 1,
        "raw_message": msg,
        "message_type": "group",
        "sender": {
            "user_id": ip,
            "nickname": ip,
            "card": ip,
            "role": "member"
        }
    }
    reply = bot.proc(context)
    if reply != "" and reply is not None:
        room.add_msg("yobot", "admin", reply.replace("\n", "<br>"))
    return room.get_chat()


async def send_it(func):
    if asyncio.iscoroutinefunction(func):
        to_sends = await func()
    else:
        to_sends = func()
    send_set = {kwargs["message"] for kwargs in to_sends}
    for msg in list(send_set):
        room.add_msg("yobot", "admin", msg.replace("\n", "<br>"))


jobs = bot.active_jobs()
if jobs:
    sche = AsyncIOScheduler()
    for trigger, job in jobs:
        sche.add_job(func=send_it,
                     args=(job,),
                     trigger=trigger,
                     coalesce=True,
                     max_instances=1,
                     misfire_grace_time=60)
    sche.start()

app.run(host="0.0.0.0", port=80)
