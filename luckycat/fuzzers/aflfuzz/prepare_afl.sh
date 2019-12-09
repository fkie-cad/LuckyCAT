#!/bin/bash
# EXECUTE AS ROOT
echo core >/proc/sys/kernel/core_pattern
cd /sys/devices/system/cpu || exit
echo performance | tee cpu*/cpufreq/scaling_governor
