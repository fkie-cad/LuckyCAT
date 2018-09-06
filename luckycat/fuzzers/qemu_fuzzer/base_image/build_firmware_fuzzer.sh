#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: build_firmware_fuzzer.sh ARCH"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "[!] Dockerfile not found. Aborting..."
fi

docker build --no-cache -t fact/firmware-afl-fuzzer:latest --build-arg arch=$1 .

if [ -d $TMP_DIR ]; then
    echo "Deleting tmp dir.";
    rm -rf $TMP_DIR
fi

echo "[+] Done."
