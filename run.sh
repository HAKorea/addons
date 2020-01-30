#!/bin/sh

JS_FILE="commax_homegateway.js"

if [ ! -f /data/$JS_FILE ]; then
        mv /$JS_FILE /data/
fi

CONFIG_PATH=/data/options.json

SERIALPORT=$(jq --raw-output ".serialport" $CONFIG_PATH)
MQTTHOST=$(jq --raw-output ".MQTT.server" $CONFIG_PATH)
MQTTUSER=$(jq --raw-output ".MQTT.username" $CONFIG_PATH)
MQTTPASSWORD=$(jq --raw-output ".MQTT.password" $CONFIG_PATH)

JS_FILE=/data/$JS_FILE

sed -i "s|%%SERIALPORT%%|$SERIALPORT|g" $JS_FILE
sed -i "s|%%MQTTHOST%%|$MQTTHOST|g" $JS_FILE
sed -i "s|%%MQTTUSER%%|$MQTTUSER|g" $JS_FILE
sed -i "s|%%MQTTPASSWORD%%|$MQTTPASSWORD|g" $JS_FILE

# start server
echo "[Info] Commax Wallpad Controller stand by..."

node $JS_FILE


while true; do echo "still live"; sleep 1800; done
