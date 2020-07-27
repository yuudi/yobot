# Windows 源码运行

::: tip

阅读此章节前，您需要了解：

- git

:::

## 前言

“酷Q机器人”是一个QQ的入口，“httpapi”是酷Q机器人的插件，yobot则是httpapi的插件。

为了使用yobot三代，本文将指导安装：酷Q机器人（用于接发QQ消息）、yobot服务（用于处理消息）。

## 准备服务器

服务器能保证24小时在线和提供web服务

[服务器推荐](./server.md)  
服务器操作系统建议选择 Windows 7 或 Windows Server 2008

为了部署机器人你可能需要一些工具，这个[工具包](https://download.yobot.win/%E5%8F%AF%E8%83%BD%E7%94%A8%E5%88%B0%E7%9A%84%E5%B7%A5%E5%85%B7.zip)包含了git，python，java，notepad++，希望对你有所帮助。

## 安装酷Q机器人

### 下载

#### Windows 使用

yobot 三代基于酷Q机器人和 httpapi 插件实现
如果你第一次使用酷Q机器人，可以直接下载[酷Q-httpapi 整合包](https://yobot.lanzous.com/iXsLmdsixkh)

如果你已经使用过酷Q机器人，可以下载[httpapi 插件](https://yobot.lanzous.com/iQentdsixif)

如果你已经使用过 httpapi 插件，或者想额外开启一个 httpapi 插件，可以下载[httpapi 插件分身版](https://yobot.lanzous.com/iS5JSdsixli)

### 环境搭建

参考：[httpapi插件文档](https://cqhttp.cc/docs/)

如果你的windows不是最新版，可能无法启动httpapi插件，请安装Visual C++ 可再发行软件包（[点击下载](https://aka.ms/vs/16/release/vc_redist.x86.exe)）。如果你的系统是 Windows 7 或 Windows Server 2008、或者安装 Visual C++ 可再发行软件包之后仍然加载失败，则还需要安装通用 C 运行库更新（[点击进入官网](https://support.microsoft.com/zh-cn/help/3118401/update-for-universal-c-runtime-in-windows)，选择你系统对应的版本下载安装）

### 配置

参考：[httpapi插件文档配置说明](https://cqhttp.cc/docs/#/Configuration)

由于新装的 httpapi 启动时有时候会重置配置文件，所以如果 httpapi 启动后与下图不符请手动配置一下文件

配置文件位于：`<酷Q运行目录>data\app\io.github.richardchien.coolqhttpapi\config\general.json`或 *QQ号.json* ，将其修改为[这里](./config.md)的配置。

配置正确后，启动 httpapi 插件后会反复出现如下都提示

![配置正确图片](https://img.yobot.win/yobot/8ba6b840bab3ac25.jpg)

## 运行yobot服务

### Windows系统源码运行

源码运行需要使用git作为版本管理和更新工具，如果没有使用过git可以阅读：[git官网](https://git-scm.com/)，[git教程](https://www.runoob.com/git/git-tutorial.html)

::: warning

以下命令均在*命令提示符（Command Prompt）*中使用，不要使用 git bash！！

:::

确保 python 版本至少为 3.6

下载源码 `git clone https://github.com/pcrbot/yobot.git`

或者使用国内源 `git clone https://gitee.com/yobot/yobot.git`

请尽量使用 git clone 而不是 download zip，否则无法自动更新版本

进入目录 `cd yobot\src\client`

安装依赖 `pip install -r requirements.txt`
（如果在国内建议加上参数 `-i https://pypi.tuna.tsinghua.edu.cn/simple`）

启动：`python main.py`

如果需要更换主机地址、端口等信息请修改 `yobot_data\yobot_config.json` 配置文件。

![windows下正确启动图](https://img.yobot.win/yobot/aaf38d1a5cbc1c87.jpg)

![windows下正确yobot与httpapi成功通信](https://img.yobot.win/yobot/8179fdd1e46690b2.jpg)

### 验证安装

向机器人发送“version”，机器人会回复当前版本

## 常见问题

见 [FAQ](../usage/faq.md)

## 开始 web 模式

[开启方法](../usage/web-mode.md)
