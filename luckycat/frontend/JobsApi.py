import base64
import datetime
import json

import flask
from flask_security import auth_token_required

from luckycat.database.models.Crash import Crash
from luckycat.database.models.Job import Job

jobs_api = flask.Blueprint('job_api', __name__)


def api_get_job_information(job):
    return {'name': job.name,
            'mutation_engine': job.mutation_engine,
            'job_id': str(job.id),
            'description': job.description,
            'maximum_samples': job.maximum_samples,
            'maximum_iteration': job.maximum_iteration,
            'archived': job.archived,
            'timeout': job.timeout,
            'enabled': job.enabled,
            'fuzzer': job.fuzzer,
            'verifier': job.verifier,
            'cmd_args': job.cmd_args
            }


@jobs_api.route('/api/jobs', methods=['GET'])
@jobs_api.route('/api/job/<job_name>', methods=['GET'])
@auth_token_required
def api_get_job(job_name=None):
    res = Job.objects
    if job_name is None:
        return json.dumps([api_get_job_information(job) for job in res])
    else:
        for job in res:
            if job['name'] == job_name:
                return json.dumps(api_get_job_information(job))
        return json.dumps({'success': False, 'msg': 'unknown job'})


@jobs_api.route('/api/job/<job_id>', methods=['DELETE'])
@auth_token_required
def api_delete_job(job_id=None):
    if job_id is None:
        return json.dumps({'success': False, 'msg': 'no job ID provided'})
    else:
        job = Job.objects.get(id=job_id)
        if job:
            job.delete()
            crashes = Crash.objects(job_id=job_id)
            crashes.delete()
            return json.dumps({'success': True})
        else:
            return json.dumps({'success': False})


@jobs_api.route('/api/job', methods=['PUT'])
@auth_token_required
def api_create_job():
    # TODO check if a job with this name does already exist
    data = flask.request.get_json()
    if data:
        # TODO sanitize data
        if not data.get('name'):
            return json.dumps({'success': False,
                               'msg': "No fuzz job name specified"})
        elif not data.get('description'):
            return json.dumps({'success': False,
                               'msg': "No fuzz job description specified"})
        if data.get('fuzzer') == "afl" and data.get('engine') is not None:
            return json.dumps({'success': False,
                               'msg': "The fuzzer afl contains a mutation engine. No need to select a mutation engine"})
        if data.get('fuzzer') == "syzkaller" and data.get('engine') is not None:
            return json.dumps({'success': False,
                               'msg': "The fuzzer syzkaller contains a mutation engine. No need to select a mutation engine"})
        if data.get('samples') is None or data.get('fuzzing_target') is None:
            return json.dumps({'success': False,
                               'msg': "Please provide a fuzzing target AND some initial test cases."})

        if data.get('firmware_root') is not None:
            firmware_root = base64.b64decode(data.get('firmware_root'))
        else:
            firmware_root = None

        new_job = Job(name=data.get('name'),
                      description=data.get('description'),
                      maximum_samples=int(data.get('maximum_samples')),
                      archived=False,
                      enabled=True,
                      maximum_iteration=int(data.get('maximum_iteration')),
                      timeout=int(data.get('timeout')),
                      date=datetime.datetime.now().strftime('%Y-%m-%d'),
                      mutation_engine=data.get('mutation_engine'),
                      fuzzer=data.get('fuzzer'),
                      samples=base64.b64decode(data.get('samples')),
                      fuzzing_target=base64.b64decode(data.get('fuzzing_target')),
                      cmd_args=data.get('cmd_args'),
                      verifier=data.get('verifier'),
                      firmware_root=firmware_root)
        new_job.save()
        return json.dumps({'success': True})
    else:
        return json.dumps({'success': False, 'msg': 'no json document provided'})
