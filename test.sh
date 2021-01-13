#!/bin/bash

result=`git diff sds_wallpad/master:sds_wallpad/README.md sds_wallpad/README.md`
#result=`git diff sds_wallpad/master:README.md sds_wallpad/README.md`
echo $result

if [[ -n "$result" ]];then
 	echo "get result"
else 
	echo "no result"
fi


