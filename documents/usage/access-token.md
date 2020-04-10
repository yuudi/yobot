# access token

## access token 有什么用

当机器人客户端与 yobot 应用连接时，`access token` 会用于验证身份。不设置 `access token` 意味着允许机器人执行来自任何人的请求，造成安全隐患。

## 如何修改机器人的 access token

进入yobot的[配置文件](./configuration.md)，将其中 `access_token` 修改为任意字符串（尽量复杂）

进入httpapi的`<应用目录/config/<general|qq号>.json`（如下图），将其中 `access_token` 修改为刚才一样的字符串

![httpapi配置文件](https://x.jingzhidh.com/img/yobot/f6772ec9.png)
