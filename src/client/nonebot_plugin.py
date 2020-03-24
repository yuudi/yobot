"""
实例3：作为nonebot的插件

加载方法：

1.将这个项目整个文件夹放在nonebot插件目录下

2.将这个项目转化为插件
运行`python nonebot_plugin.py make_plugin`
如果使用git，记得`git commit -a`
"""

import sys

if __name__ == "__main__":
    import os

    if len(sys.argv) < 2 or sys.argv[1] != "make_plugin":
        raise ValueError("unknown command")

    def makefile(path, content="# doing nothing"):
        with open(path, "w") as f:
            f.write(content)

    filepath = os.path.abspath(os.path.join(os.getcwd(), "__init__.py"))
    makefile(filepath)
    filepath = os.path.abspath(os.path.join(os.getcwd(), "../__init__.py"))
    makefile(filepath)
    filepath = os.path.abspath(os.path.join(os.getcwd(), "../../__init__.py"))
    makefile(filepath, "from .src.client import nonebot_plugin")

    sys.exit()

from .yobot import Yobot
import asyncio

if "nonebot" in sys.modules:
    from nonebot import get_bot, scheduler
else:
    raise ValueError("plugin imported before noenbot imported")

verinfo = {
    "run-as": "nonebot-plugin",
    "ver_name": "yobot{}插件版".format(Yobot.Version),
}

cqbot = get_bot()
bot = Yobot(data_path="./yobot_data",
            verinfo=verinfo,
            scheduler=scheduler,
            quart_app=cqbot.server_app,
            bot_api=cqbot._api,
            )


@cqbot.on_message
async def handle_msg(context):
    if context["message_type"] == "group" or context["message_type"] == "private":
        reply = await bot.proc_async(context.copy())
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
    tasks = [cqbot.send_msg(**kwargs) for kwargs in to_sends]
    await asyncio.gather(*tasks)

jobs = bot.active_jobs()
if jobs:
    for trigger, job in jobs:
        scheduler.add_job(
            func=send_it,
            args=(job,),
            trigger=trigger,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=60,
        )

__plugin_name__ = 'yobot'
__plugin_usage__ = 'pcr assistant bot'
