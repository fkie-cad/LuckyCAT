#!/bin/bash
git clone https://github.com/symisc/PH7.git /tmp/ph7
cd /tmp/ph7
cp examples/ph7_interp.c .
rsync -av /tmp/ph7 ~/afl-ramdisk/

mkdir -p ~/afl-ramdisk/ph7/fuzzing_in
mkdir -p ~/afl-ramdisk/ph7/crashes
cd ~/afl-ramdisk/ph7/
afl-clang -W -Wall -D PH7_ENABLE_MATH_FUNC -o ph7 ph7_interp.c ph7.c -lm
cd ~/afl-ramdisk/ph7/fuzzing_in
wget https://raw.githubusercontent.com/panique/php-login-one-file/master/index.php

AFL_OUT="~/afl-ramdisk/ph7/fuzzing_out"
if [ -d "$AFL_OUT" ]; then
    rm -rf $AFL_OUT
fi
