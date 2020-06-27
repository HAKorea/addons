#!/bin/sh

ADDON_FILE=sds_wallpad.py
OPTION_FILE=options_standalone.json
EXAMPLE_FILE=options_example.json

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
	echo "copy $EXAMPLE_FILE to $OPTION_FILE! you should edit $OPTION_FILE from now on."
	cp $EXAMPLE_FILE $OPTION_FILE
fi

python3 $ADDON_FILE $OPTION_FILE
