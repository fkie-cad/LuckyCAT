#!/bin/sh

cd /var/crash/
rm vmcore.*
tar -cvzf /tmp/last_crash.tar.gz *
rm -rf *
touch minfree
