import base64
import datetime
import hashlib
import json
import logging
import os
import shutil
from multiprocessing import Process
from mongoengine import connect
from luckycat.database.models.Crash import Crash
from luckycat.database.models.Job import Job
from luckycat.backend import WorkQueue
from luckycat import f3c_global_config

logger = logging.getLogger(os.path.basename(__file__).split(".")[0])


class CrashReceiver(Process):
    def __init__(self):
        super(CrashReceiver, self).__init__()
        self.wq = WorkQueue.WorkQueue()
        self.queue_name = "crashes"
        if not self.wq.queue_exists(self.queue_name):
            self.wq.create_queue(self.queue_name)
        self.channel = self.wq.get_channel()

    def _insert_crash_cfuzz(self, crash_data):
        # FIXME validate user provided data
        job = Job.objects.get(name=crash_data['job_name'])
        if crash_data['crash']:
            with open(crash_data['filename'], 'rb') as f:
                data = f.read()
            logger.debug("Inserting crash: %s." % str(crash_data))
            cfuzz_crash = Crash(job_id=job.id,
                                crash_signal=crash_data['signal'],
                                crash_data=data,
                                date=datetime.datetime.now(),
                                verified=False)
            cfuzz_crash.save()
            logger.debug('Crash stored')
        else:
            logger.debug('No crash clean up')

        try:
            os.remove(crash_data['filename'])
        except OSError as e:
            print ("Error: %s - %s." % (e.filename, e.strerror))

        stats = {'fuzzer': 'cfuzz',
                 'job_id': str(job.id),
                 'runtime': 0,
                 'total_execs': "+1"}
        self.wq.publish("stats", json.dumps(stats))

    def _insert_crash_afl(self, crash_data):
        logger.debug("Inserting AFL crash with signal %i." % crash_data['signal'])
        job = Job.objects.get(name=crash_data['job_name'])
        with open(crash_data['filename'], 'rb') as f:
            data = f.read()
        if 'classification' in crash_data:
            afl_crash = Crash(job_id=job.id,
                              crash_signal=crash_data['signal'],
                              crash_data=data,
                              verified=crash_data['verified'],
                              date=datetime.datetime.now(),
                              crash_hash=crash_data['hash'],
                              exploitability=crash_data['classification'],
                              additional=crash_data['description'])
        else:
            afl_crash = Crash(job_id=crash_data['job_name'],
                              crash_signal=crash_data['signal'],
                              crash_data=data,
                              date=datetime.datetime.now(),
                              verified=crash_data['verified'])

        afl_crash.save()
        logger.debug("Crash stored")

    def on_message(self, channel, method_frame, header_frame, body):
        crash_info = json.loads(body.decode("utf-8"))
        if crash_info['fuzzer'] == "afl":
            self._insert_crash_afl(crash_info)
        elif crash_info['fuzzer'] == "cfuzz":
            self._insert_crash_cfuzz(crash_info)
        else:
            logger.error("Unknown fuzzer %s" % crash_info['fuzzer'])

    def run(self):
        logger.info("Starting CrashReceiver...")
        connect(f3c_global_config.db_name, host=f3c_global_config.db_host)
        self.channel.basic_consume(self.on_message, self.queue_name)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.connection.close()
