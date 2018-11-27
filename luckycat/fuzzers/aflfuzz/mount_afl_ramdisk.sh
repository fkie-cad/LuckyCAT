#!/bin/bash
path_to_disk=/tmp/afl-ramdisk
echo "Mounting 2GB tmpfs to $path_to_disk"
mkdir -p $path_to_disk && chmod 777 $path_to_disk
sudo mount -t tmpfs -o size=2048M tmpfs $path_to_disk
