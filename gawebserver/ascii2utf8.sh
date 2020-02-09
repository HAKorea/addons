#!/bin/bash

INPUT_FILE=/usr/local/lib/python3.5/dist-packages/google/assistant/library/assistant.py

sed -i "s/query.encode('ASCII/query.encode('UTF-8/g" $INPUT_FILE
