#!/bin/bash

echo "Verifying crash originated from one of the ELFs in $1"
scp -P$2 exec_elf.sh max@localhost:/tmp/exec_elf.sh
mkdir -p /tmp/verify
cd /tmp/verify
cp -v $1 /tmp/verify/verify.tar.gz
pwd
tar -xvf /tmp/verify/verify.tar.gz
rm /tmp/verify/verify.tar.gz

for f in $(find . -exec file {} \; | grep -i ELF | cut -d: -f1); do
    echo "Verifying $f"
    /usr/bin/timeout 5 ssh max@localhost -p$2 "rm /tmp/elf_verify"
    scp -P$2 $f max@localhost:/tmp/elf_verify
    /usr/bin/timeout 20 ssh max@localhost -p$2 "/tmp/exec_elf.sh"
    if /usr/bin/timeout 5 ssh max@localhost -p$2 "exit"; then
        continue
    else
        echo "Kernel crash probably provoked by $f"
        cp $f /home/thomas/code/daemons/analysis_scripts/elf_fuzzing/results/verified_$3
        break
    fi
done

/usr/bin/timeout 10 ssh max@localhost -p$2 "rm /tmp/*.core"

echo "Cleaning up temp data..."
cd /tmp
rm -rf /tmp/verify 
