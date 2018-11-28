# Installation

Use the `install.sh` to install afl and other dependencies. Afterwards use the script `prepare.sh` to prepare your machine for fuzzing with afl.

## Requirements

It is recommended to follow the detailed installing instructions for each of the requirements listed below

* [afl-fuzzer](http://lcamtuf.coredump.cx/afl/releases/)
* [exploitable](https://gitlab.com/rc0r/exploitable)
* [afl-utils](https://gitlab.com/rc0r/afl-utils)
* [tmux](https://github.com/tmux/tmux)

# Demo Time
To test or to showcase afl-luckycat you can use the script `demo_time.sh`. This script setups everything for a demo (installation, ram disk, compilation of demo program). Then run `PYTHONPATH=. python3 luckycat/fuzzers/aflfuzz/afl-luckycat.py` from Lucky CAT's root directory. You may check the status of indivdual fuzzers via tmux (`tmux attach-session -t luckycatAFL`).
