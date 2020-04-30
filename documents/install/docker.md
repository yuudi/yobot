# 使用Docker启动yobot
使用Docker的方式应该是最省心的方式。  
建议购买一台阿里云Ubuntu 18.04(linux) 云服务器来运行。  
最低配置1核2GB。  

## 克隆项目
登录云服务器，如果您还有安装git，请先输入如下指令安装git
```shell script
sudo apt update
sudo apt install -y git
```
之后运行
```shell script
git clone https://github.com/yuudi/yobot.git
```

## 安装docker和docker-compose
如果您没有安装过docker和docker-compose（也就是新开的实例），建议运行我们的一键脚本。  
该脚本将自动为您安装docker和docker-compose并更换国内加速镜像。  
```shell script
cd yobot
sudo bash scripts/install-docker.sh
```

## 拷贝、修改项目配置
```shell script
cp .env.example .env
nano .env
```
将`VNC_PWD=Yobot123`中的`Yobot123`改为你自己的密码，用于登录酷Q后台。  
之后将您要登录的QQ号填在`QQ_ACCOUNT=`后面。  
编辑完成后按Ctrl+O，之后按回车保存。保存后按Ctrl+X退出  

## 构建项目容器，开启项目
运行
```shell script
sudo docker-compose up
```
即可启动项目。第一次启动时间较长。  
如需关闭项目请使用  
```shell script
sudo docker-compose down
```
如需重启项目请使用  
```shell script
sudo docker-compose restart
```

## 登录QQ
之后请您访问`http://您的服务器外网ip:9000`，输入您在刚刚`VNC_PWD`设置的密码即可登录。  
您服务器的外网IP您可以在阿里云控制台看到。  
如果您不能访问这个链接，请检查服务器是否成功启动、安全组设置是否放通全部端口。  
之后请登录您的QQ，如遇"下载Chrome"字样提示，请取消从重新登录。

登录后向您的bot用QQ发送`V`，如果您收到版本号回复，即为部署成功、
如果需要开启web，请看[这里](../usage/web-mode.md)


