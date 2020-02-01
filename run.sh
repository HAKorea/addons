#!/bin/sh

JS_FILE="wallpad.js"
CONFIG_PATH=/data/options.json
CUSTOM_FILE=$(jq --raw-output ".customfile" $CONFIG_PATH)
SHARE_DIR=/share

if [ -f $SHARE_DIR/$CUSTOM_FILE ]; then
	echo "[Info] Initializing with "$CUSTOM_FILE
	JS_FILE=$CUSTOM_FILE
else
  	if [ ! -f $SHARE_DIR/$JS_FILE ]; then
        	mv /$JS_FILE $SHARE_DIR
	fi
fi

JS_FILE=$SHARE_DIR/$JS_FILE

# start server
echo "[Info] Wallpad Controller stand by..."

node $JS_FILE

#while true; do echo "still live"; sleep 1800; done
