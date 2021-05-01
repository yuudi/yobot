# this file should be saved as "UTF-8 with BOM"
$ErrorActionPreference = "Stop"

function Expand-ZIPFile($file, $destination) {
  $file = (Resolve-Path -Path $file).Path
  $destination = (Resolve-Path -Path $destination).Path
  $shell = new-object -com shell.application
  $zip = $shell.NameSpace($file)
  foreach ($item in $zip.items()) {
    $shell.Namespace($destination).copyhere($item)
  }
}

# 检查运行环境
if ($Host.Version.Major -lt 3) {
  Write-Output 'powershell 版本过低，无法一键安装'
  exit
}
if ((Get-ChildItem -Path Env:OS).Value -ine 'Windows_NT') {
  Write-Output '当前操作系统不支持一键安装'
  exit
}
if (![Environment]::Is64BitProcess) {
  Write-Output '对不起，此脚本只支持64位系统'
  exit
}
if (Test-Path .\qqbot) {
  Write-Output '发现重复，是否删除旧文件并重新安装？'
  $reinstall = Read-Host '请输入 y 或 n (y/n)'
  Switch ($reinstall) {
    Y { Remove-Item .\qqbot -Recurse -Force }
    N { exit }
    Default { exit }
  }
}

# 用户输入
$qqid = Read-Host '请输入作为机器人的QQ号：'
$qqpassword = Read-Host -AsSecureString '请输入作为机器人的QQ密码：'

$port = Read-Host '请输入端口（范围8000到49151，直接回车则随机）：'
if (!$port) {
  $port = Get-Random -Minimum 8000 -Maximum 49151
}

Write-Output '是否部署 caddy 网络服务器（如果你打算部署其他网络服务器如 nginx 等，建议选否）：'
$userinput = Read-Host '请输入 y 或 n (y/n)'
Switch ($userinput) {
  Y { $use_caddy = $true }
  N { $use_caddy = $false }
  Default { $use_caddy = $false }
}

Write-Output '是否使用域名？'
Write-Output '（如果服务器在国内，则必须是备案域名）'
Write-Output '（请提前将域名指向此服务器）'
$domain = Read-Host '请输入域名（不使用则直接回车）：'

# 创建运行目录
New-Item -Path .\qqbot -ItemType Directory
Set-Location qqbot
New-Item -ItemType Directory -Path .\yobot, .\yobot\yobot_data, .\mirai

# 下载程序
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest https://download.fastgit.org/Mrs4s/go-cqhttp/releases/download/v1.0.0-beta3/go-cqhttp_windows_amd64.zip -OutFile .\go-cqhttp-v1.0.0-beta3-windows-amd64.zip
Expand-ZIPFile go-cqhttp-v1.0.0-beta3-windows-amd64.zip -Destination .\mirai\
Remove-Item go-cqhttp-v1.0.0-beta3-windows-amd64.zip

# New-Item -Path ".\mirai\升级gocqhttp.bat" -ItemType File -Value @"
# @echo off
# :PROMPT
# SET /P AREYOUSURE=comfirm update? (y/[n])?
# IF /I "%AREYOUSURE%" NEQ "y" GOTO END

# echo -y | go-cqhttp.exe update


# :END
# pause
# "@

Invoke-WebRequest https://download.fastgit.org/pcrbot/yobot/releases/download/v3.6.11/yobot-v3.6.11-windows64.zip -OutFile .\yobot.zip

Expand-ZIPFile yobot.zip -Destination .\yobot\
Remove-Item yobot.zip

if ($use_caddy) {  
  Invoke-WebRequest https://download.fastgit.org/caddyserver/caddy/releases/download/v2.3.0/caddy_2.3.0_windows_amd64.zip -OutFile .\caddy_2.3.0_windows_amd64.zip
  New-Item -ItemType Directory -Path caddy
  Expand-ZIPFile caddy_2.3.0_windows_amd64.zip -Destination .\caddy\
  Remove-Item caddy_2.3.0_windows_amd64.zip
  $listen = '127.0.0.1'
}
else {
  $listen = '0.0.0.0'
}

if ($domain) {
  if ($use_caddy) {
    $public_address = "https://${domain}"
  }
  else {
    $public_address = "http://${domain}:${port}"
  }
}
else {
  $ip = (Invoke-WebRequest api.ipify.org).content
  if ($use_caddy) {
    $public_address = "http://${ip}"
  }
  else {
    $public_address = "http://${ip}:${port}"
  }
}

# 生成随机 access_token
$token = -join ((65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object { [char]$_ })

# 写入 go-cqhttp 配置文件
$realpassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($qqpassword))
New-Item -Path .\mirai\config.yml -ItemType File -Value @"
account: # 账号相关
  uin: ${qqid} # QQ账号
  password: '${realpassword}' # 密码为空时使用扫码登录
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
  access-token: '${token}'
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
      universal: ws://127.0.0.1:${port}/ws/
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
"@

# 写入 yobot 配置文件
New-Item -Path .\yobot\yobot_data\yobot_config.json -ItemType File -Value @"
{
    "host": "${listen}",
    "port": "${port}",
    "public_address": "${public_address}",
    "public_basepath": "/",
    "access_token": "${token}"
}
"@

if ($use_caddy) {
  # 写入 caddy 配置文件
  if (!$domain) {
    $domain = ':80'
  }
  New-Item -Path .\caddy\Caddyfile -ItemType File -Value @"
${domain}
respond /ws/* "Forbidden" 403 {
  close
}
reverse_proxy / http://127.0.0.1:${port} {
  header_up X-Real-IP {remote_host}
}
"@
}

# 启动程序
Start-Process -FilePath .\yobot\yobot.exe -WorkingDirectory .\yobot
Start-Process -FilePath cmd.exe -WorkingDirectory .\mirai -ArgumentList "/C `"go-cqhttp & pause`""
if ($use_caddy) {
  Start-Process -FilePath cmd.exe -WorkingDirectory .\caddy -ArgumentList "/C `"caddy run & pause`""
}

# 创建快捷方式
$desktop = [Environment]::GetFolderPath("Desktop")

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("${desktop}\mirai-go.lnk")
$Shortcut.TargetPath = "${pwd}\mirai\go-cqhttp.exe"
$Shortcut.WorkingDirectory = "${pwd}\mirai\"
$Shortcut.Save()

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("${desktop}\yobot.lnk")
$Shortcut.TargetPath = "${pwd}\yobot\yobot.exe"
$Shortcut.WorkingDirectory = "${pwd}\yobot\"
$Shortcut.Save()
