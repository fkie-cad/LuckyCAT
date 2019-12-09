#!/bin/bash

#ip link set down eth0

FIRMWARE_DIR=/fuzz_ramdisk/firmware_root

# AFL setup
echo core >/proc/sys/kernel/core_pattern
cd /sys/devices/system/cpu
echo performance | tee cpu*/cpufreq/scaling_governor
cd -

cp -R /fuzzing/* /fuzz_ramdisk/

CORES=$1
shift
FULL_PATH=$FIRMWARE_DIR$1
shift

# setup master
afl-fuzz -Q -M MASTER -m 2048 -i /fuzz_ramdisk/test_cases -o /fuzz_ramdisk/output -- $FULL_PATH $@ &
echo "Started master in background"

# setup slaves
SLAVE_COUNT=$(expr $CORES - 1)
for i in $(seq 1 $SLAVE_COUNT); do
  afl-fuzz -Q -S SLAVE$i -m 2048 -i /fuzz_ramdisk/test_cases -o /fuzz_ramdisk/output -- $FULL_PATH $@ &
  echo "Set up slave $i in background"
done

# endless loop to keep container alive, afl-utils started stuff in screen sessions
while :; do sleep 10; done
