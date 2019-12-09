#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Usage: run_fuzz_job.sh NUMBER_OF_CORES RAM_IN_GB INTERNAL_NETWORK PATH_TO_FILE ARGS_FOR_FILE FIRMWARE_ROOT TEST_CASES"
  echo "NOTE: Use an absolute path for PATH_TO_FILE FIRMWARE_ROOT and TEST_CASES!"
  echo "EXAMPLE: ~/path/this/script.sh 4 8 10.1.1.0 /full/path/to/file @@ /full/path/to/rootfs /full/path/to/testcases/"
  exit 1
fi

echo "[*] Attempting to find existing no-internet subnet..."
id_of_existing_no_internet=$(docker network inspect --format "{{.ID}}" 'no-internet')
if [ $? != 0 ]; then
  no_internet=$(docker network create --internal --subnet $3/24 no-internet)
  echo "[+] Created new subnet!"
else
  no_internet=$id_of_existing_no_internet
  echo "[+] Reused existing network"
fi

#---------------------------------------------------------------------------------------------------
cpu_cores=$(expr $1 - 1)
rel_path=$(python3 return_path.py $4 $6)

echo "[*] Launching docker container with: $1 Cores || $2G of RAM || on iface $no_internet"

docker run --net=$no_internet --cpuset-cpus=0,$cpu_cores --memory=$2G --tmpfs /fuzz_ramdisk:exec,suid,dev,mode=1777,size=512m -v $6:/fuzzing/firmware_root/ -v $7:/fuzzing/test_cases/ --privileged fact/firmware-afl-fuzzer:latest $1 $rel_path $5
