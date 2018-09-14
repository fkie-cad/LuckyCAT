import time
import os
import random
from luckycat.verifier.templates.PythonTemplateVerifier import PythonTemplateVerifier


class DummyVerifier(PythonTemplateVerifier):

    def __init__(self):
        path_to_this_file = os.path.split(os.path.realpath(__file__))[0]
        super(DummyVerifier, self).__init__(config_path=os.path.join(
            path_to_this_file, '../templates/verifier.cfg'))

    def _verify_one_crash(self, crash_info):
        time.sleep(0.5)
        print('Verified!')
        return {'verified': True,
                'crash_id': crash_info['crash_id'],
                'short_desc': 'evil crash',
                'crash_hash': str(random.randint(0, 20000)),
                'classification': 'EXPLOITABLE'}


def main():
    dummy = DummyVerifier()
    dummy.run()


if __name__ == '__main__':
    main()
