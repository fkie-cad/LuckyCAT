import logging
import os
import json
import datetime
from multiprocessing import Process
from mongoengine import connect
from mongoengine.queryset import DoesNotExist
from luckycat import f3c_global_config
from luckycat.backend import WorkQueue
from luckycat.database.models.Statistic import Statistic

logger = logging.getLogger(os.path.basename(__file__).split(".")[0])


class StatsCollector(Process):
    def __init__(self):
        super(StatsCollector, self).__init__()
        self.wq = WorkQueue.WorkQueue()
        self.queue_name = "stats"
        if not self.wq.queue_exists(self.queue_name):
            self.wq.create_queue(self.queue_name)
        self.channel = self.wq.get_channel()

    def update_stats(self, stats):
        try:
            current_stats = Statistic.objects.get(job_id=stats['job_id'])
            current_stats.update(set__iteration=current_stats['iteration'] + 1)
        except DoesNotExist:
            current_stats = Statistic(job_id=str(stats['job_id']),
                                      runtime=0,
                                      iteration=1,
                                      execs_per_sec=0,
                                      date=datetime.datetime.now())
            current_stats.save()
        # TODO get last iteration and add one
        # current_stats = Statistic(job_id=str(stats['job_id']),
        #                           runtime=0,
        #                           iteration=1,
        #                           execs_per_sec=0,
        #                           date=datetime.datetime.now())
        # TODO
        logger.warn('Received stats %s' % str(stats))

    def update_afl_stats(self, stats):
        # FIXME use mongoengine
        vars = {"job_id": stats['job_id']}
        where = "job_id = $job_id"
        res = self.db.select("statistics", where=where, vars=vars)
        res = list(res)

        with self.db.transaction():
            if len(res) == 0:
                self.db.insert("statistics", project_id=stats['project_id'],
                               runtime=stats['runtime'],
                               iteration=stats['total_execs'],
                               execs_per_sec=stats['cumulative_speed'])

            else:
                self.db.update("statistics", runtime=stats['runtime'],
                               iteration=stats['total_execs'],
                               execs_per_sec=stats['cumulative_speed'],
                               where="project_id = $project_id", vars={"project_id": stats['project_id']})

    def on_message(self, channel, method_frame, header_frame, body):
        stats = json.loads(body.decode("utf-8"))
        if stats['fuzzer'] == 'afl':
            self.update_afl_stats(stats)
        elif stats['fuzzer'] == 'cfuzz':
            self.update_stats(stats)
        elif stats['fuzzer'] == 'elf_fuzzer':
            self.update_stats(stats)
        else:
            logger.warn("Unknown fuzzer %s" % stats['fuzzer'])

    def run(self):
        logger.info("Starting StatsCollector...")
        connect(f3c_global_config.db_name, host=f3c_global_config.db_host)
        self.channel.basic_consume(self.on_message, self.queue_name)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.connection.close()
