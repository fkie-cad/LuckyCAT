import logging
import time
import os
from multiprocessing import Process
from mongoengine import connect
from luckycat import f3c_global_config
from luckycat.database.models.Job import Job
from luckycat.database.models.Statistic import Statistic

logger = logging.getLogger(os.path.basename(__file__).split(".")[0])


class JobScheduler(Process):

    def __init__(self):
        super(JobScheduler, self).__init__()

    def _get_active_jobs(self):
        res = Job.objects(enabled=True)
        return res

    def _get_job_statistics(self, job_id):
        return Statistic.objects(job_id=job_id).order_by('date').first()

    def _timeout_or_max_iters(self, project, stats):
        return project.maximum_iteration < stats.iteration or project.timeout < stats.runtime

    def run(self):
        logger.info("Starting JobScheduler...")
        connect(f3c_global_config.db_name, host=f3c_global_config.db_host)
        while 1:
            jobs = self._get_active_jobs()
            for job in jobs:
                res = self._get_job_statistics(job.id)
                print(type(res), res)
                if res:
                    logger.info("Job: %s, Iterations: %d/%d, Runtime: %d/%d" %
                                (job.name, res.iteration, job.maximum_iteration,
                                 res.runtime, job.timeout))

                    if self._timeout_or_max_iters(job, res):
                        logger.info("Job %s reached either timeout of %d or maximum interations of %d" %
                                    (job.name, job.timeout, job.maximum_iteration))
                        job.update(enabled=False)
                        # TODO start next job
                    else:
                        logger.debug("Job %s should continue..." % job.name)

            time.sleep(f3c_global_config.job_scheduler_sleeptime)
