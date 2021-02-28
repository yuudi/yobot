# 开发注意事项

默认配置下，此目录下的文件会被 gzip 压缩缓存。修改源文件不会立刻反映在浏览器中。开发时请在配置文件中将 `web-gzp` 值设置为 `0`

或者使用下面的命令删除所有缓存

```shell
# 查看所有 .gz 文件
find . -name "*.gz" -type f

# 删除所有 .gz 文件
find . -name "*.gz" -type f -delete
```
