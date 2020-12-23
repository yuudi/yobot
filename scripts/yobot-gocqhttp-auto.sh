#!/bin/bash
set -e

# ensure amd64
if [ $(uname -m) != "x86_64" ]; then
    echo "Sorry, the architecture of your device is not supported yet."
    exit
fi

# ensure run as root
if [ $EUID -ne 0 ]; then
    echo "Please run as root"
    exit
fi

echo "
yobot-gocqhttp installer script

What will it do:
1. install docker
2. run yobot in docker
3. run go-cqhttp in docker

After script finished, you need to press 'ctrl-P, ctrl-Q' to detach the container.
此脚本执行结束并登录后，你需要按下【ctrl-P，ctrl-Q】连续组合键以挂起容器

"

read -p "请输入作为机器人的QQ号：" qqid
read -p "请输入作为机器人的QQ密码：" qqpassword

echo "开始安装，请等待"

mkdir yobot_data gocqhttp_data

if [ -x "$(command -v docker)" ]; then
    echo "docker found, skip installation"
else
    echo "installing docker"
    curl -fsSL "https://get.docker.com" | sh
fi

docker network create qqbot || true
docker pull pcrbot/gocqhttp:0.9.29-fix2
docker pull yobot/yobot:slim

access_token="$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)"

echo "
{
  \"uin\": ${qqid},
  \"password\": \"${qqpassword}\",
  \"encrypt_password\": false,
  \"password_encrypted\": \"\",
  \"enable_db\": false,
  \"access_token\": \"${access_token}\",
  \"relogin\": {
    \"enabled\": true,
    \"relogin_delay\": 3,
    \"max_relogin_times\": 0
  },
  \"_rate_limit\": {
    \"enabled\": false,
    \"frequency\": 1,
    \"bucket_size\": 1
  },
  \"post_message_format\": \"string\",
  \"ignore_invalid_cqcode\": false,
  \"force_fragmented\": true,
  \"heartbeat_interval\": 5,
  \"use_sso_address\": false,
  \"http_config\": {
    \"enabled\": false
  },
  \"ws_config\": {
    \"enabled\": false
  },
  \"ws_reverse_servers\": [
    {
      \"enabled\": true,
      \"reverse_url\": \"ws://yobot:9222/ws/\",
      \"reverse_reconnect_interval\": 3000
    }
  ],
  \"web_ui\": {
    \"enabled\": false
  }
}
">gocqhttp_data/config.json

echo "starting yobot"
docker run -d \
           --name yobot \
           -p 9222:9222 \
           --network qqbot \
           -v ${PWD}/yobot_data:/yobot/yobot_data \
           -e YOBOT_ACCESS_TOKEN="$access_token" \
           yobot/yobot:slim

echo "starting gocqhttp"
docker run -it \
           --name gocqhttp \
           --network qqbot \
           -v ${PWD}/gocqhttp_data:/data \
           pcrbot/gocqhttp:0.9.29-fix2
