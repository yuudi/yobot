FROM python:3.7-slim-buster
LABEL maintainer="yobot"

ENV PYTHONIOENCODING=utf-8

ADD src/client/ /yobot

RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo 'Asia/Shanghai' >/etc/timezone \
    && cd /yobot \
    && pip3 install aiocqhttp==0.6.8 Quart==0.6.15 --no-cache-dir \
    && pip3 install -r requirements.txt --no-cache-dir \
    && python3 main.py \
    && chmod +x yobotg.sh

WORKDIR /yobot

EXPOSE 9222

VOLUME /yobot/yobot_data

ENTRYPOINT /yobot/yobotg.sh
