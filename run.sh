#!/bin/bash
set -e

CONFIG_PATH=/data/options.json

PROJECT_ID=$(jq --raw-output ".project_id" $CONFIG_PATH)
DEVICE_MODEL_ID=$(jq --raw-output ".model_id" $CONFIG_PATH)

#MIC=$(jq --raw-output ".mic" $CONFIG_PATH)
#SPEAKER=$(jq --raw-output ".speaker" $CONFIG_PATH)
#ASOUND_CONF=/root/.asoundrc
#sed -i "s|%%MIC%%|$MIC|g" $ASOUND_CONF
#sed -i "s|%%SPEAKER%%|$SPEAKER|g" $ASOUND_CONF

if [ ! -d /share/gawebserver ]; then
	echo "[Error] You must make /share/gawebserver Directory and put client_secret.json"
	mkdir /share/gawebserver
	exit 1
else
	if [ ! -d /share/gawebserver/assistant ]; then
		echo "[Info] create assistant dir..."
		mkdir /share/gawebserver/assistant
	fi
	echo "[Info] link assistant dir. to root/.config..."
	ln -s /share/gawebserver/assistant /root/.config/google-assistant-library/assistant
fi

if [ -f /share/gawebserver/.asoundrc ]; then
	echo "[Info] Copy .asoundrc to root"
	cp /share/gawebserver/.asoundrc /root/
fi

ACCESS_TOKEN=/share/gawebserver/access_token.json
CLIENT_SECRET=/share/gawebserver/client_secret.json

/root/ascii2utf8.sh && echo "[Info] change assistant.py for using UTF-8"

if [ ! -f "$ACCESS_TOKEN" ] && [ -f "$CLIENT_SECRET" ]; then
    echo "[Info] Start WebUI for handling oauth2"
    python3 /oauth.py "$CLIENT_SECRET" "$ACCESS_TOKEN"
elif [ ! -f "$ACCESS_TOKEN" ]; then
    echo "[Error] You need initialize GoogleAssistant with a client secret json!"
    exit 1
fi

exec python3 /gawebserver.py --credentials "$ACCESS_TOKEN" --project-id "$PROJECT_ID" --device-model-id "$DEVICE_MODEL_ID" < /dev/null


