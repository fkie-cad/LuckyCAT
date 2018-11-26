import logging
import time
import os
import base64
from time import gmtime, strftime
import signal
import sys
import subprocess
import sqlite3
from luckycat.fuzzers.templates.python.PythonTemplateInternalMutationEngine import PythonFuzzer
import shutil
import config


def clean_up():
    print('Killing all afl-fuzz instances...')
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        if b'afl-fuzz' in line:
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)
    try:
        subprocess.Popen('tmux kill-session -t luckycatAFL', shell=True, stdout=subprocess.PIPE)
    except ChildProcessError:
        pass


def check_if_afl_output_dir_is_empty():
    afl_outout_dir = full_path(config.output_dir)
    if os.path.exists(afl_outout_dir) and os.path.isdir(afl_outout_dir):
        print('Fuzzing output directory seems to be not empty.\nDelete contents? [y/N]')
        user_input = input()
        if str.lower(user_input) == 'y':
            filelist = [f for f in os.listdir(afl_outout_dir)]
            for f in filelist:
                shutil.rmtree(os.path.join(afl_outout_dir, f))
        else:
            print('Aborting...')
            sys.exit(1)


def check_afl_runs():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        if b'afl-fuzz' in line:
            return True
    return False


def signal_handler(sig, frame):
    clean_up()
    sys.exit(0)


def full_path(dir_):
    # taken from http://code.activestate.com/recipes/577270-dealing-with-directory-paths-with/
    if dir_[0] == '~' and not os.path.exists(dir_):
        dir_ = os.path.expanduser(dir_)
    return os.path.abspath(dir_)


def build_tmux_session():
    subprocess.Popen('tmux new -d -s luckycatAFL', shell=True, start_new_session=True, stdout=subprocess.DEVNULL)


