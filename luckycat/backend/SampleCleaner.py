import logging
import os
import time
from multiprocessing import Process
from luckycat import f3c_global_config

logger = logging.getLogger(os.path.basename(__file__).split(".")[0])


class SampleCleaner(Process):

    def __init__(self):
        super(SampleCleaner, self).__init__()

    def _delete_crashes(self):
        deleted = 0
        for f in os.listdir(f3c_global_config.temporary_path):
            next_file = os.path.join(f3c_global_config.temporary_path, f)
            if os.stat(next_file).st_mtime < time.time() - 2 * 60:
                logger.debug("Deleting sample %s because older than 2 minutes." % next_file)
                try:
                    os.remove(next_file)
                    if os.path.exists(next_file + ".diff"):
                        os.remove(next_file + ".diff")
                    deleted += 1
                except:
                    logger.error("Error removing temporary file: %s" % str(sys.exc_info()[1]))

        if deleted > 0:
            logger.info("Cleaned up %d old test cases." % deleted)

    def run(self):
        # FIXME only delete samples that have been used
        logger.info("Starting SampleCleaner...")
        while 1:
            self._delete_crashes()
            time.sleep(120)
