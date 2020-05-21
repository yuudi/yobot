FROM python:3.7-slim-buster
LABEL maintainer="AzurCrystal"

ARG PUID=1000
ENV PYTHONIOENCODING=utf-8
RUN set -x \ 
        && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
        && echo 'Asia/Shanghai' >/etc/timezone \
        && { \
                echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main contrib non-free"; \
                echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-updates main contrib non-free"; \
                echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-backports main contrib non-free"; \
                echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security buster/updates main contrib non-free"; \
        } > /etc/apt/sources.list \
        && rm -rf /var/lib/apt/lists/* \
        && apt-get clean \
        && apt-get update \
        && apt-get install git -y --no-install-recommends --no-install-suggests \
        && useradd -u $PUID -m yobot \
        && su yobot -c \
                "mkdir -p /home/yobot \
                && cd /home/yobot \
                && git clone https://gitee.com/yobot/yobot.git \
                && { \
                        echo '#!/bin/sh'; \
                        echo 'cd /home/yobot/yobot/src/client && python3 /home/yobot/yobot/src/client/main.py && sh /home/yobot/yobot/src/client/yobotg.sh'; \
                } > /home/yobot/entry.sh \
		&& chmod 755 /home/yobot/entry.sh \
		&& chmod +x /home/yobot/entry.sh" \
        && pip3 install --no-cache-dir -r /home/yobot/yobot/src/client/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
        && apt-get clean autoclean \
        && apt-get autoremove -y \
        && rm -rf /var/lib/apt/lists/*

USER yobot

WORKDIR /home/yobot

EXPOSE 9222

VOLUME /home/yobot/yobot

ENTRYPOINT /home/yobot/entry.sh
