# 使用Docker启动yobot

::: tip

阅读此章节前，您需要了解：

- Linux 基本用法
- docker
- git

:::

使用Docker的方式应该是最省心的方式。  
建议购买一台阿里云Ubuntu 18.04(linux) 云服务器来运行。  
最低配置1核2GB。  

::: warning

本文只适用于在**Linux**下部署的情况。  
**Windows系统下部署**，建议参考[Windows源码部署](./Windows-source.md)。  
不推荐在Windows系统下部署的原因，请参阅[文档末尾](#Windows部署Docker可能出现的问题)

:::

## 克隆项目
登录云服务器，如果您还没有安装git，请先输入如下指令安装git
```shell script
sudo apt update
sudo apt install -y git
```
之后运行
```shell script
git clone https://github.com/pcrbot/yobot.git
```
或者使用国内镜像源 https://gitee.com/yobot/yobot.git

## 安装docker和docker-compose
如果您没有安装过docker和docker-compose（也就是新开的实例），建议运行我们的一键脚本。  
该脚本将自动为您安装docker和docker-compose并更换国内加速镜像。  
```shell script
cd yobot
sudo bash scripts/install-docker.sh
```

## 为docker创建管理用户（可选）
### root用户太长不看版
如果您执意**使用root用户**运行docker：  
请在yobot源码的根目录下执行  
```shell script
chown -R 1000:1000 .
```
以防止权限错误。  
之后，您可以看**下一个大标题**了。  

### 创建低权限管理用户
为了避免可能存在的提权漏洞，危害到您的服务器安全和数据安全，非常不建议您直接使用root账户运行docker实例。  
yobot目前的docker实例限制在UID=1000的用户下运行。  
如果您直接使用root运行docker-compose的话，极有可能会产生权限错误。  
如果您对linux系统比较陌生，**非常推荐**您按照以下的步骤进行操作。  
以下步骤会帮您创建一个UID=1000，GID=1000，用户名为yobot的用户，用于管理yobot及docker的运行。  
请执行以下命令:  
```shell script
groupadd -g 1000 yobot
useradd -u 1000 -g 1000 -m yobot
```
之后，请为您的账户设置一个密码：  
```shell script
passwd yobot
```
**（可选）**将yobot用户加入docker用户组内，无需使用sudo调用docker进行运行：  
```shell script
usermod -aG docker yobot
```
然后切换至运行yobot的账户：  
```shell script
su - yobot
```
克隆一份yobot的源码：  
```shell script
git clone https://github.com/pcrbot/yobot.git
```
或者使用国内镜像源 https://gitee.com/yobot/yobot.git
如果您按照上述步骤执行了，后续的源码均指刚刚从git仓库克隆下来的这份源码。  
按照上述步骤执行完后，如果没有问题，接下来您可以继续看下一个大标题 **拷贝、修改项目配置** 了。  

### UID=1000的用户被占用时的解决方法
如果您已经使用过linux系统一段时间，熟悉用户及用户组权限的设置，或者您已经在您的服务器上创建了UID=1000的用户，用户创建受到阻碍：  
对于用户已经存在的情况：建议您**添加该用户至docker用户组**，切换到该用户，并使用该用户对docker进行管理。  
对于用户已经存在但您~~不想用~~，执意**使用root用户**管理docker的情况：  
目前的最佳解决办法是，将git仓库的权限转移至UID=1000的用户下。  
在yobot的源码根目录下执行如下命令：  
```shell script
chown -R 1000:1000 .
```
之后您也可以看**下一个大标题**了。  

#### 没有root也没有UID=1000用户时的解决方法
如果您没有通行root账户权限，只能使用非UID=1000账户运行docker的话：  
dockerfile当中预留了编译时指定用户UID的编译参数：  
```dockerfile script
ARG PUID=1000
```
建议您参考docker-compose文件内的运行配置，[手动指定ARG进行构建](https://gitbook.docker-practice.com/image/dockerfile/arg)并运行，或者使用--user参数将本地用户映射到docker内用户(不推荐)。  
由于cqhttp输出的配置文件同样属于UID=1000的用户，所以极其不推荐这种方法。  
~~一般来说能遇到这种情况您大概也不需要这份教程~~  


## 拷贝、修改项目配置
进入管理用户所持有项目的根目录下： 
```shell script
cp .env.example .env
nano .env  # 或者使用 vim 等其他编辑器
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
之后请登录您的QQ，如遇"下载Chrome"字样提示，请取消重新登录。  
如果您在NOVNC页面遇到了问题，或者QQ无法登录的话，请在[CQHTTP-issue](https://github.com/richardchien/coolq-http-api/issues)中进行提问。  

## 验证安装

向机器人发送“version”，机器人会回复当前版本

## 开启web

见[开启 web](../usage/web-mode.md)

## 常见问题

见 [FAQ](../usage/faq.md)

## Windows部署Docker可能出现的问题

由于本项目的Docker镜像基于Linux系统，默认文件结尾符为**LF**  
而 Windows 系统的默认文件结尾符为**CRLF**  
所以**极 度 不 推 荐**您在 Windows 系统上使用我们提供的**docker-compose.yml**进行部署，因为我们默认会将整个目录挂载入Docker以供数据持久化保存。  
错误的文件结尾符会导致整个目录被视为更改状态，无法应用自动更新。