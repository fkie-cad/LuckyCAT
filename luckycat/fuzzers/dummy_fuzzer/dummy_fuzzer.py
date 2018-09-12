import random
import time
import os
from luckycat.fuzzers.templates.python.PythonTemplateExternalMutationEngine import PythonFuzzer


class DummyFuzzer(PythonFuzzer):

    def __init__(self):
        path_to_this_file = os.path.split(os.path.realpath(__file__))[0]
        super(DummyFuzzer, self).__init__(config_path=os.path.join(
            path_to_this_file, '../templates/python/fuzzer.cfg'))

    def _fuzz_one_test_case(self, test_case_info):
        time.sleep(0.25)
        if random.randint(1, 10) == 1:
            print("CRASH!")
            return {'crash': True,
                    'fuzzer': 'cfuzz',
                    'filename': test_case_info['filename'],
                    'signal': '139',
                    'job_id': test_case_info['job_id']}
        else:
            print("Nothing...")
            return {'crash': False,
                    'fuzzer': 'cfuzz',
                    'filename': test_case_info['filename'],
                    'job_id': test_case_info['job_id']}


def main():
    dummy = DummyFuzzer()
    dummy.start()
    dummy.join()


if __name__ == '__main__':
    main()
