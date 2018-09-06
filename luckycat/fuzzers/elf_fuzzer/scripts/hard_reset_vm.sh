#!/bin/bash

echo "Killing VM..."
killall qemu-system-x86_64
cd /media/firmware/vms/openbsd_x64/
cd /media/firmware/vms/netbsd_amd64/
#cd /media/firmware/vms/freebsd_amd64/
#rm freebsd.img
#rm openbsd.img
rm netbsd.img
echo "Restoring backup image..."
#cp freebsd.img.backup freebsd.img
#cp openbsd.img.backup openbsd.img
cp netbsd.img.backup netbsd.img
echo "Starting restored VM..."
./start.sh &
sleep 60
echo "VM reset done."
