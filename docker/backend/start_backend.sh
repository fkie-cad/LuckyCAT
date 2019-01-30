#!/bin/bash
IP=`ip route get 1 | awk '{print $NF;exit}'`
echo "Current ip address is $IP"

echo "Starting Lucky CAT backend"
cd /opt/luckycat
python3 /opt/luckycat/setup.py install &> /dev/null
echo "Waiting for queue..."
sleep 20
luckycat_backend.py

