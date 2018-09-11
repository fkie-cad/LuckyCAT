import flask
from flask_security import login_required
import collections
from datetime import timedelta
from luckycat.database.models.Statistic import Statistic
from luckycat.database.models.Job import Job
from luckycat.database.models.Crash import Crash
statistics = flask.Blueprint('statistics', __name__)

# TODO use SQLalchemy
class StatisticCalculator:

    def summarize_individual_project_statistics(self):
        iteration = 0
        runtime = 0
        execs_per_sec = 0
        for project_statistic in Statistic.objects:
            iteration += project_statistic.iteration
            runtime += project_statistic.runtime
            execs_per_sec += project_statistic.execs_per_sec
        return {"iteration": iteration, "runtime": runtime, "execs_per_sec": execs_per_sec}

    def list_job_names():
        job_names = []
        for job in Job.objects:
            job_names.append(job.name)
        return job_names

    def calculate_statistics(self):
        statistic = {}
        project_statistics = self.summarize_individual_project_statistics()
        job_names = self.list_job_names()
        number_of_job_names = Job.objects.count()
        statistic["project_statistics"] = project_statistics
        # project_query = web.input()
        project_query = flask.request.args.get("project")
        return statistic


@statistics.route('/statistics/show', methods=['GET'])
@login_required
def show_statistics():
    statistic = StatisticCalculator().calculate_statistics()
    return flask.render_template("stats_show.html",
                                 results=statistic)
