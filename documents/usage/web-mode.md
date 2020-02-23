# Web 模式

## 开启 Web 模式

### 方法 1：直接连接

在 yobot 配置文件中，将`host`字段设置为`0.0.0.0`

在服务器的防火墙面板里，打开 9222 端口（如端口更换则为更换后的端口）

警告：如果使用这种方法，**必须**为 httpapi 和 yobot 设定 access_token 防止入侵

### 方法 2：使用 Nginx 代理（推荐）

请根据服务器实际情况设定 Nginx 代理，这里给出一个示例

Nginx 代理配置后，在机器人配置文件中`public_addr`项替换为代理后的地址

```nginx {12-25}
server {
  listen 80;
  listen [::]:80;
  listen 443 ssl http2;
  listen [::]:443 ssl http2;

  ssl_certificate /path/to/ssl_certificate.crt;  # 替换为你的证书路径
  ssl_certificate_key /path/to/ssl_certificate.key;  # 替换为你的私钥路径

  server_name io.yobot.xyz;  # 替换为你的域名

  location /assets/ {
    alias /home/yobot/src/client/public/assets/;  # 替换为你的静态文件目录
    expires 30d;
  }

  location /ws/ {
    allow 127.0.0.0/8;  # Windows 酷Q-httpapi
    allow 172.16.0.0/12;  # Linux 酷Q-httpapi in docker
    deny all;
  }

  location / {
    proxy_pass http://localhost:9222/;
  }
}
```

### 方法 3：使用 Apache 代理

请根据服务器实际情况设定 Apache 代理

## 开始使用 Web 模式

向机器人私聊发送“登录”即可
