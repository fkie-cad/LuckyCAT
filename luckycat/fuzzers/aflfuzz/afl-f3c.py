import logging
import time
import os
import base64
from time import gmtime, strftime
import signal
import sys
import subprocess
import sqlite3
import json
from luckycat.fuzzers.templates.python.PythonTemplateInternalMutationEngine import PythonFuzzer
import config


def clean_up():
    print('Killing all afl-fuzz instances...')
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        if 'afl-fuzz' in line:
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)


def check_afl_runs():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        if 'afl-fuzz' in line:
            return True
    return False


def signal_handler():
    clean_up()
    sys.exit(0)


class AflFuzzer(PythonFuzzer):
    def __init__(self):
        PythonFuzzer.__init__(self)
        self.CRASHES = []

    def full_path(self, dir_):
        # taken from http://code.activestate.com/recipes/577270-dealing-with-directory-paths-with/
        if dir_[0] == '~' and not os.path.exists(dir_):
            dir_ = os.path.expanduser(dir_)
        return os.path.abspath(dir_)

    def start_fuzzers(self):
        # TODO check output !!!!
        logging.info("Starting afl-fuzz with %i fuzzers" % config.fuzzers)
        for fuzzer_id in range(config.fuzzers):
            afl_cmd = self.build_afl_command(fuzzer_id)
            logging.debug("Starting: %s" % afl_cmd)
            subprocess.Popen(afl_cmd, shell=True)

    # TODO use screen
    def build_afl_command(self, fuzzer_id):
        if fuzzer_id == 0:
            return "afl-fuzz -i %s -o %s -M master -- %s > /dev/null" % (config.input_dir, config.output_dir,
                                                                         config.cmd)
        else:
            return "afl-fuzz -i %s -o %s -S slave%i -- %s > /dev/null " % (config.input_dir, config.output_dir,
                                                                           fuzzer_id, config.cmd)

    def build_afl_collect_command(self):
        crashes_db = os.path.join(config.crashes_dir, "crashes.db")
        cmd = "afl-collect -d %s -e gdb_script -r -rr %s %s -j %i -- %s" % (crashes_db, config.output_dir,
                                                                            config.crashes_dir, config.collect_threads,
                                                                            config.cmd)
        return cmd

    def whats_up(self):
        stats = {}
        cmd = "afl-whatsup %s" % config.output_dir
        output = subprocess.check_output(cmd, shell=True)
        for line in output.splitlines():
            if ":" in line:
                split_line = line.strip().split(":")
                self.parse_stats(split_line, stats)
        logging.debug(stats)
        stats['fuzzer'] = 'afl'
        return stats

    def parse_stats(self, split_line, stats):
        if "Total run time" in split_line[0]:
            tmp = split_line[1].strip().split(",")
            stats["runtime"] = str(int(tmp[0].strip().split(" ")[0]) * 24 + int(tmp[1].strip().split(" ")[0]))
        elif "Total execs" in split_line[0]:
            stats["total_execs"] = str(int(split_line[1].strip().split(" ")[0]) * 1000000)
        elif "Cumulative speed" in split_line[0]:
            stats["cumulative_speed"] = str(int(split_line[1].strip().split(" ")[0]))

    def collect(self):
        res = []
        afl_collect_cmd = self.build_afl_collect_command()
        logging.debug(afl_collect_cmd)
        subprocess.call(afl_collect_cmd, shell=True)
        crashes = os.listdir(self.full_path(config.crashes_dir))
        for crash in crashes:
            if ".db" not in crash and "gdb" not in crash:
                if crash not in self.CRASHES:
                    logging.debug("Found new crash %s" % crash)
                    self.CRASHES.append(crash)
                    res.append(os.path.join(self.full_path(config.crashes_dir), crash))
        return res

    def get_signal(self, filename):
        return int(filename.split("sig:")[1].split(",")[0]) + 128

    def _fuzz(self):
        self.start_fuzzers()
        logging.debug("Sleeping for %i seconds..." % config.sleep)
        time.sleep(config.sleep)
        stats = self.whats_up()
        new_crashes = self.collect()
        if len(new_crashes) > 0:
            for crash in new_crashes:
                with open(crash, "rb") as fp:
                    crash_info, filename = self.populate_crash_info_data(crash, fp)
                    crashes_db = self.full_path(os.path.join(config.crashes_dir, "crashes.db"))
                    if os.path.exists(crashes_db):
                        self.connect_to_crashDB(crash_info, crashes_db, filename)
                    self.send_crash_info(crash_info)
        self.send_stats_data(stats)

    def send_stats_data(self, stats):
        try:
            print(json.dumps(stats))
            self._send_stats(stats)
        except ConnectionError:
            raise

    def send_crash_info(self, crash_info):
        try:
            print(json.dumps(crash_info))
            self._send_crash(crash_info)
        except ConnectionError:
            raise

    def populate_crash_info_data(self, crash, fp):
        crash_data = base64.b64encode(fp.read())
        filename = os.path.split(crash)[-1]
        crash_info = {'fuzzer': 'afl',
                      'timestamp': strftime("%Y-%m-%d_%H:%M:%S", gmtime()),
                      'crash_data': crash_data,
                      'signal': self.get_signal(filename),
                      'verified': 1,
                      'filename': filename}
        return crash_info, filename

    def connect_to_crashDB(self, crash_info, crashes_db, filename):
        conn = sqlite3.connect(crashes_db)
        c = conn.cursor()
        cmd = 'SELECT * FROM Data'
        c.execute(cmd)
        for verified_crash in c:
            if str(verified_crash[0]) == filename:
                self.add_additional_info_to_crash(crash_info, verified_crash)
        conn.close()

    def add_additional_info_to_crash(self, crash_info, verified_crash):
        logging.debug("Adding additional info to crash")
        crash_info['classification'] = verified_crash[1]
        crash_info['description'] = verified_crash[2]
        crash_info['hash'] = verified_crash[3]


def main():
    if check_afl_runs():
        print("Seems that AFL session is already running.")
        print("I am going to kill them all, OK?")
        print("Press any key or abort with ctrl+c...")
        input()
        clean_up()
    signal.signal(signal.SIGINT, signal_handler)
    logging.basicConfig(level=config.log_level)
    afl_fuzzer = AflFuzzer()
    afl_fuzzer.start()
    afl_fuzzer.join()


if __name__ == '__main__':
    main()
