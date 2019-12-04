'''
自定义功能：

在这里可以编写自定义的功能，
编写完毕后记得 git commit，
想成为正式功能，欢迎发 pull request
（只接收pcr相关功能，最好发到GitHub，我不怎么看Gitee）

这个模块只是为了快速编写小功能，如果想编写完整插件可以使用：
https://github.com/richardchien/python-aiocqhttp
或者
https://github.com/richardchien/nonebot
'''


class Custom:
    Passive = True  # 被动触发，即一问一答
    Active = False  # 主动触发，即定时任务

    def __init__(self, glo_setting: dict, *args, **kwargs):
        '''初始化，只在启动时执行一次'''

        # 如果需要使用，请注释掉下面一行
        return

        # 获取全局设置，注意：全局设置影响所有功能
        self.settings = glo_setting

        # 将设置打印到屏幕上
        import json
        print(json.dumps(glo_setting, indent=4))

    @staticmethod
    def match(cmd: str) -> int:
        '''
        匹配要回复的命令，
        传入：接收到的消息（字符串），
        匹配成功返回非0，
        不匹配则返回0
        '''

        # 如果需要使用，请注释掉下面一行
        return 0  # 不处理任何消息

        if cmd == "你好":
            return 1
        elif cmd == "来份色图":
            return 2
        else:
            return 0

    def execute(self, match_num: int, msg: dict) -> dict:
        '''
        执行要回复的内容，
        传入：匹配码（就是上面函数的返回值），
        传入：完整事件（见：https://cqhttp.cc/docs/#/Post?id=事件列表），
        返回：见下面的注释
        '''

        if match_num == 1:
            reply = "世界"  # 回复一个字符串
        elif match_num == 2:
            # 回复一个字符串和一个图片
            reply = [
                {
                    "type": "text",
                    "data": {"text": "图来了"}
                },
                {
                    "type": "image",
                    "date": {
                        "file": "http://api.v3.yobot.xyz/draw.jpg",
                        "cache": "0",
                    }
                }
            ]
        return {
            "reply": reply,  # 具体回复格式请参考https://cqhttp.cc/docs/#/Message
            "block": True  # 是否直接返回，阻止后续执行
        }
