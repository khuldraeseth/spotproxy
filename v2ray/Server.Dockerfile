FROM python:3.11-slim-bookworm

RUN apt update
RUN apt install v2ray nano iputils-ping iproute2 make wget -y

# Necessary for v2ray to launch
RUN wget -O /usr/bin/geoip.dat https://github.com/v2fly/geoip/releases/latest/download/geoip.dat

WORKDIR /usr/bin/spotproxy-v2ray/

COPY . .
COPY config/server-config.json /etc/v2ray/config.json

RUN pip install -r requirements.txt

EXPOSE 10086/tcp
EXPOSE 10086/udp

CMD startup-scripts/proxy-boot.sh