class AflFuzzer(PythonFuzzer):
    def __init__(self):
        PythonFuzzer.__init__(self)
        self.CRASHES = []

    @staticmethod
    def build_afl_command(fuzzer_id):
        if fuzzer_id == 0:
            return 'afl-fuzz -m {} -i {} -o {} -M master -- {}'.format(config.memory_limit,
                                                                       config.input_dir,
                                                                       config.output_dir,
                                                                       config.cmd)
        else:
            return 'afl-fuzz -m {} -i {} -o {} -S slave{} -- {}'.format(config.memory_limit,
                                                                        config.input_dir,
                                                                        config.output_dir,
                                                                        fuzzer_id,
                                                                        config.cmd)

    @staticmethod
    def build_new_tmux_window():
        subprocess.call('tmux new-window -t luckycatAFL', shell=True)

    def start_fuzzers(self):
        logging.debug('Starting afl-fuzz with {} processes'.format(config.fuzzers))
        for fuzzer_id in range(config.fuzzers):
            self.build_new_tmux_window()
            afl_cmd = self.build_afl_command(fuzzer_id)
            fuzz_task = subprocess.Popen('tmux send-keys -t luckycatAFL "{}" C-m'.format(afl_cmd), shell=True,
                                         stdout=subprocess.PIPE)
            if fuzz_task.poll() is not None:
                logging.debug('Failed to spawn at least one subprocess. Aborting!')
                sys.exit(1)
        logging.debug('Success!')

    @staticmethod
    def build_afl_collect_command():
        # afl-collect/exploitable discards "Non Exploitable"-crashes right away, are not collected!!
        crashes_db = os.path.join(config.crashes_dir, 'crashes.db')
        cmd = 'afl-collect -d {} -e gdb_script -r -rr {} {} -j {} -- {}'.format(crashes_db, config.output_dir,
                                                                                config.crashes_dir,
                                                                                config.collect_threads, config.cmd)
        return cmd

    def whats_up(self):
        stats = {}
        cmd = 'afl-whatsup {}'.format(config.output_dir)
        output = subprocess.check_output(cmd, shell=True)
        for line in output.splitlines():
            if b':' in line:
                split_line = line.strip().split(b':')
                self.parse_stats(split_line, stats)
        stats['fuzzer'] = 'afl'
        stats['job_name'] = config.job_name
        return stats

    @staticmethod
    def parse_stats(split_line, stats):
        if b'Total run time' in split_line[0]:
            tmp = split_line[1].strip().split(b',')
            stats['runtime'] = str(int(tmp[0].strip().split(b' ')[0]) * 24 + int(tmp[1].strip().split(b' ')[0]))
        elif b'Total execs' in split_line[0]:
            stats['total_execs'] = str(int(split_line[1].strip().split(b' ')[0]) * 1000000)
        elif b'Cumulative speed' in split_line[0]:
            stats['cumulative_speed'] = str(int(split_line[1].strip().split(b' ')[0]))

    def collect(self):
        res = []
        afl_collect_cmd = self.build_afl_collect_command()
        logging.debug(afl_collect_cmd)
        subprocess.call(afl_collect_cmd, shell=True)
        crashes = os.listdir(full_path(config.crashes_dir))
        for crash in crashes:
            if '.db' not in crash and 'gdb' not in crash:
                if crash not in self.CRASHES:
                    logging.debug('Found new crash {}'.format(crash))
                    self.CRASHES.append(crash)
                    res.append(os.path.join(full_path(config.crashes_dir), crash))
        return res

    @staticmethod
    def get_signal(filename):
        return int(filename.split('sig:')[1].split(',')[0]) + 128

    def _fuzz(self):
        logging.debug('Sleeping for {} seconds...'.format(config.sleep))
        time.sleep(config.sleep)
        stats = self.whats_up()
        new_crashes = self.collect()
        if len(new_crashes) > 0:
            for crash in new_crashes:
                with open(crash, 'rb') as fp:
                    crash_info, filename = self.populate_crash_info_data(crash, fp)
                    crashes_db = full_path(os.path.join(config.crashes_dir, 'crashes.db'))
                    if os.path.exists(crashes_db):
                        self.connect_to_crash_db(crash_info, crashes_db, filename)
                    self.send_crash_info(crash_info)
        self.send_stats_data(stats)

    def send_stats_data(self, stats):
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

    def populate_crash_info_data(self, crash, fp):
        test_case = base64.b64encode(fp.read()).decode()
        filename = os.path.split(crash)[-1]
        crash_info = {'job_name': config.job_name,
                      'fuzzer': 'afl',
                      'timestamp': strftime('%Y-%m-%d_%H:%M:%S', gmtime()),
                      'test_case': test_case,
                      'signal': self.get_signal(filename),
                      'verified': 1,
                      'filename': filename}
        return crash_info, filename

    def connect_to_crash_db(self, crash_info, crashes_db, filename):
        conn = sqlite3.connect(crashes_db)
        c = conn.cursor()
        cmd = 'SELECT * FROM Data'
        c.execute(cmd)
        for verified_crash in c:
            if str(verified_crash[0]) == filename:
                self.add_additional_info_to_crash(crash_info, verified_crash)
        conn.close()

    @staticmethod
    def add_additional_info_to_crash(crash_info, verified_crash):
        logging.debug('Adding additional info to crash')
        crash_info['classification'] = verified_crash[1]
        crash_info['description'] = verified_crash[2]
        crash_info['hash'] = verified_crash[3]


def main():
    if check_afl_runs():
        print('Seems that AFL session is already running.')
        print('I am going to kill them all, OK?')
        print('Press any key or abort with CTRL+c...')
        input()
        clean_up()
    signal.signal(signal.SIGINT, signal_handler)
    logging.basicConfig(level=config.log_level)
    check_if_afl_output_dir_is_empty()
    afl_fuzzer = AflFuzzer()
    logging.debug('\x1b[6;30;42m' +
                  'Attach to tmux session via "{}"!'.format('tmux attach-session -t luckycatAFL') +
                  '\x1b[0m')
    build_tmux_session()
    afl_fuzzer.start_fuzzers()
    while True:
        afl_fuzzer.run()


if __name__ == '__main__':
    main()
