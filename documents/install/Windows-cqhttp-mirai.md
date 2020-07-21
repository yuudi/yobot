# Windows 使用 cqhttp-mirai 部署

## 部署过程

本文为便携版部署方式

### 部署 yobot

下载[yobot便携版](https://yobot.lanzous.com/b00nlr3ni)

解压后双击“yobot.exe”启动服务

![windows下正确启动图](https://img.yobot.win/yobot/aaf38d1a5cbc1c87.jpg)

### 部署 mirai

下载 miraiOK  
[miraiOK 64位](http://t.imlxy.net:64724/mirai/MiraiOK/miraiOK_windows_amd64.exe)
[miraiOK 32位](http://t.imlxy.net:64724/mirai/MiraiOK/miraiOK_windows_386.exe)

双击启动 miraiOK

下载 [CQHTTPMirai.jar](https://github.com/yyuueexxiinngg/cqhttp-mirai/releases/download/0.1.4/cqhttp-mirai-0.1.4-all.jar) 并放在 `.\plugins` 目录里

新建 CQHTTPMirai 配置文件在 `.\plugins\CQHTTPMirai\setting.yml`，修改配置文件如下（注意修改 QQ 号）

```yaml
# 要进行配置的QQ号 (Mirai支持多帐号登录, 故需要对每个帐号进行单独设置)
"1234567890":
  ws_reverse:
    enable: true
    postMessageFormat: string
    reverseHost: 127.0.0.1
    reversePort: 9222
    reversePath: /ws/
    accessToken: null
    reconnectInterval: 3000
# 详细说明请参考 https://github.com/yyuueexxiinngg/cqhttp-mirai
```

重新启动 miraiOK 并登录

在 mirai 控制台里登录 QQ `login 1234567890 ppaasswwdd`

部署完成

## 验证安装

向机器人发送“version”，机器人会回复当前版本

## 常见问题

见[FAQ](../usage/faq.md)

## 开启 web 访问

[开启方法](../usage/web-mode.md)
