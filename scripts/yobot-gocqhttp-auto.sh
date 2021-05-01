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
docker pull pcrbot/gocqhttp:1.0.0-beta3
docker pull yobot/yobot:slim

access_token="$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)"

echo "
account: # 账号相关
  uin: ${qqid} # QQ账号
  password: '${qqpassword}' # 密码为空时使用扫码登录
  encrypt: false  # 是否开启密码加密
  status: 0      # 在线状态 请参考 https://github.com/Mrs4s/go-cqhttp/blob/dev/docs/config.md#在线状态
  relogin: # 重连设置
    disabled: false
    delay: 3      # 重连延迟, 单位秒
    interval: 0   # 重连间隔
    max-times: 0  # 最大重连次数, 0为无限制

  # 是否使用服务器下发的新地址进行重连
  # 注意, 此设置可能导致在海外服务器上连接情况更差
  use-sso-address: true

heartbeat:
  disabled: false # 是否开启心跳事件上报
  # 心跳频率, 单位秒
  # -1 为关闭心跳
  interval: 5

message:
  # 上报数据类型
  # 可选: string,array
  post-format: string
  # 是否忽略无效的CQ码, 如果为假将原样发送
  ignore-invalid-cqcode: true
  # 是否强制分片发送消息
  # 分片发送将会带来更快的速度
  # 但是兼容性会有些问题
  force-fragment: false
  # 是否将url分片发送
  fix-url: false
  # 下载图片等请求网络代理
  proxy-rewrite: ''
  # 是否上报自身消息
  report-self-message: false
  # 移除服务端的Reply附带的At
  remove-reply-at: false
  # 为Reply附加更多信息
  extra-reply-data: false

output:
  # 日志等级 trace,debug,info,warn,error
  log-level: warn
  # 是否启用 DEBUG
  debug: false # 开启调试模式

# 默认中间件锚点
default-middlewares: &default
  # 访问密钥, 强烈推荐在公网的服务器设置
  access-token: '${access_token}'
  # 事件过滤器文件目录
  filter: ''
  # API限速设置
  # 该设置为全局生效
  # 原 cqhttp 虽然启用了 rate_limit 后缀, 但是基本没插件适配
  # 目前该限速设置为令牌桶算法, 请参考:
  # https://baike.baidu.com/item/%E4%BB%A4%E7%89%8C%E6%A1%B6%E7%AE%97%E6%B3%95/6597000?fr=aladdin
  rate-limit:
    enabled: false # 是否启用限速
    frequency: 1  # 令牌回复频率, 单位秒
    bucket: 1     # 令牌桶大小

servers:
  # HTTP 通信设置
  - http:
      # 是否关闭正向HTTP服务器
      disabled: false
      # 服务端监听地址
      host: 127.0.0.1
      # 服务端监听端口
      port: 5700
      # 反向HTTP超时时间, 单位秒
      # 最小值为5，小于5将会忽略本项设置
      timeout: 5
      middlewares:
        <<: *default # 引用默认中间件
      # 反向HTTP POST地址列表
      post:
      #- url: '' # 地址
      #  secret: ''           # 密钥
      #- url: 127.0.0.1:5701 # 地址
      #  secret: ''          # 密钥

  # 正向WS设置
  - ws:
      # 是否禁用正向WS服务器
      disabled: true
      # 正向WS服务器监听地址
      host: 127.0.0.1
      # 正向WS服务器监听端口
      port: 6700
      middlewares:
        <<: *default # 引用默认中间件

  - ws-reverse:
      # 是否禁用当前反向WS服务
      disabled: false
      # 反向WS Universal 地址
      # 注意 设置了此项地址后下面两项将会被忽略
      universal: ws://yobot:9222/ws/
      # 反向WS API 地址
      api: ''
      # 反向WS Event 地址
      event: ''
      # 重连间隔 单位毫秒
      reconnect-interval: 3000
      middlewares:
        <<: *default # 引用默认中间件
  # pprof 性能分析服务器, 一般情况下不需要启用.
  # 如果遇到性能问题请上传报告给开发者处理
  # 注意: pprof服务不支持中间件、不支持鉴权. 请不要开放到公网
  - pprof:
      # 是否禁用pprof性能分析服务器
      disabled: true
      # pprof服务器监听地址
      host: 127.0.0.1
      # pprof服务器监听端口
      port: 7700

  # 可添加更多
  #- ws-reverse:
  #- ws:
  #- http:
  #- pprof:

database: # 数据库相关设置
  leveldb:
    # 是否启用内置leveldb数据库
    # 启用将会增加10-20MB的内存占用和一定的磁盘空间
    # 关闭将无法使用 撤回 回复 get_msg 等上下文相关功能
    enable: false
">gocqhttp_data/config.yml

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
           pcrbot/gocqhttp:1.0.0-beta3
