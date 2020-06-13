# Windows 使用 cqhttp-mirai 部署（测试）

## 部署过程

本文为便携版部署方式

### 部署 yobot

下载[yobot便携版](https://yobot.lanzous.com/b00nlr3ni)

解压后双击“yobot.exe”启动服务

![windows下正确启动图](https://vs.yixuedh.com/assets/img/yobot/aaf38d1a5cbc1c87.jpg)

### 部署 mirai

下载[mirai-installer](https://yobot.lanzous.com/id6owid)，并安装

启动 mirai

在 mirai 控制台里登录 QQ `login 123456789 ppaasswwdd`

在 mirai 控制台里安装 cqhttp-mirai `install CQHTTPMirai`

CQHTTPMirai 配置文件在 `mirai\plugins\CQHTTPMirai\setting.yml`，修改配置文件如下（注意修改 QQ 号）

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

重新启动 mirai 并登录

<!--
在 mirai 控制台里重新加载插件 `reload`
-->

部署完成

## 验证安装

向机器人发送“version”，机器人会回复当前版本

## 常见问题

见[FAQ](../usage/faq.md)

## 开启 web 访问

[开启方法](../usage/web-mode.md)
