#!/bin/bash
IP=`ip route get 1 | awk '{print $NF;exit}'`
echo "Current ip address is $IP"

echo "Waiting for queue and database..."
sleep 5

echo "Starting Fraunhofer FKIE Fuzzing Cluster backend"
cd /opt/luckycat
python3 /opt/luckycat/setup.py install
luckycat_backend.py

