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

    def calculate_statistics(self):
        statistic = {}
        selected_project = self.get_selected_project()
        job_names = self.list_job_names()
        project_statistics = {"job_names": job_names}
        if selected_project:
            project_statistics.update(self.calculate_general_statistics_for_specific_project(selected_project))
            statistic["project_statistics"] = project_statistics
            statistic["diffierent_crash_signals"] = self.calculate_different_crash_signals_for_selected_project(selected_project)
        else:
            project_statistics = self.calculate_general_statistics(project_statistics)
            statistic["project_statistics"] = project_statistics
            statistic["diffierent_crash_signals"] = self.calculate_different_crash_signals()
        statistic["test"] = "In progress..."
        return statistic

    def calculate_different_crash_signals_for_selected_project(self, selected_project):
        different_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_project}
            },
            {
                "$group": {"_id": "$crash_signal", "quantity": {"$sum": 1}}
            }
        ])
        different_crashes_with_quantity = {}
        for different_crash in different_crashes:
            different_crashes_with_quantity[different_crash["_id"]] = different_crash["quantity"]
        return different_crashes_with_quantity

    def calculate_different_crash_signals(self):
        distinct_crash_signals = Crash.objects.distinct('crash_signal')
        distinct_crash_signals_with_quantity = {}
        for crash_signal in distinct_crash_signals:
            distinct_crash_signals_with_quantity[crash_signal] = Crash.objects(crash_signal=crash_signal).count()
        return distinct_crash_signals_with_quantity

    def summarize_individual_project_statistics(self):
        iteration = 0
        runtime = 0
        execs_per_sec = 0
        for project_statistic in Statistic.objects:
            iteration += project_statistic.iteration
            runtime += project_statistic.runtime
            execs_per_sec += project_statistic.execs_per_sec
        return {"iteration": iteration, "runtime": runtime, "execs_per_sec": execs_per_sec}

    def list_job_names(self):
        job_names = []
        for job in Job.objects:
            job_names.append(job.name)
        return job_names

    def calculate_general_statistics(self, project_statistics):
        project_statistics.update(self.summarize_individual_project_statistics())
        number_of_job_names = Job.objects.count()
        project_statistics["number_of_job_names"] = number_of_job_names
        return project_statistics

    def calculate_general_statistics_for_specific_project(self, selected_project):
        # what to do if two projects have the same name. which one should be selected?
        project_statistic = Statistic.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_project}
            },
        ])
        project_statistic = self.transform_CommandCursorObject_to_dict(project_statistic)
        return {"iteration": project_statistic["iteration"],
                "runtime": project_statistic["runtime"],
                "execs_per_sec": project_statistic["execs_per_sec"]}

    def get_selected_project(self):
        return flask.request.args.get("project")

    def transform_CommandCursorObject_to_dict(self, project_statistic):
        return list(project_statistic)[0]


@statistics.route('/statistics/show', methods=['GET'])
@login_required
def show_statistics():
    statistic = StatisticCalculator().calculate_statistics()
    return flask.render_template("stats_show.html",
                                 results=statistic)
