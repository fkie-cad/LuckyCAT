#!/bin/bash

echo "Installing afl"
# TODO install AFL

echo "Installing afl-utils"
git clone https://github.com/rc0r/afl-utils /tmp/afl-utils
cd /tmp/afl-utils
sudo python3 setup.py install
