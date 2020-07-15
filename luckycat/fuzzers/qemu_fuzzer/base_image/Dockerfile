# This is an image for file-based fuzzing of firmware.
# It installs a patched AFL version (afl-other) for
# ARM, MIPS, PPC and x86. Afterwards, it adds the
# test cases and the whole (unpacked) root directory of
# the firmware to the container. Both are required to
# be specified via Docker's command line option "--build-arg="
FROM phusion/baseimage:0.11
MAINTAINER Christopher Krah <christopher.krah@fkie.fraunhofer.de>

# Configure proxy if needed
#ENV http_proxy <http_proxy>
#ENV https_proxy <https_proxy>

RUN apt-get update -y && apt-get install -y gcc cmake make libtool-bin wget \
python automake bison libglib2.0 git libssl-dev nettle-dev flex python3 \
build-essential python3-setuptools python3-dev screen gdb

WORKDIR /opt
RUN git clone https://github.com/shellphish/afl-other-arch.git

# build AFL with support binary instrumentation support via QEMU
# arch can be of the following:
# aarch64 alpha arm armeb cris i386 m68k microblaze microblazeel 
# mips mips64 mips64el mipsel mipsn32 mipsn32el or32 ppc ppc64 
# ppc64abi32 ppc64le s390x sh4 sh4eb sparc sparc32plus sparc64 unicore32 x86_64
# please refer to https://github.com/shellphish/afl-other-arch
ARG arch
WORKDIR /opt/afl-other-arch
RUN ./build.sh ${arch}

# building afl-utils
WORKDIR /opt
RUN git clone https://github.com/rc0r/afl-utils
WORKDIR /opt/afl-utils
RUN python3 setup.py install;\
echo "source /usr/lib/python3.5/site-packages/exploitable-1.32_rcor-py3.5.egg/exploitable/exploitable.py" >> ~/.gdbinit

# specifiy the path to the unpacked firmware
WORKDIR /fuzzing
COPY start_afl.sh /fuzzing/start_afl.sh

# setting up environment
ENV PATH="/opt/afl-other-arch:/opt/afl-utils/:${PATH}"
ENV AFL_PATH="/opt/afl-other-arch/tracers/${arch}"
ENV QEMU_LD_PREFIX="/fuzz_ramdisk/firmware_root/"

ENTRYPOINT ["/fuzzing/start_afl.sh"]

