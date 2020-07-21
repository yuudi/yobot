---
editLink: false
---

# yobot 公主连接群聊机器人

## 介绍

[yobot](./about.md) 是为[公主连接](https://game.bilibili.com/pcr/)公会战设计的辅助机器人，能够帮助公会战管理者提供自动化管理服务。

yobot 提供了群聊、web 页面两套用户交互方式，具有操作便捷、通知及时、数据详细的特点。

## 获取

自建方法请参考[安装教程](./install/README.md)

或者加入交流群 {{ [770947581,1044314369,1067699252,774394459][Math.floor(Math.random()*4)] }}，租用或出租机器人

## 功能介绍

### 公会战伤害统计助手

公会战成员可以把每一次伤害报告给机器人，
以生成统计数据

只要机器人记录下 boss 的状态和每一次出刀伤害，就可以：

- 统计每一天的出刀情况，生成报表
- 预约 boss，当对应 boss 出现时提醒预约的人
- 挂树，当前 boss 被击败时提醒挂树的人
- 申请出刀，提醒之后申请出刀的人有人正在出刀，防止意外撞刀
- SL 记录，记录每天的 SL 使用情况，方便指挥

新版助手提供了一个网页面板，面板上可以进行更多操作

![主面板](https://img.yobot.win/yobot/poYvQO.jpg)

![数据面板](https://img.yobot.win/yobot/HOh17P.jpg)

### 新闻推送

机器人主动发送游戏新闻与活动提醒

![游戏活动提醒](https://img.yobot.win/yobot/5bd8d1f5ac68ffde.jpg)

![数据面板](https://img.yobot.win/yobot/HOh17P.jpg)

### 日程查询

机器人主动发送游戏新闻与活动提醒

![游戏活动提醒](https://img.yobot.win/yobot/J04GEB.jpg)

### 模拟抽卡

模拟十连抽，
而且可以记录每个人的仓库并在线查看，
还可以自定义修改卡池
（怕打扰可以关闭此功能）

![模拟抽卡](https://img.yobot.win/yobot/u4OLHH.png)

### 更多功能

更多功能请参照[指令表](./features/README.md)。

## 源码

<https://github.com/pcrbot/yobot>

## 贡献者

[项目贡献者](./project/contributors.md)

## 开源协议

本工具使用了[这些](./project/open-source.md)开源软件和工具

使用时请遵循[GPL-3.0 协议](https://www.gnu.org/licenses/gpl-3.0.html)，简单地说：

- 自己使用、不重新分发，没有限制
- 对本工具免费或收费提供下载或其它服务，需要在明显地方**说明本工具可以免费获取**并注明出处
- 修改源代码并发布修改后的代码或提供其它服务，需要开放源码、改变名称、提供出处、说明变动、保持协议不变
