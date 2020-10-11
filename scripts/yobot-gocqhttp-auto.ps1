# this file should be saved as "UTF-8 with BOM"
$ErrorActionPreference = "Stop"

# 检查运行环境
if ($Host.Version.Major -lt 5) {
    Write-Output 'powershell 版本过低，无法一键安装'
    exit
}
if ((Get-ChildItem -Path Env:OS).Value -ine 'Windows_NT') {
    Write-Output '当前操作系统不支持一键安装'
    exit
}
if (![Environment]::Is64BitProcess) {
    Write-Output '暂时不支持32位系统'
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
Write-Output '是否使用YoCool皮肤（测试版）：'
$yocool = Read-Host '请输入 y 或 n (y/n)'
Switch ($yocool) {
    Y { $yocool = $true }
    N { $yocool = $false }
    Default { $yocool = $false }
}
Write-Output '是否监听80端口（如果此服务器没有其他网站，建议选 y）：'
$listen_80 = Read-Host '请输入 y 或 n (y/n)'
Switch ($listen_80) {
    Y { $port = 80 }
    N { $port = 9222 }
    Default { $port = 9222 }
}

# 创建运行目录
New-Item -Path .\qqbot -ItemType Directory
Set-Location qqbot
New-Item -ItemType Directory -Path .\yobot, .\yobot\yobot_data, .\mirai, .\mirai\plugins, .\mirai\plugins\CQHTTPMirai

# 下载程序
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest https://down.yobot.club/tools/wget.exe -OutFile .\wget.exe
.\wget.exe https://download.fastgit.org/Mrs4s/go-cqhttp/releases/download/v0.9.25-fix3/go-cqhttp-v0.9.25-fix3-windows-amd64.zip -O .\go-cqhttp.zip
Expand-Archive go-cqhttp.zip -DestinationPath .\mirai\
Remove-Item go-cqhttp.zip
if ($yocool) {
    .\wget.exe https://down.yobot.club/yobot/yocool.zip -O .\yobot.zip
}
else {
    .\wget.exe https://down.yobot.club/yobot/yobot.zip -O .\yobot.zip
}
Expand-Archive yobot.zip -DestinationPath .\yobot\
if ($yocool) { Move-Item .\yobot\yobot--with-yocool.exe  .\yobot\yobot.exe }
Remove-Item yobot.zip

# 生成随机 access_token
$token = -join ((65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object { [char]$_ })

# 写入 go-cqhttp 配置文件
$realpassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($qqpassword))
New-Item -Path .\mirai\config.json -ItemType File -Value @"
{
  "uin": ${qqid},
  "password": "${realpassword}",
  "encrypt_password": false,
  "password_encrypted": `"`",
  "enable_db": false,
  "access_token": "${token}",
  "relogin": {
    "enabled": true,
    "relogin_delay": 3,
    "max_relogin_times": 0
  },
  "_rate_limit": {
    "enabled": false,
    "frequency": 1,
    "bucket_size": 1
  },
  "post_message_format": "string",
  "ignore_invalid_cqcode": false,
  "force_fragmented": true,
  "heartbeat_interval": 5,
  "http_config": {
    "enabled": false
  },
  "ws_config": {
    "enabled": false
  },
  "ws_reverse_servers": [
    {
      "enabled": true,
      "reverse_url": "ws://localhost:${port}/ws/",
      "reverse_reconnect_interval": 3000
    }
  ]
}
"@

# 写入 yobot 配置文件
New-Item -Path .\yobot\yobot_data\yobot_config.json -ItemType File -Value @"
{
    "port": "${port}",
    "public_basepath": "/",
    "access_token": "${token}"
}
"@

# 启动程序
Start-Process -FilePath .\yobot\yobot.exe -WorkingDirectory .\yobot
Start-Process -FilePath cmd.exe -WorkingDirectory .\mirai -ArgumentList "/C `"go-cqhttp & pause`""

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
