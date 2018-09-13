# Lucky CAT - Crash All the Things!
[![BCH compliance](https://bettercodehub.com/edge/badge/fkie-cad/LuckyCAT?branch=master)](https://bettercodehub.com/)

## What is Lucky CAT?
Lucky CAT (**C**rash **A**ll the **T**hings!) is a distributed fuzzing testing suite with an easy to use web interface. It allows to manage several fuzzing jobs on several remote machines concurrently. Lucky CAT aims to be easily usable, scaleable, extensible, and fun.

Lucky CAT's origin is Joxean Koret's [Nightmare Fuzzing Project](https://github.com/joxeankoret/nightmare). However, there may be only traces of Nightmare and Lucky CAT is more 2018-ish by relaying, amongst others, on [Bootstrap](https://github.com/twbs/bootstrap), [Docker](https://www.docker.com), [MongoDB](https://www.mongodb.com), [Python 3](https://www.python.org/), and [RabbitMQ](https://github.com/rabbitmq).

## Why use Lucky CAT?
Lucky CAT offers the following features:
- **Fuzz job management**: primary focus on black box fuzzing and embedded devices
- **Easy deployment**: thanks to Docker and Docker Compose
- **Scalability**: Lucky CAT uses a micro service architecture backed by RabbitMQ
- **Easy integration**: Lucky CAT provides a RESTful API to integrate it with your other tools
- **Responsive WebUI**: for job management, crash analysis, and statistics 
- **Fast command line client**: for those who never leave the terminal...
- **Fuzzers included**:  tiny POSIX-compatible fuzzer `cfuzz`, `afl`, `afl-otherarch` wrappers and many more
- **Easy fuzzer integration**: integrate other fuzzer into Lucky CAT by using either a [Python template](luckycat/fuzzers/templates/python/) or a [C template](luckycat/fuzzers/templates/c/) 
- **Crash verification**: local and remote crash verification with the gdb plugin [exploitable](https://github.com/jfoote/exploitable)

And because we use it to find bugs:

- [CVE-2018-3005](https://cve.mitre.org/cgi-bin/cvename.cgi?name=2018-3005): Oracle VirtualBox (found with trap_fuzzer)
- [CVE-2018-6924](https://cve.mitre.org/cgi-bin/cvename.cgi?name=2018-6924) / [FreeBSD-SA-18:12.elf](https://www.freebsd.org/security/advisories/FreeBSD-SA-18:12.elf.asc): FreeBSD x64 kernel (found with elf_fuzzer)
- [CVE-2018-14775](https://cve.mitre.org/cgi-bin/cvename.cgi?name=2018-14775) / [OpenBSD 6.3 errata 015](https://ftp.openbsd.org/pub/OpenBSD/patches/6.3/common/015_ioport.patch.sig) / [OpenBSD 6.2 errata 020](https://ftp.openbsd.org/pub/OpenBSD/patches/6.2/common/020_ioport.patch.sig): OpenBSD i386 kernel (found with trap_fuzzer)
- [OpenBSD 6.3 errata 012](https://ftp.openbsd.org/pub/OpenBSD/patches/6.3/common/012_execsize.patch.sig) / [OpenBSD 6.2 errata 018](https://ftp.openbsd.org/pub/OpenBSD/patches/6.2/common/018_execsize.patch.sig): OpenBSD x64 kernel (found with elf_fuzzer)


## How to install Lucky CAT?

### Requirements
You need a recent Linux distribution like Ubuntu 18.04 and at least [Docker](https://www.docker.com) 18.06.0 as well as [docker-compose](https://github.com/docker/compose) 1.22.0 to build Lucky CAT. Even though you may not need to worry about the installation of further requirements thanks to [Docker](https://github.com/docker), Lucky CAT relies on many amazing open source projects (see [PROPS.md](PROPS.md)).

### Installation Process
Pull the whole project:
``` bash
git clone https://github.com/fkie-cad/luckycat.git
```
Just use docker-compose to build the app.
``` bash
docker-compose build && docker-compose up
```
or just use the script `start_cluster.sh`. Afterwards navigate to https://localhost:5000 and create a new user.

In case you wish to remove Lucky CAT, you may use the script `docker/clean_docker.sh`. Please note that this script deletes all Docker images and containers on your system as well as your Lucky CAT data.
## How to use Lucky CAT?
The workflow of Lucky CAT is as follows:
- Create a new job either via the web interface or the REST API.
- Deploy a fuzzer. Either you choose one of the prebuild fuzzers or your own (based on the the templates, see next section). Ensure a proper configuration (e.g. queue names).
- Deploy (if possible) a verifier for crash verification (probably on the real device if you fuzzing some IoT thingy).
- Start fuzzing and check on the results and stats in the web interface.

If you wish to integrate or automate Lucky CAT then you may want to have a look at [its RESTful API](doc/rest_api.md).

## How to extend Lucky CAT with a new fuzzer or verifier?
While there are several ways to extend the code, the easiest way is to integrate another fuzzer or verifier.

There are two example fuzzers in `luckycat/fuzzers/templates`. One of them is written in C and one in Python. Use them as basis and extend them in order to add another fuzzer to Lucky CAT.
Similarly, you can extend Lucky CAT by building upon `luckycat/verifier/templates`.

### Contribute

Contributions are always welcomed. Just fork it and open a pull request!

## Acknowledgements

This project is partly financed by [German Federal Office for Information Security (BSI)](https://www.bsi.bund.de).

## License

``` 
    Copyright (C) 2018 -      Fraunhofer FKIE  (thomas.barabosch@fkie.fraunhofer.de)
    Copyright (C) 2013 - 2015 Joxean Koret     (admin@joxeankoret.com)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
    Some plug-ins may have different licenses. If so, a license file is provided in the plug-in's folder.
```
