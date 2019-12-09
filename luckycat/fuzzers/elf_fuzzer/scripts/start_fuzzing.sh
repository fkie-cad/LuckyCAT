#!/bin/bash

PORT=$1
COMPAT_GENERATION=$2 #bsd/linux
RESULT_FOLDER=$3
VM=$4
echo "Starting fuzzing ELFs on port $1"
echo "Generation type: $2"
echo "Results go to: $3"
echo "Path to VM: $4"

echo "Starting VM."
cd $VM
$VM/start.sh &
cd -
VM_PID=$!
echo "Started VM with PID $VM_PID"
echo "Waiting for VM to start"
sleep 60
echo "Starting with the fuzzing..."

COUNTER=1
while true; do
  scp -P$1 generate_elfs.sh max@localhost:/tmp/
  scp -P$1 fuzz_elfs.sh max@localhost:/tmp/
  echo "Iteration $COUNTER"
  COUNTER=$(($COUNTER + 1))
  DATE=$(date '+%Y-%m-%d_%H_%M_%S')
  echo "Generating ELFs"
  if [ $COMPAT_GENERATION == "linux" ]; then
    echo "Compat generation (linux)"
    ./generate_elfs_compat.sh >/dev/null
    cp -v /tmp/orcs.tar.gz $RESULT_FOLDER/orcs_$1_$DATE.tar.gz
    scp -P$1 /tmp/orcs.tar max@localhost:/tmp/orcs.tar
    ssh max@localhost -p$1 "cd /tmp && tar -xf orcs.tar"
  else
    echo "Native generation (BSD)"
    ssh max@localhost -p$1 "/tmp/generate_elfs.sh" >/dev/null
    scp -P$1 max@localhost:/tmp/orcs.tar.gz $RESULT_FOLDER/orcs_$1_$DATE.tar.gz
    ssh max@localhost -p$1 "rm /tmp/orcs.tar.gz"
  fi
  echo "Fuzzing ELFs"
  /usr/bin/timeout 30 ssh max@localhost -p$1 "/tmp/fuzz_elfs.sh" >$RESULT_FOLDER/res_$1_$DATE.log
  # TODO parse result
  echo "Checking if system still alive"
  RETRY=1
  HARD_RESET=0
  while true; do
    if /usr/bin/timeout 5 ssh max@localhost -p$1 "exit"; then
      break
    else
      echo "VM not up, sleeping..."
      sleep 20
      RETRY=$(($RETRY + 1))
      if [ $RETRY == 20 ]; then
        echo "Killing VM with PID $VM_PID"
        kill -9 $VM_PID
        echo "Resetting VM..."
        cd $VM
        $VM/reset.sh
        echo "Restarting VM..."
        $VM/start.sh &
        cd -
        VM_PID=$!
        HARD_RESET=1
        break
      fi
    fi
  done

  if [ $HARD_RESET == 1 ]; then
    echo "Conducted hard reset of VM. May be due to kernel crash.I won't delete the data, do a manual verification..."
    mv $RESULT_FOLDER/res_$1_$DATE.log $RESULT_FOLDER/hard_reset_res_$1_$DATE.log
    mv $RESULT_FOLDER/orcs_$1_$DATE.tar.gz $RESULT_FOLDER/hard_reset_orcs_$1_$DATE.tar.gz
    continue
  fi

  echo "Checking for Crash Dump"
  scp -P$1 check_crash_dump.sh max@localhost:/tmp/
  scp -P$1 compress_dump.sh max@localhost:/tmp/
  ssh max@localhost -p$1 "/tmp/check_crash_dump.sh" >/tmp/check_crash_$1.log
  if grep -q "CRASH" /tmp/check_crash_$1.log; then
    echo "CRASH DUMP DETECTED!"
    ssh root@localhost -p$1 "/tmp/compress_dump.sh"
    scp -P$1 root@localhost:/tmp/last_crash.tar.gz $RESULT_FOLDER/crash_dump_$1_$DATE.tar.gz
    ./verify_crash.sh $RESULT_FOLDER/orcs_$1_$DATE.tar.gz $1 $DATE
  else
    echo "No crash dump detected. Removing temp data of run..."
    rm $RESULT_FOLDER/res_$1_$DATE.log
    rm $RESULT_FOLDER/orcs_$1_$DATE.tar.gz
  fi
done
