#!/bin/bash
set -e

# ensure amd64
if [ $(dpkg --print-architecture) != "amd64" ]; then
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

After script finished, you need to press 'ctrl-p, ctrl-q' to detach the container.

"

read -p "请输入作为机器人的QQ号：" qqid
read -p "请输入作为机器人的QQ密码：" qqpassword
export qqid
export qqpassword

echo "开始安装，请等待"

mkdir yobot_data gocqhttp_data

if [ -x "$(command -v docker)" ]; then
    echo "docker found, skip installation"
else
    echo "installing docker"
    curl -fsSL "https://get.docker.com" | sh
fi

docker network create qqbot
docker pull alpine
docker pull yobot/yobot

echo "downloading latest gocqhttp"
docker run --rm -v ${PWD}:/work -w /work python:3.7-slim-buster python3 -c "
import json
import urllib.request
url = 'https://api.github.com/repos/Mrs4s/go-cqhttp/releases'
resp = urllib.request.urlopen(url).read().decode('utf-8')
assets = json.loads(resp)[0]['assets']
for item in assets:
    if item['name'].endswith('linux-amd64.tar.gz'):
        download = item['browser_download_url']
        break
resp = urllib.request.urlopen(download).read()
f = open('go-cqhttp.tar.gz', 'wb')
f.write(resp)
f.close()
"
tar zxf go-cqhttp.tar.gz
rm go-cqhttp.tar.gz -f

echo "building gocqhttp container"
echo "
FROM alpine:latest
ADD go-cqhttp /bin/go-cqhttp
WORKDIR /bot
ENTRYPOINT /bin/go-cqhttp
">Dockerfile
docker build . -t gocqhttp
rm Dockerfile -f

echo "initializing gocqhttp configure file"
docker run --rm \
           -v ${PWD}/gocqhttp_data:/bot \
           gocqhttp >/dev/null 2>&1

echo "writing configure files"
docker run --rm -v ${PWD}:/work -w /work -e qqid -e qqpassword python:3.7-slim-buster python3 -c "
import json, os, random, string
access_token = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=16))
with open('yobot_data/yobot_config.json', 'w') as f:
    json.dump({'access_token': access_token}, f, indent=4)
with open('gocqhttp_data/config.json', 'r+') as f:
    config = json.load(f)
    config['uin'] = int(os.environ['qqid'])
    config['password'] = os.environ['qqpassword']
    config['access_token'] = access_token
    config['enable_db'] = False
    config['web_ui']['enabled'] = False
    config['http_config']['enabled'] = False
    config['ws_config']['enabled'] = False
    config['ws_reverse_servers'] = [{
        'enabled': True,
        'reverse_url': 'ws://yobot:9222/ws/',
        'reverse_api_url': '',
        'reverse_event_url': '',
        'reverse_reconnect_interval': 3000
    }]
    f.seek(0)
    f.truncate()
    json.dump(config, f, indent=4)
"

echo "starting yobot"
docker run -d \
           --name yobot \
           -p 9222:9222 \
           --network qqbot \
           -v ${PWD}/yobot_data:/yobot/yobot_data \
           yobot/yobot

echo "starting gocqhttp"
docker run -it \
           --name gocqhttp \
           --network qqbot \
           -v ${PWD}/gocqhttp_data:/bot \
           gocqhttp
