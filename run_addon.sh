#!/bin/sh

ADDON_FILE=sds_wallpad.py

echo "[Info] run $ADDON_FILE ..."
python3 /srv/$ADDON_FILE "/data/options.json"
echo "[Info] unexpected exit!"
