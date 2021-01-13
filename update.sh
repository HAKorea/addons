#!/bin/bash

READTREE_REPO=("sds_wallpad")

DIRS=`ls -d ./*/|sed 's/\.//g'|sed 's/\///g'`

in_array() {
    local needle array value
    needle="${1}"; shift; array=("${@}")
    for value in ${array[@]}; do [ "${value}" == "${needle}" ] && echo "true" && return; done
    echo "false"
}

for i in ${DIRS};do
        echo "$i";

        array_check=`in_array $i ${READTREE_REPO[@]}`
        if [ "${array_check}" == "true" ]; then

		result=`git diff $i/master:$i/config.json $i/config.json`

		if [[ -n $result ]];then
	      		echo `rm -rf $i` 
			echo `git add -A`
			echo `git commit -m $i" deleted"`	
              		echo `git read-tree --prefix=$i -u $i:$i`
			echo `git commit -m $i" refreshed"`	
              		echo -e "<<<<<<<<<<<<<<<<<<< read-tree\n"
		else
			echo -e ">>>>>>>>>>>>>>>>>>> NO UPDATE\n"
		fi
        else
              	echo `git subtree pull --prefix=$i $i master`
              	echo -e "<<<<<<<<<<<<<<<<<<< subtree\n"
        fi
done

