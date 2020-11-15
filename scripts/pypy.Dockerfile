FROM pypy:3.7-slim
LABEL maintainer="yobot"

ENV PYTHONIOENCODING=utf-8

ADD src/client/ /yobot

RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo 'Asia/Shanghai' >/etc/timezone \
    && cd /yobot \
    && pip install -r requirements.txt --no-cache-dir \
    && { \
        echo "echo \$\$ > yobotg.pid"; \
        echo "loop=true"; \
        echo "while \$loop"; \
        echo "do"; \
        echo "    loop=false"; \
        echo "    pypy3 main.py -g"; \
        echo "    if [ -f .YOBOT_RESTART ]"; \
        echo "    then"; \
        echo "        loop=true"; \
        echo "        rm .YOBOT_RESTART"; \
        echo "    fi"; \
        echo "done";  \
        } > yobotg.sh \
    && chmod +x yobotg.sh

WORKDIR /yobot

EXPOSE 9222

VOLUME /yobot/yobot_data

CMD ["sh", "yobotg.sh"]
