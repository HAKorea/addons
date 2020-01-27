#!/bin/sh

sshpass -p "myServer2Password" scp -o StrictHostKeyChecking=no $1 userid@server2ipAddress:/pass/to/homeassistant/www/motion/video && \
sleep 3
rm $1
