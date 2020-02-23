# 配置文件说明

`host` 服务绑定的地址，默认值`0.0.0.0`

`port` 服务绑定的地址，默认值 `9222`

`public_on` 开启 web 模式，默认值 ``true``

`public_addr` web 模式可以被访问的地址（如 nginx 代理后的地址），如`https://192.168.3.13:9222/yobot/`，默认自动检测

`public_basepath` web 模式使用的目录（防止与其他应用冲突），如 `/yobot/`，默认值`/`

`access_token` 与 httpapi 通信的 token，默认值 `null`

`super-admin` 管理员 user_id 列表

`black-list` 黑名单 user_id 列表

`setting-restrict` 权限控制，`0`仅主人，`1`群主，`2`管理员，`3`所有人，默认值 `3`

`auto_update` 自动更新，默认值 `true`

`update-time` 自动更新时间，默认值 `03:30`

`show_jjc_solution` jjc查询结果显示方式，可选`text` `url`，默认值 `url`

`jjc_auth_key` jjc查询授权码，默认值 `null`

`gacha_on` 开启群聊抽卡功能，默认值 `true`

`gacha_private_on` 开启私聊抽卡功能，默认值 `true`

`news_jp_official` 开启日服官网新闻推送，默认值 `true`

`news_jp_twitter` 开启日服推特新闻推送，默认值 `true`

`news_tw_official` 开启台服官网新闻推送，默认值 `true`

`news_tw_facebook` 开启台服 FaceBook 新闻推送，默认值 `true`

`news_cn_official` 开启国服官网新闻推送，默认值 `true`

`news_cn_bilibili` 开启国服 Bilibili 动态新闻推送，默认值 `true`

`news_interval_minutes` 新闻推送检测间隔分钟，默认值 30

`calender_region` 日程表地区，可选`jp` `tw` `cn`

`calender_on` 每日提醒日程，默认值 `true`

`calender_time` 每日提醒日程时间，默认值 `08:00`

`notify_groups` 每日提醒与新闻推送群组

`notify_privates` 每日提醒与新闻推送私聊

`preffix_on` 指令前缀开关（提高性能，防止误触发），默认值 `false`

`preffix_string` 指令前缀字符串

`zht_in` 接受繁中输入（降低性能），默认值 `false`

`zht_out` 输出转化为繁中，默认值 `false`

`zht_out_style` 输出转化为繁中风格，可选`s2t` `s2tw` `s2hk` `s2twp`，默认值 `s2t`
