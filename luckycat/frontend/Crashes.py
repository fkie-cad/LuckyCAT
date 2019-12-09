import base64
import collections
import io
import json
import os
from difflib import SequenceMatcher

from flask import render_template, redirect, send_file, flash, request, Blueprint
from flask_security import login_required, current_user

from luckycat.database.models.Crash import Crash
from luckycat.database.models.Job import Job

crashes = Blueprint('crashes', __name__)


def _get_job_name_from_id(job_id):
    job = Job.objects.get(id=job_id)
    return job.name


def _get_job_id_of_job_name(job_name):
    for job in Job.objects:
        if job_name == job.name:
            return job.id


def _get_job_ids_of_user():
    job_ids = []
    for job in Job.objects:
        if job.owner and job.owner.email == current_user.email:
            job_ids.append(job.id)
    return job_ids


def _get_job_names_of_user():
    job_ids = _get_job_ids_of_user()
    job_names = []
    for job_id in job_ids:
        job_names.append(get_job_name_of_job_id(job_id))
    return job_names


@crashes.route('/crashes/show')
@login_required
def show_crashes(crashes=None):
    # FIXME show colors again
    # FIXME fix checkboxes and so on!!!
    # FIXME just show first ten results, make it expandable
    if crashes:
        crashes = crashes
    else:
        crashes = list(Crash.objects.aggregate(*[]))
    job_ids = _get_job_ids_of_user()
    sorted_res = collections.defaultdict(list)
    for crash in crashes:
        if crash["job_id"] in job_ids:
            sorted_res[str(crash["job_id"])] = sorted_res[str(crash["job_id"])] + [crash]
    final_res = collections.defaultdict(list)
    for k, v in sorted_res.items():
        final_res[_get_job_name_from_id(k)] = v
    return render_template("crashes_show.html",
                           results=final_res.items())


@crashes.route('/crashes/show/<crash_id>')
@login_required
def show_crash(crash_id):
    # TODO only show diff if mutation engine is external and actually mutates something (e.g. radamsa)
    # TODO Do not show diff if mutation engine is fuzzer interal or generates samples like /dev/urandom
    if crash_id:
        crash = Crash.objects.get(id=crash_id)
        if crash:
            job_ids = _get_job_ids_of_user()
            if crash.job_id in job_ids:
                job_name = get_job_name_of_job_id(crash.job_id)
                encoded_original_test_case, encoded_crash_test_case = get_original_and_crash_test_case_of_crash(crash)
                return render_template("crashes_view.html",
                                       crash=crash,
                                       job_name=job_name,
                                       encoded_crash_test_case=encoded_crash_test_case,
                                       encoded_original_test_case=encoded_original_test_case)
            else:
                flash("'Not allowed to view this crash.")
                return redirect('crashes/show')
        else:
            flash('No crash with crash id %s' % crash_id)
            return redirect('crashes/show')
    else:
        flash('Not a valid crash id.')
        return redirect('crashes/show')


def get_job_name_of_job_id(job_id):
    return list(Job.objects(id=job_id))[0]["name"]


@crashes.route('/crashes/search', methods=['GET', 'POST'])
@login_required
def search_crash(error=None):
    crash_database_structure = [item for item in Crash._get_collection().find()[0]]
    job_names = _get_job_names_of_user()
    if request.method == 'POST':
        try:
            crashes = process_search_query()
            if crashes:
                return show_crashes(crashes=crashes)
            else:
                error = "No Crashes are fitting to your Search Request"
        except Exception as e:
            error = e

    return render_template("crashes_search.html", database_structure=crash_database_structure, job_names=job_names,
                           error=error)


def process_search_query():
    query = json.loads(request.form['search'])
    selected_job_name = request.form.get('job')
    if not selected_job_name == "":
        job_id = _get_job_id_of_job_name(selected_job_name)
        query.update({"job_id": job_id})
    crashes = Crash.objects.aggregate(*[{"$match": query}])
    return list(crashes)


def testcase_can_be_diffed(job_id):
    mutation_engine = list(Job.objects(id=job_id))[0]["mutation_engine"]
    if mutation_engine == "radamsa":
        return True
    else:
        return False


def get_original_and_crash_test_case_of_crash(crash):
    crash_test_case = crash.test_case
    original_test_case = list(Job.objects(id=crash.job_id))[0]["samples"]
    encoded_crash_test_case = base64.b64encode(crash_test_case).decode('ascii')

    if testcase_can_be_diffed(crash.job_id):
        if (original_test_case.startswith(b'PK')):
            original_test_case = get_original_crash_test_case_of_zipfile(crash_test_case, original_test_case)
        encoded_original_test_case = base64.b64encode(original_test_case).decode('ascii')
    else:
        encoded_original_test_case = None

    return encoded_original_test_case, encoded_crash_test_case


def get_original_crash_test_case_of_zipfile(crash_test_case, original_test_case):
    import zipfile
    zipfile = zipfile.ZipFile(io.BytesIO(original_test_case))
    max_similarity = 0
    for name in zipfile.namelist():
        possible_original_test_case = zipfile.read(name)
        similarity = SequenceMatcher(None, base64.b64encode(possible_original_test_case),
                                     base64.b64encode(crash_test_case)).ratio()
        if similarity > max_similarity:
            max_similarity = similarity
            original_test_case = possible_original_test_case
    return original_test_case


@crashes.route('/crashes/show/next/<crash_id>')
@login_required
def show_next_crash(crash_id):
    job_id_of_crash = list(Crash.objects(id=crash_id))[0]["job_id"]
    all_job_crashes = list(Crash.objects(job_id=job_id_of_crash))
    for index, crash in enumerate(all_job_crashes):
        if str(crash["id"]) == str(crash_id):
            if index == len(all_job_crashes) - 1:
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
                next_crash_index = len(all_job_crashes) - 1
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
                return send_file(filename, as_attachment=True)
        else:
            flash('You are not allowed to download this crash.')
            return redirect('crashes/show')
    else:
        flash('Unknown crash ID: %s' % crash_id)
        return redirect('crashes/show')
