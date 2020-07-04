#!/bin/sh

ADDON_FILE=sds_wallpad.py
OPTION_FILE=options_standalone.json
GENERATE_OPTION_SCRIPT=generate_options_standalone.py

if which sudo >/dev/null; then
	SUDO=sudo
else
	SUDO=
fi

if which apk >/dev/null; then
	$SUDO apk add --no-cache python3
	$SUDO apk add --no-cache py3-pip
elif which apt >/dev/null; then
	$SUDO apt install -y python3
	$SUDO apt install -y python3-pip
fi

python3 -m pip install --upgrade pip
python3 -m pip install pyserial
python3 -m pip install paho-mqtt

if [ ! -f $OPTION_FILE ]; then
	python3 $GENERATE_OPTION_SCRIPT $OPTION_FILE
	echo "$OPTION_FILE is generated! please modify it then start this script again."
	exit 1
fi

python3 $ADDON_FILE $OPTION_FILE
