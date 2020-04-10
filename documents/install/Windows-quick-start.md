# Windows 运行包（快速上手版）

## 参考视频

在 windows 下使用运行包安装可以参考[演示视频](https://x.jingzhidh.com/3/Tutorial.mp4)  
（视频中网站为旧版，不影响安装过程）

## 准备服务器

虽然在自己电脑运行也可以，不过最好能租一个服务器，以便长期挂机和提供web服务

[服务器推荐](./server.md)

## 安装

### 第一步

点击下载[酷Q-httpapi 整合包](https://x.jingzhidh.com/CoolQ_With_Httpapi.7z)

解压后双击“CQA.exe”，输入账号密码（注意账号风险，请勿使用重要的QQ号）

右键点击悬浮窗，应用→应用管理→启用HTTP API插件（如果无法启动请参考下方的[常见问题](#http-api-%E6%97%A0%E6%B3%95%E5%90%AF%E5%8A%A8)）

启动 httpapi 插件后会反复出现如下的提示

![httpapi启用图片](https://x.jingzhidh.com/img/yobot/8ba6b840bab3ac25.jpg)

### 第二步

点击下载[yobot运行包](https://yuudi.github.io/yobot/v3/download-latest.html)

解压后双击“yobot.exe”启动服务，双方通信成功后出现如下的提示

![windows下正确yobot与httpapi成功通信](https://x.jingzhidh.com/img/yobot/8179fdd1e46690b2.jpg)

### 验证安装

向机器人发送“version”，机器人会回复当前版本

## 使用

向机器人发送“帮助”，按照帮助使用功能即可

## 常见问题

### Http Api 无法启动

参考：[httpapi插件文档](https://cqhttp.cc/docs/)

如果你的windows不是最新版，可能无法启动httpapi插件，请安装Visual C++ 可再发行软件包（[点击下载](https://aka.ms/vs/16/release/vc_redist.x86.exe)）。如果你的系统是 Windows 7 或 Windows Server 2008、或者安装 Visual C++ 可再发行软件包之后仍然加载失败，则还需要安装通用 C 运行库更新（[点击进入官网](https://support.microsoft.com/zh-cn/help/3118401/update-for-universal-c-runtime-in-windows)，选择你系统对应的版本下载安装）

### 酷Q的日志显示了发送，实际却没有发送

这种情况一般是消息被腾讯屏蔽，常常发生在异地登陆时

解决方法：

* 关闭所有插件，机器人挂机一段时间
* 在远程主机上使用一下QQ网页服务（比如QQ邮箱、QQ安全中心等）
* 下载QQ安全中心，确认异地登录

## 开始 web 模式

[开启方法](../usage/web-mode.md)
