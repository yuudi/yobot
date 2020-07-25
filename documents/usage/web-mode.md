# Web 模式

机器人开启web模式后，可以使用网页版的公会战交互界面。网页版和群聊版互通。

## 开启 Web 模式

请在服务器上运行软件，[服务器推荐](../install/server.md)

如果坚持在本地计算机运行，也可以使用内网穿透（不建议新手使用）

### 方法 1：直接连接（最简单）

在 yobot [配置文件](./configuration.md)中，将`host`字段恢复为`0.0.0.0`（即默认值，如果没有手动修改过就不用管）

在服务器的防火墙面板里，打开 9222 端口（如端口更换则为更换后的端口）  
（[阿里云开启方法](https://help.aliyun.com/document_detail/25471.html) [腾讯云开启方法](https://cloud.tencent.com/document/product/213/39740)）
如果是腾讯云 Windows 服务器，可能还需要放行 Windows 防火墙

由于不同的服务器提供商所需的步骤不同，所以具体方法请通过搜索引擎搜索：【你的提供商+你的操作系统+如何开放端口】

由于需要和yobot插件版兼容，默认路由设置为/yobot，直接访问根目录会产生405错误。
如果您没有修改路径，请通过 `http://您的公网IP:yobot运行的端口/yobot/` 进行访问。
e.g. `http://10.10.10.10:9222/yobot/`

::: warning

如果使用这种方法，**必须**为 httpapi 和 yobot 设定 access_token 防止入侵

:::

### 方法 2：使用 Nginx 代理（功能最强）

如果需要为网页添加日志记录、HTTPS支持、安全限制等，或者需要同时部署其他站点，可以使用 Nginx、Apache 之类的服务器软件

请根据服务器实际情况设定 Nginx 代理，这里给出一个示例，**不要直接复制**，如果不懂请用工具生成或请熟悉的人代劳

Nginx 代理配置后，在机器人配置文件中`public_address`项替换为代理后的地址，安全起见可以将`host`项设置为`127.0.0.1`

```nginx
server {
  listen 80;
  listen [::]:80;

  ## 使用 https 加密通信，增加安全性（可选）
  # listen 443 ssl http2;
  # listen [::]:443 ssl http2;
  # ssl_certificate /home/www/ssl/ssl_certificate.crt;  # 你的证书路径
  # ssl_certificate_key /home/www/ssl/ssl_certificate.key;  # 你的私钥路径

  server_name io.yobot.xyz;  # 你的域名

  location /
  {
    proxy_pass http://localhost:9222;  # 反向代理
    proxy_set_header X-Real-IP $remote_addr;  # 传递用户IP
  }

  ## 静态文件直接访问（可选，性能）
  #location /yobot/assets/ {
  #  alias /home/yobot/src/client/public/static/;  # 你的静态文件目录，如果你修改了`public_basepath`，请同时修改这里的`location`
  #  expires 30d;
  #}

  ## 输出文件直接访问（可选，性能）
  #location /yobot/output/ {
  #  alias /home/yobot/src/client/yobot_data/output/;  # 你的输出文件目录，如果你修改了`public_basepath`，请同时修改这里的`location`
  #  charset utf-8;  # 设置 HTTP 响应的字符集避免页面出现乱码
  #  expires 30d;
  #}

  # 阻止酷Q接口被访问(可选，安全)
  location /ws/ {
    # allow 172.16.0.0/12;  # 允许酷Q通过（yobot与酷Q不在同一个服务器上时使用，ip为酷Q所在服务器的ip）
    deny all;
  }
}
```

### 方法 3：使用 Apache 代理

请根据服务器实际情况设定 Apache 代理，这里给出一个示例，**不要直接复制**

```apacheconf
<VirtualHost *:80>
  Servername io.yobot.xyz
  ProxyRequests Off
  <Proxy *>
    Order Deny, Allow
    Allow from All
  </Proxy>
  <Location />  # 反向代理
    ProxyPass http://localhost:9222/
    ProxyPassReverse http://localhost:9222/
  </Location>
  <Location "/ws/">  # 阻止酷Q接口被访问
  AllowOverride None
    Order Deny, Allow
    Deny from All
  </Location>
  RemoteIPHeader X-Real-IP  # 传递用户IP
</VirtualHost>
```

## 开始使用 Web 模式

向机器人私聊发送“登录”即可

如果需要密码，向机器人私聊发送“重置密码”即可\(3.5.6+\)

开启 Web 模式后，可以使用[新版公会战](./web-clanbattle.md)

## 不使用 Web 模式（不推荐）

使用旧版的公会战。

在[配置文件](./configuration.md)中，将 `clan_battle_mode` 字段修改为 `chat`
