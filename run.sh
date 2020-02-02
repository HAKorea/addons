#!/bin/sh

CUSTOM_FILE=$(jq --raw-output ".customfile" $CONFIG_PATH)
MODEL=$(jq --raw-output ".model" $CONFIG_PATH)

JS_FILE=$MODEL".js"
CONFIG_PATH=/data/options.json
SHARE_DIR=/share

if [ -f $SHARE_DIR/$CUSTOM_FILE ]; then
	echo "[Info] Initializing with Custom file: "$CUSTOM_FILE
	JS_FILE=$CUSTOM_FILE
else
  	if [ ! -f $SHARE_DIR/$JS_FILE ]; then
        	mv /js/$JS_FILE $SHARE_DIR
	fi
fi

# start server
echo "[Info] Wallpad Controller stand by... : "$JS_FILE

JS_FILE=/$SHARE_DIR/$JS_FILE
node $JS_FILE

while true; do echo "still live"; sleep 1800; done
