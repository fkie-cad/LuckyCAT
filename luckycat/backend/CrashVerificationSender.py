import base64
import json
import logging
import os
import time
from mongoengine import connect
from multiprocessing import Process
from luckycat import f3c_global_config
from luckycat.backend import WorkQueue
from luckycat.database.models.Crash import Crash
from luckycat.database.models.Job import Job

logger = logging.getLogger(os.path.basename(__file__).split(".")[0])


class CrashVerificationSender(Process):

    def __init__(self):
        super(CrashVerificationSender, self).__init__()
        self.wq = WorkQueue.WorkQueue()
        self.ver_queue = "verification"
        if not self.wq.queue_exists(self.ver_queue):
            self.wq.create_queue(self.ver_queue)

    def _get_job_from_crash(self, crash):
        res = Job.objects.get(id=crash.job_id)
        return res

    def _get_non_verified_crashes(self):
        res = Crash.objects(verified=False)
        return res

    def run(self):
        logger.info("Starting CrashVerification ...")
        connect(f3c_global_config.db_name, host=f3c_global_config.db_host)
        while 1:
            if not self.wq.queue_is_empty(self.ver_queue):
                logger.info('Verification queue not empty. Waiting...')
            else:
                crashes = self._get_non_verified_crashes()
                for crash in crashes:
                    # TODO determine verifier from project table
                    current_project = self._get_job_from_crash(crash)
                    try:
                        buf = crash.crash_data
                        crash = {'data': base64.b64encode(buf).decode(),
                                 'args': '',
                                 'program': '',
                                 'crash_id': str(crash.id),
                                 'remote': current_project.fuzzer == "cfuzz"}
                        self.wq.publish(self.ver_queue, json.dumps(crash))
                    except Exception as e:
                        logger.warn("Failed verification of %s with %s. Deleting crash!" % (crash['crash_path'], str(e)))
                        crash.delete()

            time.sleep(f3c_global_config.crash_verification_sender_sleeptime)
