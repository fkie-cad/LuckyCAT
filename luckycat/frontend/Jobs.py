import datetime
import json
import os
import flask
from flask_security import login_required

from luckycat import f3c_global_config
from luckycat.database.models.Job import Job
from luckycat.database.models.Crash import Crash
from luckycat.frontend.InMemoryZip import InMemoryZip

jobs = flask.Blueprint('jobs', __name__)


@jobs.route("/jobs/show")
@login_required
def jobs_show():
    res = Job.objects
    return flask.render_template("jobs_show.html", jobs=res)


@jobs.route("/jobs/add", methods=['GET', 'POST'])
@login_required
def add_job():
    if flask.request.method == 'GET':
        engines = [x['name'] for x in f3c_global_config.mutation_engines]
        fuzzers = [x['name'] for x in f3c_global_config.fuzzers]

        return flask.render_template("jobs_add.html",
                                     engines=engines,
                                     fuzzers=fuzzers)
    else:
        data = flask.request.form
        files = flask.request.files

        engine = data.get('mutation_engine')
        if data.get('fuzzer') == "afl":
            engine = 'external'

        if not ('fuzzing_target' in files):
            flask.abort(400, description='Please provide a fuzzing target.')

        if engine != 'external' and not ('samples' in files):
            flask.abort(400,
                        description='If mutation engine is not external then you must provide some initial test cases.')

        samples = None
        if 'samples' in files:
            samples = files['samples'].stream.read()

        firmware_root = None
        if 'firmware_root' in files:
            firmware_root = files['firmware_root'].stream.read()

        new_job = Job(name=data.get('name'),
                      description=data.get('description'),
                      maximum_samples=f3c_global_config.maximum_samples,
                      archived=False,
                      enabled=True,
                      maximum_iteration=int(data.get('maximum_iteration')),
                      timeout=int(data.get('timeout')),
                      date=datetime.datetime.now().strftime('%Y-%m-%d'),
                      mutation_engine=engine,
                      fuzzer=data.get('fuzzer'),
                      samples=samples,
                      fuzzing_target=files['fuzzing_target'].stream.read(),
                      firmware_root=firmware_root)
        new_job.save()
        return flask.redirect("/jobs/show")


@jobs.route('/jobs/delete/<job_id>', methods=['GET', 'POST'])
@login_required
def delete_job(job_id):
    if job_id is None:
        flask.abort(400, description="Invalid job ID")
    if flask.request.method == 'POST':
        job = Job.objects.get(id=job_id)
        if job:
            job.delete()
            crashes = Crash.objects(job_id=job_id)
            crashes.delete()
        return flask.redirect('/jobs/show')
    else:
        return flask.render_template('jobs_delete.html', id=job_id)


@jobs.route('/jobs/edit/<job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.objects.get(id=job_id)
    if job:
        if flask.request.method == 'POST':
            data = flask.request.form
            engine = data.get('mutation_engine')
            if data.get('fuzzer') == "afl":
                engine = 'external'

            Job.objects(id=job_id).update(**{
                'name': data.get('name'),
                'description': data.get('description'),
                'fuzzer': data.get('fuzzer'),
                'mutation_engine': engine,
            })

            return flask.redirect("/jobs/show")
        else:
            engines = [x['name'] for x in f3c_global_config.mutation_engines]
            fuzzers = [x['name'] for x in f3c_global_config.fuzzers]
            return flask.render_template('jobs_edit.html',
                                         job=job,
                                         engines=engines,
                                         fuzzers=fuzzers)
    else:
        flask.abort(400, description="Invalid job ID")


def _get_summary_for_crash(crash):
    res = {}
    res['crash_signal'] = crash.crash_signal
    res['exploitability'] = crash.exploitability
    res['date'] = crash.date.strftime("%Y-%m-%d %H:%M:%S")
    res['additional'] = crash.additional
    res['crash_hash'] = crash.crash_hash
    res['verfied'] = crash.verified
    res['filename'] = str(crash.id)
    return res


@jobs.route("/jobs/download/<job_id>")
@login_required
def jobs_download(job_id):
    if job_id is None:
        flask.abort(400, description="Invalid job ID")

    job_crashes = Crash.objects(job_id=job_id)
    if job_crashes:
        imz = InMemoryZip()
        summary = {}
        for c in job_crashes:
            summary[str(c.id)] = _get_summary_for_crash(c)
            imz.append("%s" % str(c.id), c.crash_data)
        imz.append("summary.json", json.dumps(summary, indent=4))

        filename = os.path.join('/tmp', '%s.zip' % job_id)
        if os.path.exists(filename):
            os.remove(filename)
        imz.writetofile(filename)
        return flask.send_file(filename, as_attachment=True)
