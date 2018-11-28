#!/bin/bash
echo "Preparing AFL Lucky CAT demo."
if ! type "afl-fuzz" &> /dev/null; then
    echo "Installing requirements"
    sudo ./install.sh
fi

echo "Creating RAM disk"
./mount_afl_ramdisk.sh
echo "Getting demo test case"
./get_demo_testcase.sh 
echo "Preparing AFL"
sudo ./prepare_afl.sh 
