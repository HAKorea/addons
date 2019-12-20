#!/bin/sh

/makeconf.sh
mv /rs485.py /data/

echo "[Info] Run Wallpad Controller"
python3 rs485.py


