import collections
import flask
import os
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


@crashes.route('/crashes/show', methods=['GET'])
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
        flask.abort(400, description='Unknown crash ID: %s' % crash_id)

# def map_signal_to_sting(self, signal):
#     # TODO make a jinja filter!
#     if type(signal) is int:
#         signal = str(signal)
#     signal_mapping = {
#         "129": "SIGHUP(129)",
#         "132": "SIGILL(132)",
#         "134": "SIGABRT(134)",
#         "136": "SIGFPE(136)",
#         "137": "SIGKILL(137)",
#         "139": "SIGSEGV(139)",
#         "140": "SIGSYS(140)",
#         "143": "SIGTERM(143)",
#         "146": "SIGCONT/SIGSTOP/SIGCHILD(146)",
#         "159": "SIGSYS(159)"
#     }
#     if signal in signal_mapping:
#         signal = signal_mapping[signal]
#     return signal

# def hexor(buf):
#     try:
#         return hex(buf)
#     except:
#         return buf

# def render_crash(crash_id):
#     # XXX: FIXME: Joxean, why do 2 queries instead of one????
#     # Get the project_id from the crash_id
#     db = init_web_db()
#     vars = {"id": crash_id}
#     res = db.select("crashes", where="crash_id=$id", vars=vars)
#     crash_row = res[0]

#     # Get the project name
#     where = "project_id=$id"
#     vars = {"id": crash_row.project_id}
#     res = db.select("projects", what="name", where=where, vars=vars)
#     project_name = res[0].name

#     crash_data = {}
#     crash_data["crash_id"] = crash_row.crash_id
#     crash_data["project_id"] = crash_row.project_id
#     crash_data["program_counter"] = 0
#     crash_data["crash_signal"] = crash_row.crash_signal
#     crash_data["exploitability"] = crash_row.exploitability
#     crash_data["disassembly"] = crash_row.disassembly
#     crash_data["date"] = crash_row.date
#     crash_data["crash_hash"] = crash_row.crash_hash
#     crash_data["additional"] = crash_row.additional

#     return render.view_crash(project_name, crash_data, str=str, map=map,
#                              repr=myrepr, b64=b64decode, sorted=sorted,
#                              type=type, hexor=hexor)

# class view_crash:
#     def GET(self):
#         if not 'user' in session or session.user is None:
#             f = register_form()
#             return render.login(f)

#         i = web.input()
#         if not "id" in i:
#             return render.error("No crash identifier given")

#         return render_crash(i.id)

# class next_crash:
#     def GET(self):
#         i = web.input()
#         if not "id" in i:
#             return render.error("No crash identifier given")

#         # XXX: FIXME: Joxean, why do 2 queries instead of one????
#         # Get the project_id from the crash_id
#         crash_id = i.id
#         db = init_web_db()
#         vars = {"id": crash_id}
#         res = db.select("crashes", where="crash_id=$id", vars=vars)
#         crash_row = res[0]

#         # Get the project name
#         where = "crash_id < $id and project_id = $project_id"
#         vars = {"project_id": crash_row.project_id, "id": crash_id}
#         rows = db.select("crashes", what="crash_id", where=where, vars=vars, order="crash_id desc")
#         if len(rows) > 0:
#             crash_id = rows[0].crash_id
#             return render_crash(crash_id)
#         else:
#             return render.error("No more crashes for this project")
# sys.path.append("../minimizer")


# from diff_match_patch import diff_match_patch
# from inmemoryzip import InMemoryZip
# class download_sample:
#     def GET(self):
#         if not 'user' in session or session.user is None:
#             f = register_form()
#             return render.login(f)

#         i = web.input()
#         if not "id" in i:
#             return render.error("No crash identifier given")

#         db = init_web_db()
#         what = "crash_path"
#         where = "crash_id = $id"
#         vars = {"id": i.id}
#         res = db.select("crashes", what=what, where=where, vars=vars)
#         res = list(res)
#         if len(res) == 0:
#             return render.error("Invalid crash identifier")
#         crash_path = res[0].crash_path

#         if not os.path.exists(crash_path):
#             return render.error("Crash sample does not exists! %s" % crash_path)

#         web.header("Content-type", "application/octet-stream")
#         web.header("Content-disposition", "attachment; filename=%s" % os.path.split(crash_path)[-1])
#         f = open(crash_path, 'rb')
#         return f.read()
