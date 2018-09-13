import datetime
import json
import os
import base64
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

# TODO reimplement as /edit/job
# class edit_project:
    #     def POST(self):
    #         if not 'user' in session or session.user is None:
    #             f = register_form()
    #             return render.login(f)
    #         i = web.input(id=-1, name="", description="",
    #                       enabled="", archived="",
    #                       ignore_duplicates=0, mutation_engine="")
    #         if i.id == -1:
    #             return render.error("Invalid project identifier")
    #         elif i.name == "":
    #             return render.error("No project name specified")
    #         elif i.description == "":
    #             return render.error("No project description specified")

    #         if i.enabled == "on":
    #             enabled = 1
    #         else:
    #             enabled = 0

    #         if i.archived == "on":
    #             archived = 1
    #         else:
    #             archived = 0

    #         if i.ignore_duplicates == "on":
    #             ignore_duplicates = 1
    #         else:
    #             ignore_duplicates = 0

    #         db = init_web_db()
    #         with db.transaction():
    #             enabled = i.enabled == "on"
    #             archived = i.archived == "on"
    #             db.update("projects", name=i.name, description=i.description,
    #                       maximum_samples=i.max_files, enabled=enabled,
    #                       maximum_iteration=i.max_iteration,
    #                       archived=archived, where="project_id = $project_id",
    #                       ignore_duplicates=ignore_duplicates, mutation_engine=i.mutation_engine,
    #                       vars={"project_id": i.id})
    #         return web.redirect("/projects")

    #     def GET(self):
    #         if not 'user' in session or session.user is None:
    #             f = register_form()
    #             return render.login(f)
    #         i = web.input(id=-1)
    #         if i.id == -1:
    #             return render.error("Invalid project identifier")

    #         db = init_web_db()
    #         what = """project_id, name, description, subfolder, tube_prefix,
    #               maximum_samples, enabled, date, archived,
    #               maximum_iteration, ignore_duplicates, mutation_engine """
    #         where = "project_id = $project_id"
    #         vars = {"project_id": i.id}
    #         res = db.select("projects", what=what, where=where, vars=vars)
    #         res = list(res)
    #         if len(res) == 0:
    #             return render.error("Invalid project identifier")
    #         engines = [x['name'] for x in f3c_global_config.mutation_engines]
    #         fuzzers = [x['name'] for x in f3c_global_config.fuzzers]
    #         return render.edit_project(res[0], engines, fuzzers)


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

    # TODO validate job_id
    job_crashes = Crash.objects(job_id=job_id)

    # TODO check if there are crashes
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
