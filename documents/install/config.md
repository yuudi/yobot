# 配置文件

高亮部分必要，其他部分供参考，详细说明参考[httpapi文档](https://cqhttp.cc/docs/#/Configuration)

不懂就全部复制

```json {2-7}
{
    "use_http": false,
    "use_ws": false,
    "use_ws_reverse": true,
    "ws_reverse_api_url": "ws://127.0.0.1:9222/ws/api/",
    "ws_reverse_event_url": "ws://127.0.0.1:9222/ws/event/",
    "access_token": "your-token",
    "host": "[::]",
    "port": 5700,
    "ws_host": "[::]",
    "ws_port": 6700,
    "ws_reverse_url": "ws://127.0.0.1:9222",
    "ws_reverse_reconnect_interval": 4000,
    "ws_reverse_reconnect_on_code_1000": true,
    "post_url": "",
    "secret": "",
    "post_message_format": "string",
    "serve_data_files": false,
    "update_source": "github",
    "update_channel": "stable",
    "auto_check_update": false,
    "auto_perform_update": false,
    "show_log_console": true,
    "log_level": "info"
}
```
