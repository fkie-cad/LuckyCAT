# ELF Fuzzer

ELF Fuzzer is a wrapper of [Melkor_ELF_Fuzzer](https://github.com/IOActive/Melkor_ELF_Fuzzer). We utilized it in order to fuzz the syscall sys_execve of BSD-based systems. Therefore, we added support for FreeBSD, OpenBSD, and NetBSD to Melkor_ELF_Fuzzer (currently an [open pull request](https://github.com/IOActive/Melkor_ELF_Fuzzer/pull/2)). We found with it the following bugs:

- [OpenBSD 6.3 errata 012](https://ftp.openbsd.org/pub/OpenBSD/patches/6.3/common/012_execsize.patch.sig) / [OpenBSD 6.2 errata 018](https://ftp.openbsd.org/pub/OpenBSD/patches/6.2/common/018_execsize.patch.sig): OpenBSD x64 kernel
- ???: ??? x64 kernel

Note that there are many operating systems other than Linux and BSD-based ones that utilize the ELF format. We believe that there are still many lurking in the ELF header parser of the kernels that can be easily found with this fuzzer. There are many code paths to be explored: think of 32/64 bit ELFs or compatibility modes.

## Using ELF Fuzzer

In this walk through, we fuzz [OpenBSD 6.3 x64](https://cdn.openbsd.org/pub/OpenBSD/6.3/amd64/install63.iso)(unpatched!). Within a couple of minutes, you should witness OpenBSD 6.3 errata 012.

### Preparing the Target

Install a QEMU VM with OpenBSD 6.3 x64. Afterwards, create a script to start the VM. A simple start.sh script as the following should work:
``` bash
#!/bin/bash
qemu-system-x86_64 -enable-kvm -hda openbsd.img -boot c -m 512 -net nic -net user,hostfwd=tcp::10042-:22
```
Enable SSH key login for your user and root and upload your key to the VM. Test it! Furthermore, you need a reset.sh script:
``` bash
#!/bin/bash
rm openbsd.img
cp openbsd.img.backup openbsd.img
sync
```
On the target, check out the code of [Melkor_ELF_Fuzzer](https://github.com/IOActive/Melkor_ELF_Fuzzer) (for the time being use our pull request) and compile it.
### Creating a Job in Lucky CAT

### Configuring and Starting ELF Fuzzer

## Future Work

- use QEMU snapshots
- refactor the whole fuzzer, at the moment it is just a proof of concept
