"""
# 实例3：作为nonebot的插件

## 加载方法：

### 将这个项目整个文件夹放在nonebot插件目录下

### 将这个项目转化为插件

运行`python nonebot_plugin.py make_plugin`

如果使用git，记得`git commit -a`
"""


if __name__ == "__main__":
    import sys
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

    filepath = os.path.abspath(os.path.join(os.getcwd(), "yobot.py"))
    with open(filepath, "r+") as f:
        codes = f.read()
        codes = codes.replace("from plugins import", "from .plugins import")
        f.seek(0)
        f.truncate()
        f.write(codes)

    filepath = os.path.abspath(os.path.join(os.getcwd(), "plugins", "updater.py"))
    with open(filepath, "r+") as f:
        codes = f.read()
        codes = codes.replace("yobot源码版", "yobot源码(插件)版")
        f.seek(0)
        f.truncate()
        f.write(codes)

    sys.exit()


from nonebot import get_bot, scheduler

from .yobot import Yobot


rcnb = get_bot()
bot = Yobot(data_path="./yobot_data")


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
