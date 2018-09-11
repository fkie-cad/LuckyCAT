import json
import configparser
import multiprocessing
import pika


class PythonFuzzer(multiprocessing.Process):
    '''
    Use this base class to derive your
    Python-based fuzzer from. It allows
    you to quickly enhance Lucky CAT with
    a new fuzzer.
    '''

    def __init__(self, config_path="fuzzer.cfg"):
        super(PythonFuzzer, self).__init__()
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

    def _fuzz_one_test_case(self, test_case_info):
        '''
        Implement this method in your fuzzer class.
        For a demonstartion see luckycat/fuzzers/dummy_fuzzer.py.

        In a nutshell, this function takes a JSON document with
        including the test case as input. Here you call you execute
        the sample and check if a crash occured.

        If the target did not crash, then return None.
        Otherwise, you should return a dictionary resembling the
        following example:
        {'fuzzer': NAME_OF_THE_FUZZER,
        'filename': test_case_info['filename'],
        'signal': CRASH_SIGNAL,
        'job_id': sample['job_id'],
        }
        '''
        pass

    def _on_test_case(self, channel, method_frame, header_frame, body):
        test_case_info = json.loads(body)
        res = self._fuzz_one_test_case(test_case_info)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        if res:
            self._send_crash(res)

    def _send_crash(self, crash):
        conn = pika.BlockingConnection(pika.ConnectionParameters(
            self.config['DEFAULT']['queue_host']))
        channel = conn.channel()
        channel.basic_publish(exchange='luckycat',
                              routing_key=self.config['DEFAULT']['crash_queue'],
                              body=json.dumps(crash))
        conn.close()

    def run(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(self.config['DEFAULT']['queue_host']))
        channel = connection.channel()
        channel.basic_consume(self._on_test_case,
                              self.config['DEFAULT']['sample_queue'])
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            connection.close()
