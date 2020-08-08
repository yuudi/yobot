# this file should be saved as "UTF-8 with BOM"
$ErrorActionPreference = "Inquire"

# 检查运行环境
if ($Host.Version.Major -lt 5) {
    Write-Output 'powershell 版本过低，无法一键安装'
    exit
}
if ((Get-ChildItem -Path Env:OS).Value -ine 'Windows_NT') {
    Write-Output '当前操作系统不支持一键安装'
    exit
}
if ([Environment]::Is64BitProcess) {
}
else {
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
$qqpassword = Read-Host '请输入作为机器人的QQ密码：'
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
Invoke-WebRequest https://get.yobot.win/scyb/miraiOK_win_amd64.exe -OutFile .\mirai\miraiOK.exe
if ((Get-FileHash -Path .\mirai\miraiOK.exe -Algorithm SHA256).Hash -ne "60B4B16AC401ADD7D75FADA83344B50EBA9F0976F73113FF6D95E5C09E79941F") { Write-Output '下载失败'; exit }
Invoke-WebRequest https://get.yobot.win/scyb/cqhttp-mirai-0.1.9-all.jar -OutFile .\mirai\plugins\cqhttp-mirai-0.1.9-all.jar
if ((Get-FileHash -Path .\mirai\plugins\cqhttp-mirai-0.1.9-all.jar -Algorithm SHA256).Hash -ne "6A93DB2B422D93B1632A92C8E0AC25FE51050A5474B36B252BB2E1A8D22B5B0D") { Write-Output '下载失败'; exit }
Invoke-WebRequest https://get.yobot.win/scyb/yobot208.zip -OutFile .\yobot.zip
if ((Get-FileHash -Path .\yobot.zip -Algorithm SHA256).Hash -ne "5D5FE0CBEEA746D4C50303794C4E01C0A7EAA54D805873CA3269BBEF35BEA643") { Write-Output '下载失败'; exit }
Expand-Archive yobot.zip -DestinationPath .\yobot\
Remove-Item yobot.zip

# 生成随机 access_token
$token = -join ((65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object { [char]$_ })

# 写入 cqmiraihttp 配置文件
New-Item -Path .\mirai\plugins\CQHTTPMirai\setting.yml -ItemType File -Value @"
"${qqid}":
  ws_reverse:
    - enable: true
      postMessageFormat: string
      reverseHost: 127.0.0.1
      reversePort: ${port}
      reversePath: /ws/
      accessToken: ${token}
      reconnectInterval: 3000
"@

# 写入 miraiOK 配置文件
New-Item -Path .\mirai\config.txt -ItemType File -Value "----------`nlogin ${qqid} ${qqpassword}`n"

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
Start-Process -FilePath .\mirai\miraiOK.exe -WorkingDirectory .\mirai

# 创建快捷方式
$desktop = [Environment]::GetFolderPath("Desktop")

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("${desktop}\mirai.lnk")
$Shortcut.TargetPath = "${pwd}\mirai\miraiOK.exe"
$Shortcut.WorkingDirectory = "${pwd}\mirai\"
$Shortcut.Save()

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("${desktop}\yobot.lnk")
$Shortcut.TargetPath = "${pwd}\yobot\yobot.exe"
$Shortcut.WorkingDirectory = "${pwd}\yobot\"
$Shortcut.Save()
