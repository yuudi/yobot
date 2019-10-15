# 使用方法
## 运行环境
在`python3.7.4`中通过测试，其他环境未测试
## 主程序
导入yobot并调用
```
import yobot
txtlist = yobot.yobot(groupid, qqid, nickname, msg)
```
输入四个参数均为字符串
输出为list包含若干个字符串

主文件`yobot.py`后面有一个例子

## 更新程序
运行`updater.py`，会从`version.json`里读取更新信息并在线更新