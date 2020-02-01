# 作为 nonebot 插件运行

前提：已经安装好[nonebot](https://nonebot.cqp.moe/)（或者其衍生物）并且可以正常运行

[nonebot介绍](/usage/nonebot-introductions.md)

进入nonebot插件目录，添加git的子模块：  

`git submodule add https://github.com/yuudi/yobot.git`  

（或者使用国内源`https://gitee.com/yobot/yobot.git`）  

（或者使用普通git仓库管理`git clone https://gitee.com/yobot/yobot.git`）

安装依赖`pip install -r yobot/src/client/requirements.txt`，重新加载nonebot插件，开始使用
