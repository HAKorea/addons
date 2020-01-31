#!/bin/sh

DIRS=`ls -d ./*/|sed 's/\.//g'|sed 's/\///g'`
  
for i in ${DIRS};do
      echo "$i";
`git subtree pull --prefix=$i $i master`	
done
