#!/bin/bash

git remote add $1 https://github.com/zooil/$1
git subtree add --prefix=$1 $1 master

echo $1" repository locally added"
