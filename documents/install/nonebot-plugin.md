# 作为 nonebot 插件运行

::: tip

yobot 从编写开始，nonebot 框架已经变化了很多，现在不再推荐作为 nonebot 插件运行。  
如果希望编写自定义的功能，建议将 yobot 与 nonebot 分别部署。  
如果想用其他编程语言制作机器人，可以在[这里](https://github.com/richardchien/coolq-http-api/blob/master/README.md#sdk%E5%BC%80%E5%8F%91%E6%A1%86%E6%9E%B6)找到相应的框架。

:::

使用前提：已经安装好[nonebot](https://nonebot.cqp.moe/)（或者其衍生物），创建好插件目录，并且**可以正常运行**

由于`nonebot`从`1.4`版本开始依赖`quart>=0.7`，这与本工具的依赖可能不兼容，建议使用`nonebot~=1.3.1 aiocqhttp~=0.6.8 quart~=0.6.15`，或将nonebot与本工具分开部署

[nonebot介绍](../usage/nonebot-introductions.md)

[nonebot教程](https://nonebot.cqp.moe/)

如果你还没有为 nonebot 建立仓库，请在 nonebot 工作目录下执行 `git init` 新建一个仓库。  

进入 nonebot 插件目录，添加 git 的子模块：  
`git submodule add https://github.com/yuudi/yobot.git`  
（或者使用国内源`https://gitee.com/yobot/yobot.git`）

安装依赖`pip install -r yobot/src/client/requirements.txt`，重新加载nonebot插件，安装完成

向机器人发送“version”、“帮助”，即可开始使用

## 注意事项

作为nonebot插件运行时，配置项中的`host`、`port`、`access_token`不会生效，这些配置会沿用nonebot中的设置

为了开启web模式，请配置nonebot的`host`字段为`0.0.0.0`，yobot的`yobot_data/yobot_config.json`中`public_address`内的端口号与nonebot配置中的`port`对应（如果你使用了反向代理，则`public_address`为代理后的地址）
