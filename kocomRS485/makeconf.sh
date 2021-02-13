#!/bin/sh

CONFIG_FILE=/data/options.json
CONFIG_RS485=/share/kocom/rs485.conf

CONFIG=`cat $CONFIG_FILE`

> $CONFIG_RS485

for i in $(echo $CONFIG | jq -r 'keys_unsorted | .[]')
do
  if [ $i == "Advanced" ]
  then 
    break
  fi 
  echo "[$i]" >> $CONFIG_RS485
  echo $CONFIG | jq --arg id "$i" -r '.[$id]|to_entries|map("\(.key)=\(.value|tostring)")|.[]' | sed -e "s/false/False/g" -e "s/true/True/g" >> $CONFIG_RS485
done

