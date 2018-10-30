import json
import logging
import sys
from multiprocessing import Process
from urllib.parse import urljoin

import requests

from luckycat.reporter import config
from luckycat.reporter.EmailGenerator import EmailGenerator
from luckycat.reporter.EmailSender import EmailSender
from luckycat.reporter.StatsFetcher import StatsFetcher


class Reporter(Process):
    base_url = config.base_url
    email = config.email
    password = config.password
    recipients = config.recipients

    def get_user_authentication_token(self):
        url = urljoin(self.base_url, '/login')
        r = requests.post(url,
                          data=json.dumps({'email': self.email, 'password': self.password}),
                          headers={'content-type': 'application/json'}, verify=False)
        j = r.json()
        if 'response' in j and 'user' in j['response'] and 'authentication_token' in j['response']['user']:
            return j['response']['user']['authentication_token']
        else:
            logging.error("Could not aquire authentication token: %s" % j)
            sys.exit(1)

    def run(self):
        authentication_token = self.get_user_authentication_token()
        stats = StatsFetcher(self.base_url, authentication_token).fetch_general_and_last_day_crashes_stats_for_every_job()
        email = EmailGenerator().process_stats_to_tabular_output(stats)
        EmailSender().send_mails_to_all_recipients(email, self.recipients)


Reporter().run()

