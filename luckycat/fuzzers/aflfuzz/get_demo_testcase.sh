#!/bin/bash
git clone https://github.com/symisc/PH7.git /tmp/ph7
cd /tmp/ph7 || exit
cp examples/ph7_interp.c .
rsync -av /tmp/ph7 /tmp/afl-ramdisk/

mkdir -p /tmp/afl-ramdisk/ph7/fuzzing_in
mkdir -p /tmp/afl-ramdisk/ph7/crashes
cd /tmp/afl-ramdisk/ph7/ || exit
# using ASAN segfaults directly...
# AFL_USE_ASAN=1 afl-clang -m32 -W -Wall -D PH7_ENABLE_MATH_FUNC -o ph7 ph7_interp.c ph7.c -lm
afl-clang -W -Wall -D PH7_ENABLE_MATH_FUNC -o ph7 ph7_interp.c ph7.c -lm
cd /tmp/afl-ramdisk/ph7/fuzzing_in || exit
wget https://raw.githubusercontent.com/panique/php-login-one-file/master/index.php

AFL_OUT="/tmp/afl-ramdisk/ph7/fuzzing_out"
if [ -d "$AFL_OUT" ]; then
  rm -rf $AFL_OUT
fi
