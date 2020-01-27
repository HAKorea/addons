#!/bin/sh

# Load Default recorder.conf if not available
echo "Make Config File"
/makeconf.sh

ot-recorder --initialize
ot-recorder "$@" 

#while true; do echo "still live"; sleep 100; done
