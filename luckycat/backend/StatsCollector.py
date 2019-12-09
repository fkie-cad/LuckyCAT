import datetime
import json
import logging
import os
from multiprocessing import Process

from mongoengine import connect
from mongoengine.queryset import DoesNotExist

from luckycat import luckycat_global_config
from luckycat.backend import WorkQueue
from luckycat.database.models.Job import Job
from luckycat.database.models.Statistic import Statistic

logger = logging.getLogger(os.path.basename(__file__).split('.')[0])


class StatsCollector(Process):
    def __init__(self):
        super(StatsCollector, self).__init__()
        self.wq = WorkQueue.WorkQueue()
        self.queue_name = 'stats'
        if not self.wq.queue_exists(self.queue_name):
            self.wq.create_queue(self.queue_name)
        self.channel = self.wq.get_channel()

    def update_stats(self, stats):
        try:
            job_doc = Job.objects.get(name=stats['job_name'])
            job_id = job_doc.id
            current_stats = Statistic.objects.get(job_id=str(job_id))
            current_stats.update(set__iteration=current_stats['iteration'] + 1)
        except DoesNotExist:
            current_stats = Statistic(job_id=str(job_id),
                                      runtime=0,
                                      iteration=1,
                                      execs_per_sec=0,
                                      date=datetime.datetime.now())
            current_stats.save()
        logger.debug(f'Received stats {str(stats)}')

    def update_external_stats(self, stats):
        try:
            job_doc = Job.objects.get(name=stats['job_name'])
            job_id = job_doc.id
            current_stats = Statistic.objects.get(job_id=str(job_id))
            current_stats.update(runtime=stats['runtime'],
                                 iteration=stats['total_execs'],
                                 execs_per_sec=stats['cumulative_speed'])
        except DoesNotExist:
            current_stats = Statistic(job_id=str(job_id),
                                      runtime=stats['runtime'],
                                      iteration=stats['total_execs'],
                                      execs_per_sec=stats['cumulative_speed'])
            current_stats.save()
        logger.debug(f'Received stats {str(stats)}')

    def on_message(self, channel, method_frame, header_frame, body):
        stats = json.loads(body.decode("utf-8"))
        if stats['fuzzer'] == 'afl' or 'syzkaller':
            self.update_external_stats(stats)
        elif stats['fuzzer'] == 'cfuzz':
            self.update_stats(stats)
        elif stats['fuzzer'] == 'elf_fuzzer':
            self.update_stats(stats)
        else:
            logger.warning(f"Unknown fuzzer {stats['fuzzer']}")

    def run(self):
        logger.info('Starting StatsCollector...')
        connect(luckycat_global_config.db_name, host=luckycat_global_config.db_host)
        self.channel.basic_consume(self.on_message, self.queue_name)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.connection.close()
