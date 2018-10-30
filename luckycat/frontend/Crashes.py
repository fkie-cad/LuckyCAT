import collections
import flask
import os
import base64
from flask_security import login_required, current_user
from luckycat.database.models.Crash import Crash
from luckycat.database.models.Job import Job

crashes = flask.Blueprint('crashes', __name__)


def _get_job_name_from_id(job_id):
    job = Job.objects.get(id=job_id)
    return job.name


def _get_job_ids_of_user():
    job_ids = []
    for job in Job.objects:
        if job.owner and job.owner.email == current_user.email:
            job_ids.append(job.id)
    return job_ids


@crashes.route('/crashes/show')
@login_required
def show_crashes():
    # FIXME show colors again
    # FIXME fix checkboxes and so on!!!
    # FIXME just show first ten results, make it expandable
    job_ids = _get_job_ids_of_user()
    sorted_res = collections.defaultdict(list)
    for crash in Crash.objects:
        if crash.job_id in job_ids:
            sorted_res[str(crash.job_id)] = sorted_res[str(crash.job_id)] + [crash]

    final_res = collections.defaultdict(list)
    for k, v in sorted_res.items():
        final_res[_get_job_name_from_id(k)] = v

    return flask.render_template("crashes_show.html",
                                 results=final_res.items())


@crashes.route('/crashes/show/<crash_id>')
@login_required
def show_crash(crash_id):
    if crash_id:
        crash = Crash.objects.get(id=crash_id)
        if crash:
            job_ids = _get_job_ids_of_user()
            if crash.job_id in job_ids:
                return flask.render_template("crashes_view.html",
                                             crash=crash,
                                             encoded_buffer=base64.b64encode(crash.crash_data).decode('ascii'))
            else:
                flask.flash("'Not allowed to view this crash.")
                return flask.redirect('crashes/show')
        else:
            flask.flash('No crash with crash id %s' % crash_id)
            return flask.redirect('crashes/show')
    else:
        flask.flash('Not a valid crash id.')
        return flask.redirect('crashes/show')


@crashes.route('/crashes/show/next/<crash_id>')
@login_required
def show_next_crash(crash_id):
    pass


@crashes.route('/crashes/download/<crash_id>')
@login_required
def download_crash(crash_id):
    job_ids = _get_job_ids_of_user()
    crash = Crash.objects.get(id=crash_id)
    if crash:
        if crash.job_id in job_ids:
            filename = os.path.join('/tmp', crash_id)
            with open(filename, 'wb') as f:
                f.write(crash.crash_data)
                return flask.send_file(filename, as_attachment=True)
        else:
            flask.flash('You are not allowed to download this crash.')
            return flask.redirect('crashes/show')
    else:
        flask.flash('Unknown crash ID: %s' % crash_id)
        return flask.redirect('crashes/show')
