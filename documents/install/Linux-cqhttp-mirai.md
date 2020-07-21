# Linux 使用 cqhttp-mirai 部署

::: tip

阅读此章节前，您需要了解：

- Linux 基本用法
- screen（或tmux）
- git

:::

## 部署过程

### 环境准备

#### 安装依赖

```shell
# RHEL / CentOS:
yum install -y python3 screen wget git

# Debain / Ubuntu
# apt-get install -y python3 screen wget git
```

#### （可选）新建一个 linux 用户

> 使用低权限的用户可以减少意外时的损失

```shell
groupadd qqbot
useradd -g qqbot -m qqbot
su - qqbot
```

#### 使用终端复用器

这里我们用 screen 作为终端复用工具，具体用法请搜索 screen 教程  
现在新建一个 screen 终端

```shell
screen -S qqbot
```

### 部署 yobot

```shell
mkdir -p ~/qqbot/yobot
cd ~/qqbot/yobot

# 下载源码
git clone https://github.com/pcrbot/yobot.git
# 国内可改用 https://gitee.com/yobot/yobot.git

cd yobot/src/client/

# 安装依赖
pip3 install -r requirements.txt --user
# 国内可加上参数 -i https://pypi.tuna.tsinghua.edu.cn/simple

# 生成 yobotg
python3 main.py

# 启用 yobot
sh yobotg.sh
```

按下 `ctrl-a , c` 连续组合键，新建一个 screen shell

### 部署 mirai

#### 下载 miraiOK

下面这个是 amd64 的可执行文件（大部分服务器都是这个），如果你的计算机不是 amd64 架构，请在[这里](https://github.com/LXY1226/MiraiOK/#下载地址)找到其他的可执行文件

```shell
mkdir -p ~/qqbot/mirai/plugins/CQHTTPMirai
cd ~/qqbot/mirai
wget http://t.imlxy.net:64724/mirai/MiraiOK/miraiOK_linux_amd64 -O miraiOK
```

#### 下载 cqhttp-mirai

你也可以在[这里](https://github.com/yyuueexxiinngg/cqhttp-mirai/releases)找到最新版本

```shell
cd ~/qqbot/mirai/plugins

wget https://github.com/yyuueexxiinngg/cqhttp-mirai/releases/download/0.1.4/cqhttp-mirai-0.1.4-all.jar
# 国内可改用 https://github-proxy.yobot.win/yyuueexxiinngg/cqhttp-mirai/releases/download/0.1.4/cqhttp-mirai-0.1.4-all.jar
```

#### 修改 CQHTTPMirai 配置文件

```shell
cd ~/qqbot/mirai/plugins/CQHTTPMirai
vim setting.yml
# 如果你不熟悉 vim，建议使用 nano
# yum install nano -y 或 apt-get install nano -y
# nano setting.yml
```

修改配置文件如下（注意修改 QQ 号）

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

#### 启动 miraiOK 并登录 QQ

```shell
cd ~/qqbot/mirai
chmod +x miraiOK
./miraiOK

# （mirai-console内）
login 123456789 ppaasswwdd # 注意改成你的QQ小号的账号密码
```

部署完成，现在可以按下 `ctrl-a , d` 连续组合键挂起这两个 shell

#### （可选）为 miraiOK 设置自动登录

编辑 `~/qqbot/mirai/config.txt`，内容如下

```plain
----------
login 123456789 ppaasswwdd

```

注意：

- 第一行的 `----------` 不可省略
- 最后一个换行不可省略
- 换行必须使用 `\n`，不能用 `\r\n`（不要在 Windows 下编辑再上传）

## 验证安装

向机器人发送“version”，机器人会回复当前版本

## 常见问题

见[FAQ](../usage/faq.md)

## 开启 web 访问

[开启方法](../usage/web-mode.md)
