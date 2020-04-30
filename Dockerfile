FROM python:3.7
LABEL author="winrey"

#print()时在控制台正常显示中文
ENV PYTHONIOENCODING=utf-8

# 设置系统时间与时区
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo 'Asia/Shanghai' >/etc/timezone

# 安装需要的python库
ADD src/client/requirements.txt /build/requirements.txt

RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r /build/requirements.txt \
    && rm /build/requirements.txt

# 代码复制过来后的路径
RUN mkdir /code

# 添加环境变量
#RUN export PYTHONPATH=$PYTHONPATH:/code

ADD src/client/. /code

WORKDIR /code

RUN python3 main.py

CMD ["sh", "yobotg.sh"]