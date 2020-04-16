# 常见问题

## 酷Q 问题

### 需要购买 酷Q Pro 吗

yobot 不需要。（其他插件可能需要）

### 机器人群聊没有回复

新号、长期不登录的号、异地登录的号会被腾讯屏蔽一段时间。如果是这个原因，酷Q 日志会显示已成功发送。解决方法机器人挂机 3-5 天即可。

### 机器人群临时消息没有回复

新入群成员发送群临时消息失败，可能是因为缓存没有刷新。如果是这个原因，酷Q 日志会显示已找不到于目标的关系。解决方法等待一段时间或者重启机器人。

## mirai 问题

### mirai 如何使用

mirai 尚未稳定，稳定后本站会发布教程和一键安装包。如果想体验测试版可以参考[这里](https://github.com/mamoe/mirai)

## yobot 问题

### 机器人提供的网站无法登录

请参考[无法打开网页](./cannot-open-webpage.md)

### 如何修改机器人的设置

由主人向机器人私聊发送“登录”，登录后点击设置按钮即可。如果要手动修改配置文件请参考[这里](./configuration.md)。

### 如何修改机器人的 access_token

参考[这里](./access-token.md)。

### 如何添加自定义的新闻推送

使用源码运行时，在 `ybplugins/push_news.py` 文件第 33 行开始填写 RSS。或者在[插件社区](https://cqp.cc/b/app)下载专门的 RSS 推送插件。

### 如何删除公会战成员

在公会战面板的查刀页面中，选择要删除的成员点击删除。

### 这里没有我的问题

可以在[这里](https://github.com/yuudi/yobot/issues)提问，提问前可以阅读[正确的提问姿势](https://github.com/tangx/Stop-Ask-Questions-The-Stupid-Ways/blob/master/README.md)
