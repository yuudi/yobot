# 使用酷Q安装

::: tip

开始使用前  
如果提供服务的QQ号是刚注册的、长期未使用的、异地登录的，则很容易被封禁。  
建议在服务器上将账号**挂机一周**再提供服务

yobot搭建难度约等于搭建网站的难度，请量力而行

:::

如果想租用或出租机器人，可以加群 {{ [770947581,1044314369,1067699252,774394459][Math.floor(Math.random()*4)] }}

选择一个安装教程：

## Windows 服务器：便携版（新手推荐）

最简单的运行方法

[快速使用](./Windows-quick-start.md)☚最简单

## Windows 服务器：源码运行

用 python 运行源码，可以方便地做一些小改动

[详细说明](./Windows-source.md)

## Linux 服务器：源码运行

在 Linux 或 MacOS 上用 python 运行源码，
同时在 docker 下使用 wine 运行酷Q。
由于不是原生环境，所以其他插件可能不兼容。

[详细说明](./Linux-source.md)

## Linux 服务器：Docker 部署

使用 Docker 一键部署。

[详细说明](./docker.md)

## 作为 nonebot 插件运行

如果想搭建一个高度自定义的机器人，可以使用 [nonebot](https://nonebot.cqp.moe/) 框架。（Python语言）

你可以在 Windows 或 Linux 或 MacOS 上运行 nonebot，将 yobot 作为 nonebot 的一个插件运行。

[详细说明](./nonebot-plugin.md)
