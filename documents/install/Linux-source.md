# Linux 源码运行

::: tip

阅读此章节前，您需要了解：

- Linux 基本用法
- docker
- git

:::

由于 酷Q 机器人原生于 Windows 系统，所以 Linux 上运行只能使用 wine（类似于虚拟机）来运行 酷Q，使用 Docker 可以直接部署。  

由于 wine 与原生 Windows 差别较大，很多 酷Q 插件无法在 wine 中运行。

Linux 用户可以使用 Docker 部署，具体请看[这里](./docker.md)。

Linux 用户可以使用 mirai 部署，具体请看[这里](./Linux-cqhttp-mirai.md)。

**Linux运行存在问题较多，不推荐使用**，如果你坚持使用Linux来部署机器人，可以参考本文步骤。

## 前言

“酷Q机器人”是一个QQ的入口，“httpapi”是酷Q机器人的插件，yobot则是httpapi的插件。

为了使用yobot三代，本文将指导安装：酷Q机器人（用于接发QQ消息）、yobot服务（用于处理消息）。

## 准备服务器

虽然在自己电脑运行也可以，不过最好能租一个服务器，以便长期挂机和提供web服务

[服务器推荐](./server.md)

## 安装酷Q机器人

### 下载

#### Linux 使用

参考：[httpapi插件文档](https://cqhttp.cc/docs/#/Docker)

请参考上面的文档进行部署，运行参数中“事件上报地址”可不填，后续手动修改配置文件。

### 配置

参考：[httpapi插件文档配置说明](https://cqhttp.cc/docs/#/Configuration)  

配置文件位于：`<酷Q运行目录>coolq/app/io.github.richardchien.coolqhttpapi/config/general.json`或`<QQ号>.json`，将其修改为[这里](./config.md)的配置，如果启动过httpapi，会出现`QQ号.ini`文件，请将其删除。

**请注意：** docker 版本默认的网络模式为“桥接模式（bridge）”，此模式下与宿主机进行网络通信的ip地址为172.17.0.1，如果使用阿里云服务器，这个地址被占用则改为172.18.0.1，请将配置文件中127.0.0.1修改为这个地址。

或者可以将 docker 的网络模式修改为“宿主模式（host）”，此模式下 docker 与宿主机共用网段，通信的ip地址为127.0.0.1，不需要修改配置文件。

如果需要使用host模式，请在启动 docker 时添加参数 `--net=host`

配置正确后，启动 httpapi 插件后会反复出现如下都提示

![配置正确图片](https://img.yobot.win/yobot/8ba6b840bab3ac25.jpg)

## 运行 yobot 服务

### Linux 系统源码运行

源码运行需要使用 git 作为版本管理和更新工具，如果没有使用过 git 可以阅读：[git官网](https://git-scm.com/)，[git教程](https://www.runoob.com/git/git-tutorial.html)

确保 python 版本至少为 3.6

下载源码 `git clone https://github.com/pcrbot/yobot.git`

或者使用国内源 `git clone https://gitee.com/yobot/yobot.git`

请尽量使用 git clone 而不是 download zip ，否则无法自动更新版本

进入目录 `cd yobot`

安装依赖 `pip3 install -r src/client/requirements.txt`  
（如果在国内建议加上参数 `-i https://pypi.tuna.tsinghua.edu.cn/simple`）

启动：

```shell
cd src/client

# 建议使用sreen或类似的终端复用器
screen -S yobot

python3 main.py  # 生成yobotg.sh
sh yobotg.sh  # 如果python的路径不是python3，请手动修改这个脚本
# 然后按下 Ctrl+a, d 连续组合键暂离这个会话（这个快捷键只适用于screen）

## 或者使用nohup
# nohup sh yobotg.sh &
```

如果需要更换主机地址、端口等信息请修改src\client\yobot_config.json配置文件。

![windows下正确启动图](https://img.yobot.win/yobot/aaf38d1a5cbc1c87.jpg)

![windows下正确yobot与httpapi成功通信](https://img.yobot.win/yobot/8179fdd1e46690b2.jpg)

### 验证安装

向机器人发送“version”，机器人会回复当前版本

## 常见问题

### 如何修改运行的端口号

需要修改服务程序的端口号和httpapi的配置文件

服务程序的配置文件在src/client/yobot_config.json，port字段就是端口号，默认值为9222，可以修改为8000至65535之间的数。

httpapi的配置文件如[配置小节](#配置)所示，请将文件中默认端口9222(三处)改为与服务程序相同的端口号。

### 其他问题

见[FAQ](../usage/faq.md)

## 注意事项

* **请不要使用重要的QQ号作为机器人**
* 系统至少要windows 7或者windows server 2008
* 机器人的数据都是分群存储的，一个机器人可以服务多个群
* 本机器人不包含“签到”、“宠物”等通用功能，如果需要可以在[酷Q插件社区](https://cqp.cc/b/app)搜索下载。
* 发送图片，发送语音等功能必须购买高级版才能使用，yobot三代所有功能均可用文字实现，不需要高级版

容易引起封号的行为：

* 异地登录后立刻修改昵称头像（可以先修改再异地登录）
* 新注册的号在机房ip登录（ip真人鉴别有很多，比如[这个](https://ip.rtbasia.com/)）
* 机器人大量地发长消息（尤其是抽卡，条件允许可以改用图片抽卡）
* 机器人24小时不停发消息（如果真的有需求可以让两个账号轮班）
* 账号在短时间内加了大量的群（可以慢慢加，最好不超过10个群）
* 大量高危账号在同一个ip登录（可以慢慢加，一台服务器最好不超过5个账号）

## 开始 web 模式

[开启方法](../usage/web-mode.md)
