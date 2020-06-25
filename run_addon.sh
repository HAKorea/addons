#!/bin/sh

SHARE_DIR=/share
ADDON_FILE=sds_wallpad.py

if [ ! -f $SHARE_DIR/$ADDON_FILE ]; then
	echo "[Info] copy latest file to $SHARE_DIR ..."
	cp /srv/$ADDON_FILE $SHARE_DIR/
fi

echo "[Info] run $ADDON_FILE ..."
python3 $SHARE_DIR/$ADDON_FILE "/data/options.json"
echo "[Info] unexpected exit!"
