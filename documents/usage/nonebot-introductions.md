# 介绍：Nonebot、HoshinoBot、可可萝·Android

先理一下机器人实现方法：

《酷Q》用于接收和发送消息，《httpapi》是酷Q的插件 用于将消息转化为http协议的通信，《yobot》是利用aiocphttp制作的通信服务端，可以处理消息并与与httpapi通信。

《nonebot》是基于aiocphttp制作的通信服务端 ，以插件的形式管理各个功能。《HoshinoBot》和《可可萝·Android》是nonebot的插件组，各自用一组插件来实现功能。所以，只需要将HoshinoBot和可可萝·Android的插件复制到一起，就可以同时拥有两个机器人的功能。

yobot和nonebot一样基于aiocphttp，本仓库已经可以直接作为nonebot插件使用。从而在nonebot里使用yobot，同时拥有更多插件的功能。

[使用方法](../install/nonebot-plugin.md)

[nonebot文档](https://nonebot.cqp.moe/)
