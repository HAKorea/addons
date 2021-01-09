#!/bin/bash

CONFIG_PATH=/data/options.json
WEBDAV_PATH=/share/webdav

USERNAME=$(jq --raw-output ".username" $CONFIG_PATH)
USERPWD=$(jq --raw-output ".password" $CONFIG_PATH)


if [ ! -d $WEBDAV_PATH ]; then
	echo "[Info] making directory /share/webdav/"
	mkdir $WEBDAV_PATH
	chown www-data $WEBDAV_PATH && chmod -R 777 $WEBDAV_PATH
else
	echo "[Info] webdev directory aleady exist. using /share/webdev dir."
fi

if [[ -n "$USERNAME" ]] && [[ -n "$USERPWD" ]]; then
	htpasswd -bc /etc/nginx/users.pass $USERNAME $USERPWD
	echo "[Info] htpasswd setting done"
	echo "[Info] start Webdav"
fi

