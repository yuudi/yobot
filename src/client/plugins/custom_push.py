'''
自定义功能（主动推送）：

在这里可以编写自定义的功能，
编写完毕后记得 git commit，
想成为正式功能，欢迎发 pull request
（只接收pcr相关功能，最好发到GitHub，我不怎么看Gitee）

这个模块只是为了快速编写小功能，如果想编写完整插件可以使用：
https://github.com/richardchien/python-aiocqhttp
或者
https://github.com/richardchien/nonebot
'''


from typing import Any, Callable, Dict, Iterable, Tuple


class Custom_push:
    Passive = False  # 被动触发，即一问一答
    Active = True  # 主动触发，即定时任务

    def __init__(self, glo_setting: dict, *args, **kwargs):
        '''初始化，只在启动时执行一次'''
        pass

    def jobs(self) -> Iterable[Tuple[Any, Callable[[], Iterable[Dict[str, Any]]]]]:
        '''
        用可迭代对象的方法返回所有的定时任务，
        每个返回的定时任务是一个元组，
        第一个元素是apscheduler的触发器，
        第二个元素是需要定时执行的任务，
        这个任务是一个函数 不接收参数 返回一个可迭代对象，
        可迭代对象中是要发送的消息，
        每个消息是一个字典 包括发送方式、接收者、内容
        '''

        # 如果需要使用，请注释掉下面一行
        return ()  # 返回空的元组

        # 例子，每天13:55提醒打竞技场

        # 导入定时型触发器
        from apscheduler.triggers.cron import CronTrigger
        # 如果要使用间隔型触发器，请使用下面这个
        # from apscheduler.triggers.interval import IntervalTrigger

        # 触发器，每天13:55触发
        trigger = CronTrigger(hour=13, minute=55)

        # 要执行的函数
        def send_notice():
            print("时间到，正在发送消息")
            # 要发送的消息之一
            send_1 = {
                "message_type": "group",  # 发送群消息
                "group_id": 123456,  # 群号
                "message": "现在时间是13:55"
            }
            # 要发送的消息之二
            send_2 = {
                "message_type": "private",  # 发送私聊消息
                "user_id": 123456,  # QQ号
                "message": "现在时间是13:55"
            }
            return (send_1, send_2)  # 可以一次发送若干个消息

        # 一个触发器加一个函数组成一个任务
        job = (trigger, send_notice)

        # 返回所有的任务（如果只有一个任务，不要忘记加逗号）
        return (job,)

# 编写完成后将这个类加入yobot.py的plugins中
