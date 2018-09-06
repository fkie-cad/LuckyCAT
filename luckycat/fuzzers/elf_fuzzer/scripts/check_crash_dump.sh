#!/bin/sh
RES=`ls /var/crash/ | wc -l | tr -d '[:space:]'`
if [ $RES != "1" ]; then
    echo "CRASH"
else
    echo "CONT"
fi
