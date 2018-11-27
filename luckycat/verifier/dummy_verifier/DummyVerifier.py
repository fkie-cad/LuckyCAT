import time
import os
import random
import zipfile
from luckycat.verifier.templates.PythonTemplateVerifier import PythonTemplateVerifier

path_to_data = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'data')

zip_ref = zipfile.ZipFile(os.path.join(path_to_data, 'data.zip'), 'r')
zip_ref.extractall(path_to_data)
zip_ref.close()

DEMO_CLASSIFICATIONS = [['8ea40395c2a8', 'Double Free', 'EXPLOITABLE'],
                        ['f34202b1d135', 'Use After Free', 'EXPLOITABLE'],
                        ['517feb05aaed', 'Heap Overflow', 'EXPLOITABLE'],
                        ['0df7e8ddc868', 'Near NULL Pointer', 'PROBABLY_NOT_EXPLOITABLE'],
                        ['2fbbb7865534', 'Abort Signal', 'UNKNOWN']]

ADDITIONAL = [open(os.path.join(path_to_data, 'core.txt.0')).read(),
              open(os.path.join(path_to_data, 'core.txt.1')).read()]


class DummyVerifier(PythonTemplateVerifier):

    def __init__(self):
        path_to_this_file = os.path.split(os.path.realpath(__file__))[0]
        super(DummyVerifier, self).__init__(config_path=os.path.join(
            path_to_this_file, '../templates/verifier.cfg'))

    def _verify_one_crash(self, crash_info):
        time.sleep(0.5)
        print('Verified!')
        current_classification = random.choice(DEMO_CLASSIFICATIONS)
        return {'verified': True,
                'crash_id': crash_info['crash_id'],
                'short_desc': current_classification[1],
                'crash_hash': current_classification[0],
                'classification': current_classification[2],
                'additional': random.choice(ADDITIONAL)}


def main():
    dummy = DummyVerifier()
    dummy.run()


if __name__ == '__main__':
    main()
