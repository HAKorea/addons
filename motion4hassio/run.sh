#!/bin/sh


CONFIG_PATH=/data/options.json

VIDEODEVICE=$(jq --raw-output ".videodevice" $CONFIG_PATH)
WIDTH=$(jq --raw-output ".width" $CONFIG_PATH)
HEIGHT=$(jq --raw-output ".height" $CONFIG_PATH)
FRAMERATE=$(jq --raw-output ".framerate" $CONFIG_PATH)
TEXTRIGHT=$(jq --raw-output ".text_right" $CONFIG_PATH)
ROTATE=$(jq --raw-output ".rotate" $CONFIG_PATH)
TARGETDIR=$(jq --raw-output ".target_dir" $CONFIG_PATH)
ONEVENTSTART=$(jq --raw-output ".on_event_start" $CONFIG_PATH) 
ONEVENTEND=$(jq --raw-output ".on_event_end" $CONFIG_PATH)
ONMOVIEEND=$(jq --raw-output ".on_movie_end" $CONFIG_PATH)
MOVIEOUTPUT=$(jq --raw-output ".movie_output" $CONFIG_PATH)
MOVIEMAXTIME=$(jq --raw-output ".movie_max_time" $CONFIG_PATH)
MOVIEQUALITY=$(jq --raw-output ".movie_quality" $CONFIG_PATH)
MOVIECODEC=$(jq --raw-output ".movie_codec" $CONFIG_PATH)
SNAPSHOTINTERVAL=$(jq --raw-output ".snapshot_interval" $CONFIG_PATH) 
SNAPSHOTNAME=$(jq --raw-output ".snapshot_name" $CONFIG_PATH) 
PICTUREOUTPUT=$(jq --raw-output ".picture_output" $CONFIG_PATH)
PICTURENAME=$(jq --raw-output ".picture_name" $CONFIG_PATH)
WEBCONTROLLOCAL=$(jq --raw-output ".webcontrol_local" $CONFIG_PATH)

MOTION_CONF=/etc/motion/motion.conf

sed -i "s|%%VIDEODEVICE%%|$VIDEODEVICE|g" $MOTION_CONF
sed -i "s|%%WIDTH%%|$WIDTH|g" $MOTION_CONF
sed -i "s|%%HEIGHT%%|$HEIGHT|g" $MOTION_CONF
sed -i "s|%%FRAMERATE%%|$FRAMERATE|g" $MOTION_CONF
sed -i "s|%%TEXTRIGHT%%|$TEXTRIGHT|g" $MOTION_CONF
sed -i "s|%%ROTATE%%|$ROTATE|g" $MOTION_CONF
sed -i "s|%%TARGETDIR%%|$TARGETDIR|g" $MOTION_CONF
sed -i "s|%%MOVIEOUTPUT%%|$MOVIEOUTPUT|g" $MOTION_CONF
sed -i "s|%%MOVIEMAXTIME%%|$MOVIEMAXTIME|g" $MOTION_CONF
sed -i "s|%%MOVIEQUALITY%%|$MOVIEQUALITY|g" $MOTION_CONF
sed -i "s|%%MOVIECODEC%%|$MOVIECODEC|g" $MOTION_CONF
sed -i "s|%%SNAPSHOTINTERVAL%%|$SNAPSHOTINTERVAL|g" $MOTION_CONF
sed -i "s|%%SNAPSHOTNAME%%|$SNAPSHOTNAME|g" $MOTION_CONF
sed -i "s|%%PICTUREOUTPUT%%|$PICTUREOUTPUT|g" $MOTION_CONF
sed -i "s|%%PICTURENAME%%|$PICTURENAME|g" $MOTION_CONF
sed -i "s|%%WEBCONTROLLOCAL%%|$WEBCONTROLLOCAL|g" $MOTION_CONF

if [ "$ONEVENTSTART" == "null" ]
then
	sed -i "/%%ONEVENTSTART%%/d" $MOTION_CONF
else
	sed -i "s|%%ONEVENTSTART%%|$ONEVENTSTART|g" $MOTION_CONF
fi

if [ "$ONEVENTEND" == "null" ]
then
	sed -i "/%%ONEVENTEND%%/d" $MOTION_CONF
else
	sed -i "s|%%ONEVENTEND%%|$ONEVENTEND|g" $MOTION_CONF	
fi

if [ "$ONMOVIEEND" == "null" ]
then
	sed -i "/%%ONMOVIEEND%%/d" $MOTION_CONF
else
	sed -i "s|%%ONMOVIEEND%%|$ONMOVIEEND|g" $MOTION_CONF
fi

if [ ! -d "/config/scripts/motion" ]
then
	echo "[Info] create homeassistant/script/motion directory"
        mv /var/tmp/scripts /config/scripts/motion
	echo "[Info] copy event scripts to homeassistant/script/motion directory"
else 
	echo "[Info] homeassistant/script/motion directory exists. skip copying scripts"
fi

if [ ! -d $TARGETDIR ]; then
	echo "[Info] making TARGET DIRECTORY..."
	mkdir -p $TARGETDIR
else
	echo "[Info] TARGET DIRECTORY already exists"
fi
# start server
echo "[Info] Doorbell Video Capture stand by..."
motion -c $MOTION_CONF

while true; do echo "still live"; sleep 1800; done
