# 多实例

1. 将 yobot 与 酷Q 复制一份新的副本
1. 修改 [yobot配置文件](./configuration.md)中 `port` 字段，建议在 `8000-65535` 之间。
1. 修改 酷Q 中 [httpapi的配置文件](../install/config.md)中所有 `ws_reverse` 相关字段，将 `9222` 修改为你新的端口
1. 参照[开启web方法](./web-mode.md)的方法，为新的端口设置入口。
