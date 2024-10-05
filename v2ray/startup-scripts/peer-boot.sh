#!/bin/bash

v2ray --config=/etc/v2ray/config.json run &

cd src || exit

python3 client.py
