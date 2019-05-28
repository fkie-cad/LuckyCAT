import base64
import logging
import os
import time
from time import gmtime, strftime

import config

from luckycat.fuzzers.templates.python.PythonTemplateInternalMutationEngine import PythonFuzzer
from luckycat.fuzzers.syzkaller.RemoteCrashFetcher import RemoteCrashFetcher

def full_path(dir_):
    # taken from http://code.activestate.com/recipes/577270-dealing-with-directory-paths-with/
    if dir_[0] == '~' and not os.path.exists(dir_):
        dir_ = os.path.expanduser(dir_)
    return os.path.abspath(dir_)

class SyzkallerFuzzer(PythonFuzzer):
    def __init__(self):
        PythonFuzzer.__init__(self)
        self.CRASHES = []
        self.Start_Time = time.time()
        self.Last_Crash_Timestamp = self.Start_Time

    def get_dir_path_of_filepath(self, filepath):
        return '/'.join(filepath.split('/')[:-1])

    def collect(self):
        # does not collect new crashes after 100 occurences, because syzkaller counts only up to 100 crash logs/reports per crash hash dir and then starts from log0 again.
        results = []
        crash_dirs = os.listdir(config.crashes_dir)
        tmp_Last_Crash_Timestamp = self.Last_Crash_Timestamp

        for crash_dir in crash_dirs:
            crash_dir_path = os.path.join(config.crashes_dir, crash_dir)
            files = os.listdir(crash_dir_path)
            crashes = [file for file in files if file.startswith('log')]
            for crash in crashes:
                crash_path = os.path.join(crash_dir_path, crash)
                if crash_path not in self.CRASHES:
                    crash_time = os.stat(crash_path).st_mtime
                    if not crash_time > self.Last_Crash_Timestamp:
                        continue
                    if crash_time > tmp_Last_Crash_Timestamp:
                        tmp_Last_Crash_Timestamp = crash_time
                    self.CRASHES.append(crash_path)
                    logging.debug('Found new crash {}'.format(crash_path))
                    results.append(crash_path)
        self.Last_Crash_Timestamp = tmp_Last_Crash_Timestamp
        return results

    def populate_crash_info_data(self, crash_path):
        crash_description_path = os.path.join(self.get_dir_path_of_filepath(crash_path), 'description')
        with open(crash_description_path, 'r') as fd:
            #not used by syzkaller at the moment
            crash_description = fd.read()
            logging.debug('Crash Description: {}'.format(crash_description))
        with open(crash_path, 'r') as fd:
            crash_string = fd.read()
        test_case = crash_string
        filename = crash_path
        crash_info = {'job_name': config.job_name,
                      'fuzzer': 'syzkaller',
                      'timestamp': strftime('%Y-%m-%d_%H:%M:%S', gmtime()),
                      'test_case': test_case,
                      'signal': 0,
                      'verified': 1,
                      'filename': filename}
        return crash_info

    def crash_time_is_new(self, crash_path):
        crash_time = os.stat(crash_path).st_mtime
        if crash_time > self.Last_Crash_Timestamp:
            return True

    def _fuzz(self):
        new_crashes = self.collect()
        if len(new_crashes) > 0:
            for crash in new_crashes:
                crash_info = self.populate_crash_info_data(crash)
                self.send_crash_info(crash_info)
        self.send_stats_data()
        logging.debug('Sleeping for {} seconds...'.format(config.sleep))
        time.sleep(config.sleep)

    def send_stats_data(self):
        stats = {'fuzzer': 'syzkaller',
                 'job_name': config.job_name,
                 'runtime': time.time() - self.Start_Time,
                 'total_execs': 0,
                 'cumulative_speed': 0}
        try:
            logging.info('Sending stats info...')
            self._send_stats(stats)
        except ConnectionError:
            raise

    def send_crash_info(self, crash_info):
        try:
            logging.info('Sending crash info...')
            self._send_crash(crash_info)
        except ConnectionError:
            raise

def main():
    syzkaller_fuzzer = SyzkallerFuzzer()
    if config.remote_system_ip and config.remote_crashes_dir:
        RemoteCrashFetcher().start()
    while True:
        syzkaller_fuzzer.run()

if __name__ == '__main__':
    main()