# 使用方法

## 运行环境

在`python3.7.4`中通过测试，其他环境未测试

python最低要求为`python3.6`

## 主程序

导入yobot并调用

```python
import yobot
bot = yobot.Yobot()
reply = bot.proc(context)
```

其中：
`reply`是一个`str`；
`context`是一个`dict`，其结构为

```python
context = {
    "group_id": 12345, # 聊天编号（QQ群号）
    "raw_message": "你好", # 消息内容
    "sender": {
        "user_id": 456, # 用户编号（QQ号）
        "nickname": "nickname", # 用户昵称
        "role": "admin" # 用户身份
    }
}
```

主文件`main.py`是利用`aiocqhttp`的应用

## 增加功能

### 被动回复

在![custom.py](https://github.com/yuudi/yobot/tree/master/src/client/plugins/custom.py)文件中可以增加简单的功能，详见文件内描述

### 主动推送

在![custom_push.py](https://github.com/yuudi/yobot/tree/master/src/client/plugins/custom_push.py)文件中可以增加简单的推送功能，详见文件内描述

### RSS订阅与网页抓取

见![custom_push.py](https://github.com/yuudi/yobot/tree/master/src/client/plugins/spider/README.md)
