#!/bin/bash

echo "Installing tmux"
sudo apt install tmux

echo "Installing afl"
sudo apt install afl-cov afl

echo "Installing afl-utils"
git clone https://github.com/rc0r/afl-utils /tmp/afl-utils
cd /tmp/afl-utils
sudo python3 setup.py install
cd -
