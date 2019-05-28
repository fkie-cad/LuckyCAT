# Description

Lucky CAT can be used to collect and process crashes from Syzkaller.

# Installation

Syzkaller need to be installed as descibed on the github [page](https://github.com/google/syzkaller) of Syzkaller. It need to be configured and a fuzzing target need to be selected. Pip module paramiko need to installed to fetch files over scp from a remote syzkaller system. Use `install.sh` to install the paramiko module.

## Requirements

The crashes path of Syzkaller need to be setup in the config. A fuzzing job need be added with same name as the job name in the config.

If you want to collect crashes from a Syzkaller instance running on a remote system, you will need enable remote fetching by filling the empty variables remote_system_ip and remote_crashes_dir in `config.py`. For remote fetching your ssh key need to be added to authorized keys on the remote system. Generate an ssh key with an empty passphrase. For example, you can ssh-copy-id to copy your key to the remote system. If your Syzkaller fuzzer is running on the same system where Lucky Cat is running, let the both variables in config.py empty

# Running
Run `PYTHONPATH=. python3 luckycat/fuzzers/syzkaller/syzkaller-luckycat.py` from Lucky CAT's root directory to start the collection of crashes. Afterwards Syzkaller's fuzzing can be started.

# Limitations

Lucky Cat only collects crashes from Syzkaller's crash directory. The following meta information of crashes is missing:

* iteration
* total_execs
* cumulative_speed
* crash_signal

However, Lucky Cat requires this meta information. For that reason, some dummy values will be used. For example, all Syzkaller crashes will get the same crash signal of 0 in Lucky Cat.


