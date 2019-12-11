import json
from datetime import timedelta

import flask
from dateutil.parser import parse as parse_date
from flask_security import auth_token_required

from luckycat.database.models.Crash import Crash
from luckycat.database.models.Job import Job
from luckycat.frontend.Statistics import StatisticCalculator

statistics_api = flask.Blueprint('statistic_api', __name__)


@statistics_api.route('/api/stats', methods=['GET'])
@statistics_api.route('/api/stats/<job_name_or_date>', methods=['GET'])
@statistics_api.route('/api/stats/<job_name_or_date>/<date>', methods=['GET'])
@auth_token_required
def get_general_stats(job_name_or_date=None, date=None):
    if job_name_or_date is None:
        general_statistcis = StatisticCalculator().calculate_general_statistics()
        return json.dumps(general_statistcis)
    else:
        if is_date(job_name_or_date):
            date = parse_date(job_name_or_date)
            crash_stats = get_crash_stats_of_date(date)
            return json.dumps(crash_stats)
        else:
            valid_job_names = StatisticCalculator().list_job_names()
            if job_name_or_date in valid_job_names:
                valid_job_name = job_name_or_date
                if date is None:
                    general_statistcis_of_job = StatisticCalculator().calculate_general_statistics_for_specific_job(
                        job_name_or_date)
                    return json.dumps(general_statistcis_of_job)
                else:
                    if is_date(date):
                        date = parse_date(date)
                        crash_stats = get_crash_stats_of_date_for_selected_job(date, valid_job_name)
                        return json.dumps(crash_stats)
                    else:
                        return 'no vaild date'

            else:
                return 'No valid date or job name'


def get_crash_stats_of_date(date):
    number_of_crashes = Crash.objects(date__gte=date, date__lt=date + timedelta(days=1)).count()
    unique_crashes = get_unique_crashes_of_date(date)
    unique_exploitable_crashes = get_unique_exploitable_crashes_of_date(date)
    return {'number_of_crashes': number_of_crashes,
            'number_of_unique_crashes': len(list(unique_crashes)),
            'number_of_unique_exploitable_crashes': len(list(unique_exploitable_crashes))}


def get_unique_exploitable_crashes_of_date(date):
    unique_exploitable_crashes = Crash.objects.aggregate(*[
        {
            '$match': {'exploitability': 'EXPLOITABLE', 'date': {'$gte': date, '$lt': date + timedelta(days=1)}}
        },
        {
            '$group': {'_id': '$crash_hash'}
        }
    ])
    return unique_exploitable_crashes


def get_unique_crashes_of_date(date):
    unique_crashes = Crash.objects.aggregate(*[
        {
            '$match': {'date': {'$gte': date, '$lt': date + timedelta(days=1)}}
        },
        {
            '$group': {'_id': '$crash_hash'}
        }
    ])
    return unique_crashes


def get_crash_stats_of_date_for_selected_job(date, selected_job):
    crashes = get_crashes_of_date_for_selected_job(date, selected_job)
    unique_crashes = get_unique_crashes_of_date_for_selected_job(date, selected_job)
    unique_exploitable_crashes = get_unique_exploitable_crashes_of_date_for_selected_job(date, selected_job)
    return {'number_of_crashes': len(list(crashes)),
            'number_of_unique_crashes': len(list(unique_crashes)),
            'number_of_unique_exploitable_crashes': len(list(unique_exploitable_crashes))}


def get_unique_exploitable_crashes_of_date_for_selected_job(date, selected_job):
    unique_exploitable_crashes = Crash.objects.aggregate(*[
        {
            '$lookup':
                {'from': Job._get_collection_name(),
                 'localField': 'job_id',
                 'foreignField': '_id',
                 'as': 'relation'}
        },
        {
            '$match': {'relation.name': selected_job, 'exploitability': 'EXPLOITABLE',
                       'date': {'$gte': date, '$lt': date + timedelta(days=1)}}
        },
        {
            '$group': {'_id': '$crash_hash'}
        }
    ])
    return unique_exploitable_crashes


def get_unique_crashes_of_date_for_selected_job(date, selected_job):
    return Crash.objects.aggregate(*[
        {
            '$lookup':
                {'from': Job._get_collection_name(),
                 'localField': 'job_id',
                 'foreignField': '_id',
                 'as': 'relation'}
        },
        {
            '$match': {'relation.name': selected_job, 'date': {'$gte': date, '$lt': date + timedelta(days=1)}}
        },
        {
            '$group': {'_id': '$crash_hash'}
        }
    ])


def get_crashes_of_date_for_selected_job(date, selected_job):
    return Crash.objects.aggregate(*[
        {
            '$lookup':
                {'from': Job._get_collection_name(),
                 'localField': 'job_id',
                 'foreignField': '_id',
                 'as': 'relation'}
        },
        {
            '$match': {'relation.name': selected_job, 'date': {'$gte': date, '$lt': date + timedelta(days=1)}}
        }
    ])


def is_date(string):
    try:
        parse_date(string)
        return True
    except ValueError:
        return False

# curl -i -k https://localhost:5000/api/stats
# curl -i -k -X GET https://localhost:5000/api/stats
# curl -i -k -X GET https://localhost:5000/api/stats/2018-12-01
# curl -i -k -X GET https://localhost:5000/api/stats/test
# curl -i -k -X GET https://localhost:5000/api/stats/test/2018-12-01
# curl -i -k donald@great.again:password https://localhost:5000/api/stats
