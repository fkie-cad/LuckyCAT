import random
import time
import os
import argparse
import luckycat.fuzzers.dummy_fuzzer.dummy_fuzzer_config
from luckycat.fuzzers.templates.python.PythonTemplateExternalMutationEngine import PythonFuzzer


class DummyFuzzer(PythonFuzzer):

    def __init__(self, demo):
        path_to_this_file = os.path.split(os.path.realpath(__file__))[0]
        super(DummyFuzzer, self).__init__(config_path=os.path.join(
            path_to_this_file, '../templates/python/fuzzer.cfg'))

        self.demo = demo
        self.crashes = 0
        self.iterations = 0

        if self.demo:
            self.probability = luckycat.fuzzers.dummy_fuzzer.dummy_fuzzer_config.demo_probability
            self.sleep_time = luckycat.fuzzers.dummy_fuzzer.dummy_fuzzer_config.demo_sleep_time
        else:
            self.probability = luckycat.fuzzers.dummy_fuzzer.dummy_fuzzer_config.probability
            self.sleep_time = luckycat.fuzzers.dummy_fuzzer.dummy_fuzzer_config.sleep_time

    def _fuzz_one_test_case(self, test_case_info):
        time.sleep(self.sleep_time)
        self.iterations += 1
        print('Iterations: %d, Crashes: %d' % (self.iterations, self.crashes), end='\r', flush=True)

        if random.randint(1, self.probability) == 1:
            self.crashes += 1
            return {'crash': True,
                    'fuzzer': 'cfuzz',
                    'filename': test_case_info['filename'],
                    'signal': '139',
                    'job_name': self.config['DEFAULT']['job_name']}
        else:
            return {'crash': False,
                    'fuzzer': 'cfuzz',
                    'filename': test_case_info['filename'],
                    'job_name': self.config['DEFAULT']['job_name']}


def parse_args():
    parser = argparse.ArgumentParser(description='Manage fuzzing jobs from the command line')
    parser.add_argument('--demo', action='store_true', default=False,
                        help='Run in demo mode.')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    dummy = DummyFuzzer(args.demo)
    dummy.start()
    dummy.join()


if __name__ == '__main__':
    main()
