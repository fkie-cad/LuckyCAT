from datetime import date, timedelta

from requests import get


class StatsFetcher:
    def __init__(self, base_url, authentication_token):
        self.authentication_token = authentication_token
        self.base_url = base_url
        self.stats_api_url = base_url + '/api/stats'

    def get_request(self, url):
        return get(url, verify=False, headers={'Authentication-Token': self.authentication_token,
                                               'content-type': 'application/json'}).json()
    def fetch_general_stats(self, job_name=None):
        if job_name is None:
            url = self.stats_api_url
            general_stats = self.get_request(url)
            return general_stats
        else:
            url = self.stats_api_url + '/' + job_name
            general_stats = self.get_request(url)
            return general_stats

    def fetch_yesterdays_crashes(self, job_name=None):
        date_today = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        if job_name is None:
            url = self.stats_api_url + '/' + date_today
            general_stats = self.get_request(url)
            return general_stats
        else:
            url = self.stats_api_url + '/' + date_today
            general_stats = self.get_request(url)
            return general_stats

    def get_all_jobs(self):
        url = self.base_url + '/' + '/api/jobs'
        jobs = self.get_request(url)
        job_names = []
        for job in jobs:
            job_names.append(job['name'])
        return job_names

    def fetch_general_and_last_day_crashes_stats_for_every_job(self):
        all_job_names = self.get_all_jobs()
        jobs_stats = []
        for name in all_job_names:
            job_general_stats = self.fetch_general_stats(name)
            job_last_day_crashes_stats = self.fetch_yesterdays_crashes(name)
            jobs_stats.append({'Job':name, 'stats': {'General Stats': job_general_stats, 'Last Day Stats': job_last_day_crashes_stats}})
        return jobs_stats






