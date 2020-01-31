#!/bin/sh

SHARE_DIR=/share/kocom_wallpad

if [ ! -f $SHARE_DIR/rs485.py ]; then
	mkdir $SHARE_DIR
	mv /rs485.py $SHARE_DIR
fi
/makeconf.sh

echo "[Info] Run Wallpad Controller"
python3 $SHARE_DIR/rs485.py

# for dev
#while true; do echo "still live"; sleep 100; done
