#!/bin/sh

/makeconf.sh
if [ ! -f /data/rs485.py ]; then
	mv /rs485.py /data/
fi

echo "[Info] Run Wallpad Controller"
python3 /data/rs485.py

# for dev
#while true; do echo "still live"; sleep 100; done
