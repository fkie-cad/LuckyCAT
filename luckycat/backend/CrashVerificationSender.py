import base64
import json
import logging
import os
import time
from multiprocessing import Process

from mongoengine import connect

from luckycat import luckycat_global_config
from luckycat.backend import WorkQueue
from luckycat.database.models.Crash import Crash
from luckycat.database.models.Job import Job

logger = logging.getLogger(os.path.basename(__file__).split('.')[0])


class CrashVerificationSender(Process):

    def __init__(self):
        super(CrashVerificationSender, self).__init__()
        self.wq = WorkQueue.WorkQueue()
        self.ver_queue = 'verification'
        if not self.wq.queue_exists(self.ver_queue):
            self.wq.create_queue(self.ver_queue)

    @staticmethod
    def _get_job_from_crash(crash):
        res = Job.objects.get(id=crash.job_id)
        return res

    @staticmethod
    def _get_non_verified_crashes():
        res = Crash.objects(verified=False)
        return res

    def _send_crash_out(self, project, crash):
        try:
            buf = crash.test_case
            crash = {'data': base64.b64encode(buf).decode(),
                     'cmd_args': project.cmd_args,
                     'executable': base64.b64encode(project.fuzzing_target).decode(),
                     'crash_id': str(crash.id),
                     'verifier': project.verifier}
            self.wq.publish(self.ver_queue, json.dumps(crash))
        except Exception as e:
            logger.warning(f"Failed verification of {crash['crash_path']} with {str(e)}. Deleting crash!")
            crash.delete()

    def run(self):
        logger.info('Starting CrashVerification ...')
        connect(luckycat_global_config.db_name, host=luckycat_global_config.db_host)
        while 1:
            if not self.wq.queue_is_empty(self.ver_queue):
                logger.info('Verification queue not empty. Waiting...')
            else:
                crashes = self._get_non_verified_crashes()
                for crash in crashes:
                    current_project = self._get_job_from_crash(crash)
                    if current_project.verifier != 'no_verification':
                        self._send_crash_out(current_project, crash)

            time.sleep(luckycat_global_config.crash_verification_sender_sleeptime)
