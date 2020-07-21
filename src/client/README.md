# 使用方法

## 运行环境

python最低要求为 `python3.6`

## 打包

（一般不建议对 python 项目打包）

安装 `pyinstaller`

```sh
pip install pyinstaller
```

打包程序

```sh
pyinstaller main.spec
```

在 `dist` 中找到目标文件

## 扩展

见[custom.py](./ybplugins/custom.py)文件

## 移植

经过多次迭代，yobot与[cq-http-api](https://github.com/richardchien/coolq-http-api/)的耦合越来越深，不再适合移植了
