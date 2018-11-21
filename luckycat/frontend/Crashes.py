import base64
import collections
import io
import os
from difflib import SequenceMatcher

import flask
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
                job_name = get_job_name_of_job_id(crash.job_id)
                encoded_original_test_case, encoded_crash_test_case  = get_original_and_crash_test_case_of_crash(crash)
                return flask.render_template("crashes_view.html",
                                             crash=crash,
                                             job_name=job_name,
                                             encoded_crash_test_case=encoded_crash_test_case,
                                             encoded_original_test_case=encoded_original_test_case)
            else:
                flask.flash("'Not allowed to view this crash.")
                return flask.redirect('crashes/show')
        else:
            flask.flash('No crash with crash id %s' % crash_id)
            return flask.redirect('crashes/show')
    else:
        flask.flash('Not a valid crash id.')
        return flask.redirect('crashes/show')

def get_job_name_of_job_id(job_id):
    return list(Job.objects(id=job_id))[0]["name"]


def testcase_can_be_diffed(job_id):
    mutation_engine = list(Job.objects(id=job_id))[0]["mutation_engine"]
    if mutation_engine == "radamsa":
        return True
    else:
        return False


def get_original_and_crash_test_case_of_crash(crash):
    crash_test_case = crash.test_case
    original_test_case = list(Job.objects(id=crash.job_id))[0]["samples"]
    encoded_original_test_case = base64.b64encode(original_test_case).decode('ascii')
    encoded_crash_test_case = base64.b64encode(crash_test_case).decode('ascii')

    if testcase_can_be_diffed(crash.job_id):
        if (original_test_case.startswith(b'PK')):
            import zipfile
            zipfile = zipfile.ZipFile(io.BytesIO(original_test_case))
            max_similarity = 0
            for name in zipfile.namelist():
                possible_original_test_case = zipfile.read(name)
                similarity = SequenceMatcher(None, base64.b64encode(possible_original_test_case),
                                             encoded_crash_test_case).ratio()
                if similarity > max_similarity:
                    max_similarity = similarity
                    original_test_case = possible_original_test_case

            encoded_original_test_case = base64.b64encode(original_test_case).decode('ascii')
    else:
        encoded_original_test_case = None


    return encoded_original_test_case, encoded_crash_test_case


@crashes.route('/crashes/show/next/<crash_id>')
@login_required
def show_next_crash(crash_id):
    job_id_of_crash = list(Crash.objects(id=crash_id))[0]["job_id"]
    all_job_crashes = list(Crash.objects(job_id=job_id_of_crash))
    for index, crash in enumerate(all_job_crashes):
        if str(crash["id"]) == str(crash_id):
            if index == len(all_job_crashes)-1:
                next_crash_index = 0
                break
            else:
                next_crash_index = index + 1
                break
    return show_crash(all_job_crashes[next_crash_index]["id"])


@crashes.route('/crashes/show/previous/<crash_id>')
@login_required
def show_previous_crash(crash_id):
    job_id_of_crash = list(Crash.objects(id=crash_id))[0]["job_id"]
    all_job_crashes = list(Crash.objects(job_id=job_id_of_crash))
    for index, crash in enumerate(all_job_crashes):
        if str(crash["id"]) == str(crash_id):
            if index == 0:
                next_crash_index = len(all_job_crashes)-1
                break
            else:
                next_crash_index = index - 1
                break
    return show_crash(all_job_crashes[next_crash_index]["id"])



@crashes.route('/crashes/download/<crash_id>')
@login_required
def download_crash(crash_id):
    job_ids = _get_job_ids_of_user()
    crash = Crash.objects.get(id=crash_id)
    if crash:
        if crash.job_id in job_ids:
            filename = os.path.join('/tmp', crash_id)
            with open(filename, 'wb') as f:
                f.write(crash.test_case)
                return flask.send_file(filename, as_attachment=True)
        else:
            flask.flash('You are not allowed to download this crash.')
            return flask.redirect('crashes/show')
    else:
        flask.flash('Unknown crash ID: %s' % crash_id)
        return flask.redirect('crashes/show')
