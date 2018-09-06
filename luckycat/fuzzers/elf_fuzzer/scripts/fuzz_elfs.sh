#!/bin/sh

#rm *.core

/home/max/melkor/test_fuzzed.sh /tmp/orcs_foo/
/home/max/melkor/test_fuzzed.sh /tmp/orcs_foo_dl_iterate_phdr/
/home/max/melkor/test_fuzzed.sh /tmp/orcs_foo_dlopen/ 
/home/max/melkor/test_fuzzed.sh /tmp/orcs_foo_full_relro/ 
/home/max/melkor/test_fuzzed.sh /tmp/orcs_foo_libfoo/ 
#/usr/home/max/melkor/test_fuzzed.sh /tmp/orcs_foo_stackprotector_execstack/ 
/home/max/melkor/test_fuzzed.sh /tmp/orcs_foo_static/ 
