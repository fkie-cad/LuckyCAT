#!/usr/bin/env bash
set -e

sudo apt-get update && sudo apt-get install lsof python3-dev python3-pip
curl -fsSL get.docker.com -o get-docker.sh && sh get-docker.sh && sudo gpasswd -a $USER docker && newgrp docker
sudo -EH pip3 install docker-compose
sudo systemctl enable docker
sudo systemctl start docker
git clone https://github.com/fkie-cad/LuckyCAT.git -b "arm_rpi3_32bit" && cd LuckyCAT && ./start_cluster.sh 

