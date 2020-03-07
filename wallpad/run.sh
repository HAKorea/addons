#!/bin/sh

CONFIG_PATH=/data/options.json
SHARE_DIR=/share

CUSTOM_FILE=$(jq --raw-output ".customfile" $CONFIG_PATH)
MODEL=$(jq --raw-output ".model" $CONFIG_PATH)
TYPE=$(jq --raw-output ".type" $CONFIG_PATH)
JS_FILE=$MODEL"_"$TYPE"_wallpad.js"

if [ -f $SHARE_DIR/$CUSTOM_FILE ]; then
	echo "[Info] Initializing with Custom file: "$CUSTOM_FILE
	JS_FILE=$CUSTOM_FILE
else
  	if [ ! -f $SHARE_DIR/$JS_FILE ]; then
		LS_RESULT=`ls $SHARE_DIR | grep wallpad`
		if [ $? -eq 0 ]; then
			rm $SHARE_DIR/*wallpad.js
		fi
        cp /js/$MODEL"_"$TYPE".js" $SHARE_DIR/$JS_FILE
	fi
fi

# start server
echo "[Info] Wallpad Controller stand by... : "$JS_FILE

JS_FILE=/$SHARE_DIR/$JS_FILE
node $JS_FILE

#while true; do echo "still live"; sleep 1800; done
