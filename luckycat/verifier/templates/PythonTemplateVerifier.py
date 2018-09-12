import json
import configparser
import multiprocessing
import pika


class PythonTemplateVerifier(object):
    '''
    Use this base class to derive your
    Python-based verifier from. It allows
    you to quickly enhance Lucky CAT with
    a new verifier.
    '''

    def __init__(self, config_path="verifier.cfg"):
        super(PythonTemplateVerifier, self).__init__()

        self.config = configparser.ConfigParser()
        self.config.read(config_path)

    def _verify_one_crash(self, crash_info):
        '''
        Implement this method in your verifier class.
        For a demonstartion see luckycat/verifiers/dummy_verifier/dummy_verifier.py.

        In a nutshell, this function takes a JSON document with
        including the crash as input. Here you execute
        the crash and verify it.

        You should return a dictionary resembling the following:
        {'fuzzer': NAME_OF_THE_FUZZER,
        'filename': test_case_info['filename'],
        'signal': CRASH_SIGNAL,
        'job_id': sample['job_id'],
        }
        '''
        pass

    def _on_test_case(self, channel, method_frame, header_frame, body):
        crash_info = json.loads(body)
        res = self._verify_one_crash(crash_info)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        if res:
            self._send_verification(res)

    def _send_verification(self, crash):
        conn = pika.BlockingConnection(pika.ConnectionParameters(
            self.config['DEFAULT']['queue_host']))
        channel = conn.channel()
        channel.basic_publish(exchange='luckycat',
                              routing_key=self.config['DEFAULT']['out_queue'],
                              body=json.dumps(crash))
        conn.close()

    def run(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(self.config['DEFAULT']['queue_host']))
        channel = connection.channel()
        channel.basic_consume(self._on_test_case,
                              self.config['DEFAULT']['in_queue'])
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            connection.close()
