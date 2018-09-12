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
        if crash_data['crash']:

            crash_path = os.path.join(f3c_global_config.samples_path, "crashes")
            # FIXME: do not rely on data from client, santanize!
            temp_file = crash_data['filename']
            if not os.path.exists(temp_file):
                logger.error("Test case file %s does not exists!" % temp_file)
                return False

            buf = open(temp_file, "rb").read()
            file_hash = hashlib.sha1(buf).hexdigest()
            new_path = os.path.join(crash_path, file_hash)

            logger.info("Saving test file %s" % new_path)
            shutil.move(temp_file, new_path)

            logger.debug("Inserting crash: %s." % str(crash_data))
            cfuzz_crash = Crash(job_id=crash_data['job_id'],
                                crash_signal=crash_data['signal'],
                                crash_path=new_path,
                                date=datetime.datetime.now(),
                                verified=False)
            cfuzz_crash.save()
            logger.warn('Crash stored')
        else:
            logger.warn('No crash clean up')

        try:
            os.remove(crash_data['filename'])
        except OSError as e:
            print ("Error: %s - %s." % (e.filename, e.strerror))

        stats = {'fuzzer': 'cfuzz',
                 'job_id': crash_data['job_id'],
                 'runtime': 0,
                 'total_execs': "+1"}
        self.wq.publish("stats", json.dumps(stats))

    def _insert_crash_afl(self, crash_data):
        logger.info("Inserting AFL crash: %s" % crash_data['filename'])
        crash_path = os.path.join(f3c_global_config.samples_path, "crashes")
        new_path = os.path.join(crash_path, crash_data['filename'])
        with open(new_path, 'wb') as fp:
            fp.write(base64.b64decode(crash_data['crash_data']))

        logger.debug("Inserting AFL crash with signal %i." % crash_data['signal'])
        if 'classification' in crash_data:
            # TODO ensure that verified is a boolean
            afl_crash = Crash(job_id=crash_data['job_id'],
                              crash_signal=crash_data['signal'],
                              crash_path=new_path,
                              verified=crash_data['verified'],
                              date=datetime.datetime.now(),
                              crash_hash=crash_data['hash'],
                              exploitability=crash_data['classification'],
                              additional=crash_data['description'])
        else:
            afl_crash = Crash(job_id=crash_data['job_id'],
                              crash_signal=crash_data['signal'],
                              crash_path=new_path,
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
