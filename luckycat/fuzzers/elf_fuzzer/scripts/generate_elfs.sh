#!/bin/sh

COUNT=10

cd /tmp
rm -rf orcs*
/home/max/melkor/melkor -A -n $COUNT -q /home/max/melkor/templates/foo
/home/max/melkor/melkor -A -n $COUNT -q /home/max/melkor/templates/foo_dl_iterate_phdr
#/home/max/melkor/melkor -A -n $COUNT -q /home/max/melkor/templates/foo_dlopen
/home/max/melkor/melkor -A -n $COUNT -q /home/max/melkor/templates/foo_full_relro
/home/max/melkor/melkor -A -n $COUNT -q /home/max/melkor/templates/foo_libfoo
/home/max/melkor/melkor -A -n $COUNT -q /home/max/melkor/templates/foo_stackprotector_execstack
/home/max/melkor/melkor -A -n $COUNT -q /home/max/melkor/templates/foo_static
tar -cvzf orcs.tar.gz orcs_*
sync
