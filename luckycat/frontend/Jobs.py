import datetime
import json
import logging
import os

import flask
from flask_security import login_required, current_user

from luckycat import luckycat_global_config
from luckycat.database.models.Crash import Crash
from luckycat.database.models.Job import Job
from luckycat.database.models.User import User
from luckycat.frontend.InMemoryZip import InMemoryZip

jobs = flask.Blueprint('jobs', __name__)


def mutation_engine_requires_samples(engine):
    return engine != 'external' and engine != 'urandom'


def can_do_stuff_with_job(current_user, owner):
    return current_user.has_role('admin') or current_user.email == owner.email


@jobs.route("/jobs/show")
@login_required
def jobs_show():
    filtered_jobs = []
    if current_user.has_role('admin'):
        filtered_jobs = Job.objects
    else:
        for job in Job.objects:
            if job.owner:
                if job.owner.email == current_user.email:
                    filtered_jobs.append(job)

    return flask.render_template("jobs_show.html", jobs=filtered_jobs)


@jobs.route("/jobs/add", methods=['GET', 'POST'])
@login_required
def add_job():
    # TODO check if job with this name already exists
    if flask.request.method == 'GET':
        engines = [x['name'] for x in luckycat_global_config.mutation_engines]
        fuzzers = [x['name'] for x in luckycat_global_config.fuzzers]
        verifiers = [x['name'] for x in luckycat_global_config.verifiers]

        return flask.render_template("jobs_add.html",
                                     engines=engines,
                                     fuzzers=fuzzers,
                                     verifiers=verifiers)
    else:
        data = flask.request.form
        files = flask.request.files

        engine = data.get('mutation_engine')
        if data.get('fuzzer') == "afl" or "syzkaller":
            engine = 'external'

        if not ('fuzzing_target' in files):
            flask.flash('Please provide a fuzzing target.')
            return flask.redirect('/jobs/add')

        if mutation_engine_requires_samples(engine) and not ('samples' in files):
            flask.flash('If mutation engine is not external then you must provide some initial test cases.')
            return flask.redirect('/jobs/add')

        samples = None
        if 'samples' in files:
            samples = files['samples'].stream.read()

        firmware_root = None
        if 'firmware_root' in files:
            firmware_root = files['firmware_root'].stream.read()

        new_job = Job(name=data.get('name'),
                      description=data.get('description'),
                      maximum_samples=luckycat_global_config.maximum_samples,
                      archived=False,
                      enabled=True,
                      maximum_iteration=int(data.get('maximum_iteration')),
                      timeout=int(data.get('timeout')),
                      date=datetime.datetime.now().strftime('%Y-%m-%d'),
                      mutation_engine=engine,
                      fuzzer=data.get('fuzzer'),
                      verifier=data.get('verifier'),
                      samples=samples,
                      fuzzing_target=files['fuzzing_target'].stream.read(),
                      cmd_args=data.get('cmd_args'),
                      firmware_root=firmware_root,
                      owner=User.objects.get(email=current_user.email))
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
            if not can_do_stuff_with_job(current_user, job.owner):
                logging.error('User %s can not delete job with id %s' %
                              (current_user.email, str(job.id)))
                flask.flash('You are not allow to delete this job.')
            else:
                job.delete()
                crashes = Crash.objects(job_id=job_id)
                crashes.delete()
        return flask.redirect('/jobs/show')
    else:
        return flask.render_template('jobs_delete.html', id=job_id)


@jobs.route('/jobs/edit/<job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    # TODO prefill form with current values
    job = Job.objects.get(id=job_id)
    if job:
        if not can_do_stuff_with_job(current_user, job.owner):
            flask.flash('You are not allowed to edit this job')
            return flask.redirect("/jobs/show")
        if flask.request.method == 'POST':
            data = flask.request.form
            engine = data.get('mutation_engine')
            if data.get('fuzzer') == "afl" or "syzkaller":
                engine = 'external'

            Job.objects(id=job_id).update(**{
                'name': data.get('name'),
                'description': data.get('description'),
                'fuzzer': data.get('fuzzer'),
                'mutation_engine': engine,
                'verifier': data.get('verifier'),
            })

            return flask.redirect("/jobs/show")
        else:
            engines = [x['name'] for x in luckycat_global_config.mutation_engines]
            fuzzers = [x['name'] for x in luckycat_global_config.fuzzers]
            verifiers = [x['name'] for x in luckycat_global_config.verifiers]
            return flask.render_template('jobs_edit.html',
                                         job=job,
                                         engines=engines,
                                         fuzzers=fuzzers,
                                         verifiers=verifiers)
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
    # FIXME may crash if no crashes available
    if job_id is None:
        flask.flash("Invalid job ID")
        return flask.redirect('/jobs/show')

    job = Job.objects.get(id=job_id)
    if not can_do_stuff_with_job(current_user, job.owner):
        flask.flash('User is not allowed to download job.')
        return flask.redirect('/jobs/show')

    job_crashes = Crash.objects(job_id=job_id)
    if job_crashes:
        imz = InMemoryZip()
        summary = {}
        for c in job_crashes:
            summary[str(c.id)] = _get_summary_for_crash(c)
            imz.append("%s" % str(c.id), c.test_case)
        imz.append("summary.json", json.dumps(summary, indent=4))

        filename = os.path.join('/tmp', '%s.zip' % job_id)
        if os.path.exists(filename):
            os.remove(filename)
        imz.writetofile(filename)
        return flask.send_file(filename, as_attachment=True)
