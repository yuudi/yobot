"""
实例1：利用aiocqhttp作为httpapi的服务端
"""

import asyncio
import json

from aiocqhttp import CQHttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import yobot


def main():
    print("正在初始化...")

    bot = yobot.Yobot()

    with open("yobot_config.json", "r") as f:
        config = json.load(f)
    host = config.get("host", "127.0.0.1")
    port = config.get("port", 9222)
    token = config.get("access_token", "your-token")

    rcnb = CQHttp(access_token=token,
                  enable_http_post=False)

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
        if to_sends is None:
            return
        tasks = [rcnb.send_msg(**kwargs) for kwargs in to_sends]
        await asyncio.gather(*tasks)

    # # 如果要使用WebHook，可以用如下方法
    # # WehHook的端口号与机器人端口号相同
    # app = rcnb.server_app

    # from quart import request
    # @app.route("/webhook",  # webhook路径
    #            methods=['POST', 'GET'],  # 允许get和post
    #            host="0.0.0.0")  # 允许所有网络访问
    # async def webhook():
    #     if request.method = "GET":
    #         return("use post!")
    #     data = await request.get_data()  # 如果方式是post，获取post内容
    #     text = data.decode("utf-8")  # 将post解码为字符串
    #     await rcnb.send_msg(message_type="private",  # 私聊发送消息
    #                         user_id=123456789,  # QQ号
    #                         # group_id=123456789, # 如果message_type是"group"则用group_id
    #                         message="text")  # 内容

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

    print("初始化完成，启动服务...")

    rcnb.run(host=host, port=port)


if __name__ == "__main__":
    main()
