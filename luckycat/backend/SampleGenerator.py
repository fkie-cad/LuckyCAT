import logging
import base64
import os
import random
import sys
import tempfile
import json
import zipfile
import hashlib
from multiprocessing import Process
from mongoengine import connect
from luckycat.database.models.Job import Job
from luckycat import f3c_global_config
from luckycat.backend import WorkQueue

logger = logging.getLogger(os.path.basename(__file__).split(".")[0])


class SampleGenerator(Process):
    def __init__(self):
        super(SampleGenerator, self).__init__()
        self.wq = WorkQueue.WorkQueue()

    def _get_active_jobs(self):
        return Job.objects(enabled=True)

    def read_random_file(self, basepath):
        if not os.path.exists(basepath):
            logger.error("Basepath %s does not exist. Skipping..." % basepath)
            return None

        files = os.listdir(basepath)
        if len(files) == 0:
            logger.error("No samples in basepath %s. Skipping..." % basepath)
            return None

        filename = random.choice(files)
        return os.path.join(basepath, filename)

    def build_mutation_engine_command(self, cmd, filename, subfolder):
        cmd = cmd.replace("%INPUT%", '"%s"' % filename)
        temp_file = tempfile.mktemp(dir=f3c_global_config.temporary_path)
        cmd = cmd.replace("%OUTPUT%", temp_file)
        cmd = cmd.replace("%FOLDER%", subfolder)
        return cmd, temp_file

    def _create_samples_dir(self, job):
        logger.info("Getting test cases from database and setting up directories")

        # FIXME escape project name for subfolder
        fuzz_job_basepath = os.path.join(f3c_global_config.templates_path, job.name)
        if not os.path.exists(fuzz_job_basepath):
            os.mkdir(fuzz_job_basepath)

        if job.samples.startswith(b"PK"):
            logger.info("Detected zip file")
            b = job.samples
            filename = hashlib.sha224(b).hexdigest() + ".zip"
            path_to_zip_file = os.path.join(fuzz_job_basepath, filename)
            f = open(path_to_zip_file, 'wb')
            f.write(b)
            f.close()

            zip_ref = zipfile.ZipFile(path_to_zip_file, 'r')
            zip_ref.extractall(os.path.split(path_to_zip_file)[0])
            zip_ref.close()

            try:
                os.remove(path_to_zip_file)
            except:
                logger.error("Could not delete zipfile %s" % path_to_zip_file)
        else:
            b = job.samples
            filename = hashlib.sha224(b).hexdigest()
            f = open(os.path.join(fuzz_job_basepath, filename), 'wb')
            f.write(b)
            f.close()

    def _get_mutation_engine_template_command(self, engine_name):
        for e in f3c_global_config.mutation_engines:
            if e['name'] == engine_name:
                return e['command']
        return ""

    def create_sample(self, job):
        command = self._get_mutation_engine_template_command(job.mutation_engine)
        fuzz_job_basepath = os.path.join(f3c_global_config.templates_path, job.name)

        if not os.path.exists(fuzz_job_basepath) or len(os.listdir(fuzz_job_basepath)) == 0:
            self._create_samples_dir(job)

        filename = self.read_random_file(fuzz_job_basepath)
        if filename is None:
            # TODO: maybe throw an execption??
            return

        logger.debug("Random template file %s" % filename)
        cmd, temp_file = self.build_mutation_engine_command(command, filename, fuzz_job_basepath)
        logger.debug("Generating mutated file %s" % temp_file)
        logger.debug("*** Command: %s" % cmd)
        os.system(cmd)

        try:
            buf = open(temp_file, "rb").read()
            sample = {'payload': base64.b64encode(buf).decode('utf-8'),
                      'filename': temp_file,
                      'job_id': str(job.id)}
            self.wq.publish("%s-samples" % job.name, json.dumps(sample))
        except:
            logger.error("Error putting job in queue: %s" % str(sys.exc_info()[1]))
            logger.error("Removing temporary file %s" % temp_file)
            try:
                os.remove(temp_file)
            except:
                pass

    def run(self):
        logger.info("Starting SampleGenerator...")
        connect(f3c_global_config.db_name, host=f3c_global_config.db_host)
        while 1:
            jobs = self._get_active_jobs()
            for job in jobs:
                if job.mutation_engine != 'external':
                    samples_queue = "%s-%s" % (job.name, "samples")
                    maximum = job.maximum_samples
                    if not self.wq.queue_exists(samples_queue):
                        self.wq.create_queue(samples_queue)

                    if not self.wq.queue_is_full(samples_queue, maximum):
                        for i in range(self.wq.get_pending_elements(samples_queue, maximum)):
                            try:
                                self.create_sample(job)
                            except:
                                logger.error("Error creating sample: %s" % str(sys.exc_info()[1]))
                                raise
