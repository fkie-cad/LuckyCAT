import json
import logging
import os
from multiprocessing import Process
from mongoengine import connect
from luckycat import f3c_global_config
from luckycat.backend import WorkQueue
from luckycat.database.models.Crash import Crash

logger = logging.getLogger(os.path.basename(__file__).split(".")[0])


class CrashVerificationCollector(Process):

    def __init__(self):
        super(CrashVerificationCollector, self).__init__()
        self.wq = WorkQueue.WorkQueue()
        self.queue_name = "verified"
        if not self.wq.queue_exists(self.queue_name):
            self.wq.create_queue(self.queue_name)
        self.channel = self.wq.get_channel()

    def on_message(self, channel, method_frame, header_frame, body):
        verified_crash = json.loads(body.decode("utf-8"))
        if verified_crash['verified']:
            logger.debug('[CrashVerification] Got verified crash with ID %s' % verified_crash['crash_id'])
            crash = Crash.objects(id=verified_crash['crash_id']).limit(1)
            crash.update(verified=True,
                         exploitability=verified_crash['classification'],
                         additional=verified_crash['short_desc'],
                         crash_hash=verified_crash['crash_hash'])
            logger.debug('[CrashVerification] Updated crash in DB.')
        else:
            logger.debug('[CrashVerification] Could not verify crash.')
            crash = Crash.objects.get(id=verified_crash['crash_id'])
            if crash:
                crash.delete()
            logger.debug('[CrashVerification] Deleted crash from database.')

    def run(self):
        connect(f3c_global_config.db_name, host=f3c_global_config.db_host)
        self.channel.basic_consume(self.on_message, self.queue_name)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.connection.close()
