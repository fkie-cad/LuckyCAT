#!/bin/bash

COUNT=250

cd /tmp
rm -rf orcs*
/home/thomas/code/daemons/melkor/melkor -l 25 -A -n $COUNT -q /home/max/melkor/templates/foo
/home/thomas/code/daemons/melkor/melkor -l 25 -A -n $COUNT -q /home/thomas/code/daemons/melkor/templates/foo_dl_iterate_phdr
#/home/thomas/code/daemons/melkor/melkor -l 25 -A -n $COUNT -q /home/thomas/code/daemons/melkor/templates/foo_dlopen
/home/thomas/code/daemons/melkor/melkor -l 25 -A -n $COUNT -q /home/thomas/code/daemons/melkor/templates/foo_full_relro
/home/thomas/code/daemons/melkor/melkor -l 25 -A -n $COUNT -q /home/thomas/code/daemons/melkor/templates/foo_libfoo
/home/thomas/code/daemons/melkor/melkor -l 25 -A -n $COUNT -q /home/thomas/code/daemons/melkor/templates/foo_stackprotector_execstack
/home/thomas/code/daemons/melkor/melkor -l 25 -A -n $COUNT -q /home/thomas/code/daemons/melkor/templates/foo_static
tar -cvf orcs.tar orcs_*
tar -cvzf orcs.tar.gz orcs_*
