# Linux 使用 cqhttp-mirai 部署（测试）

## 部署过程

安装环境

```shell
# RHEL / CentOS:
yum install -y java python3 screen wget git

# Debain / Ubuntu
# apt-get install -y java python3 screen wget git
```

（可选）新建一个 linux 用户

```shell
groupadd qqbot
useradd -g qqbot -m qqbot
su qqbot
```

新建一个 screen

```shell
screen -S qqbot
```

下载并启动 yobot

```shell
mkdir -p ~/qqbot/yobot
cd ~/qqbot/yobot

# 下载源码
git clone https://github.com/yuudi/yobot.git
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

启动 mirai-console

```shell
mkdir -p ~/qqbot/mirai
cd ~/qqbot/mirai

# 你可以在这里找到最新版本：https://github.com/mamoe/mirai-console-wrapper/releases
wget https://github.com/mamoe/mirai-console-wrapper/releases/download/1.3.0/mirai-console-wrapper-1.3.0-all.jar
java -jar mirai-console-wrapper-1.3.0-all.jar
```

在 mirai-console 里登录 QQ 并下载 CQHTTPMirai 插件

```shell
# （mirai-console内）
# 登录 QQ
login 123456789 ppaasswwdd # 注意改成你的QQ小号的账号密码

# 安装 cqhttp-mirai
install CQHTTPMirai
```

按下 `ctrl-a , c` 连续组合键，新建一个 screen shell

修改 CQHTTPMirai 配置文件

```shell
mkdir -p ~/qqbot/mirai/plugins/CQHTTPMirai
cd ~/qqbot/mirai/plugins/CQHTTPMirai
vi setting.yml
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

保存后按下 `ctrl-a , 1` 连续组合键，回到 1 号 shell （即 mirai-console 所在的 shell）

按下 `ctrl-c` 退出 mirai 然后重新启动 mirai 并登录 QQ

<!--
重新加载插件

```shell
# （mirai-console内）
reload
```
-->

部署完成，现在可以按下 `ctrl-a , d` 连续组合键挂起这两个 shell

## 验证安装

向机器人发送“version”，机器人会回复当前版本

## 常见问题

见[FAQ](../usage/faq.md)

## 开启 web 访问

[开启方法](../usage/web-mode.md)
