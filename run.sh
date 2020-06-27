#!/bin/sh

ADDON_FILE=sds_wallpad.py
OPTION_FILE=options_standalone.json
EXAMPLE_FILE=options_example.json

if [ ! -f $OPTION_FILE ]; then
	echo "copy $EXAMPLE_FILE to $OPTION_FILE! you should edit $OPTION_FILE from now on."
	cp $EXAMPLE_FILE $OPTION_FILE
fi

python3 $ADDON_FILE $OPTION_FILE
