import logging

job_name = 'syz'
crashes_dir = '/home/workdir/crashes'
sleep = 60
log_level = logging.DEBUG

# remote syzkaller system, let the values empty if you don't want to use a remote syzkaller
remote_system_ip = ''
remote_crashes_dir = ''

# example
# crashes_dir = '/home/workdir/crashes'
# remote_system_ip = '11.11.11.11'
# remote_crashes_dir = '/remote/home/workdir/crashes'
