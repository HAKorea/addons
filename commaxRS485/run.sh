#!/bin/sh

JS_FILE="commax_homegateway.js"
CONFIG_PATH=/data/options.json
RESET=$(jq --raw-output ".reset" $CONFIG_PATH)
SHARE_DIR=/share/commax

if [ ! -f $SHARE_DIR/$JS_FILE -o "$RESET" = true ]; then
	echo "[Info] Initializing "$JS_FILE

	SERIALPORT=$(jq --raw-output ".serialport" $CONFIG_PATH)
	MQTTHOST=$(jq --raw-output ".MQTT.server" $CONFIG_PATH)
	MQTTUSER=$(jq --raw-output ".MQTT.username" $CONFIG_PATH)
	MQTTPASSWORD=$(jq --raw-output ".MQTT.password" $CONFIG_PATH)

	sed -i "s|%%SERIALPORT%%|$SERIALPORT|g" /$JS_FILE
	sed -i "s|%%MQTTHOST%%|$MQTTHOST|g" /$JS_FILE
	sed -i "s|%%MQTTUSER%%|$MQTTUSER|g" /$JS_FILE
	sed -i "s|%%MQTTPASSWORD%%|$MQTTPASSWORD|g" /$JS_FILE
  if [ -f $SHARE_DIR/$JS_FILE ]; then
	mv $SHARE_DIR/$JS_FILE $SHARE_DIR/$JS_FILE.bak
  else
	mkdir $SHARE_DIR
  fi
        mv /$JS_FILE $SHARE_DIR
else
	echo "[Info] Skip initializing "$JS_FILE
fi

JS_FILE=$SHARE_DIR/$JS_FILE

# start server
echo "[Info] Commax Wallpad Controller stand by..."

node $JS_FILE

#while true; do echo "still live"; sleep 1800; done
