import os
import logging

# Lucky CAT configs
host = "127.0.0.1"
port = 11300
sample_queue = "test-samples"
crash_queue = "crashes"
stats_queue = "stats"
sleep = 120
log_level = logging.DEBUG

# afl configs
base_path = "~/afl-ramdisk"
cmd = os.path.join(base_path, "some_path/program_name") + " @@"
fuzzers = 4
collect_threads = 4
input_dir = os.path.join(base_path, "fuzzing_in")
output_dir = os.path.join(base_path, "fuzzing_out")
crashes_dir = os.path.join(base_path, "crashes")
