import flask
from flask_security import login_required
import collections
from datetime import timedelta
from luckycat.database.models.Statistic import Statistic
from luckycat.database.models.Job import Job
from luckycat.database.models.Crash import Crash
import datetime
statistics = flask.Blueprint('statistics', __name__)

# TODO use SQLalchemy
class StatisticCalculator:
    crash_counter = 1
    date_now = datetime.datetime.now()

    def calculate_statistics(self):
        statistic = {}
        selected_project = self.get_selected_project()
        job_names = self.list_job_names()
        project_statistics = {"job_names": job_names}
        if selected_project:
            project_statistics.update(self.calculate_general_statistics_for_specific_project(selected_project))
            statistic["project_statistics"] = project_statistics
            statistic["diffierent_crash_signals"] = self.calculate_different_crash_signals_for_selected_project(selected_project)
            statistic["crashes_over_time"] = {}
            statistic["crashes_over_time"]["crashes"], statistic["crashes_over_time"]["unique_crashes"] = self.calculate_crashes_over_time_for_selected_project(selected_project)
        else:
            project_statistics = self.calculate_general_statistics(project_statistics)
            statistic["project_statistics"] = project_statistics
            statistic["diffierent_crash_signals"] = self.calculate_different_crash_signals()

            statistic["crashes_over_time"] = {}
            statistic["crashes_over_time"]["crashes"], statistic["crashes_over_time"]["unique_crashes"] = self.calculated_crashes_over_time()

        statistic["test"] = "In progress..."
        return statistic

    def calculated_crashes_over_time(self):
        crashes = {}
        all_crashes = Crash.objects(date__gte=self.date_now - timedelta(days=30)).only("date").order_by("date")
        all_crashes_per_time_interval = self.calculate_crashes_per_time_interval(list(all_crashes))
        crashes["all_time"] = all_crashes_per_time_interval
        last_24_hours_crashes = Crash.objects(date__gte=self.date_now - timedelta(days=1)).only("date").order_by("date")
        last_24_hours_crashes_per_time_interval = self.calculate_crashes_per_time_interval(list(last_24_hours_crashes))
        crashes["last_24_hours"] = last_24_hours_crashes_per_time_interval
        last_72_hours_crashes = Crash.objects(date__gte=self.date_now - timedelta(days=3)).only("date").order_by("date")
        last_72_hours_crashes_per_time_interval = self.calculate_crashes_per_time_interval(list(last_72_hours_crashes))
        crashes["last_72_hours"] = last_72_hours_crashes_per_time_interval

        unique_crashes = {}
        unique_crashes["all_time"] = all_crashes_per_time_interval
        unique_crashes["last_24_hours"] = last_24_hours_crashes_per_time_interval
        unique_crashes["last_72_hours"] = last_72_hours_crashes_per_time_interval
        return crashes, unique_crashes

    def calculate_crashes_over_time_for_selected_project(self, selected_project):
        crashes = {}
        all_crashes = Crash.objects.aggregate(*[
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
                "$sort": {"date": 1}
            },
            {
                "$project": {"date": 1}
            }
        ])
        all_crashes = self.transform_CommandCursorObject_to_list(all_crashes)
        all_crashes_per_time_interval = self.calculate_crashes_per_time_interval(all_crashes)
        crashes["all_time"] = all_crashes_per_time_interval
        last_24_hours_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_project, "date": {"$gte": self.date_now - timedelta(days=1)}}
            },
            {
                "$sort": {"date": 1}
            },
            {
                "$project": {"date": 1}
            }
        ])
        last_24_hours_crashes = self.transform_CommandCursorObject_to_list(last_24_hours_crashes)
        last_24_hours_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_24_hours_crashes)
        crashes["last_24_hours"] = last_24_hours_crashes_per_time_interval
        last_72_hours_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_project, "date": {"$gte": self.date_now - timedelta(days=3)}}
            },
            {
                "$sort": {"date": 1}
            },
            {
                "$project": {"date": 1}
            }
        ])
        last_72_hours_crashes = self.transform_CommandCursorObject_to_list(last_72_hours_crashes)
        last_72_hours_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_72_hours_crashes)
        crashes["last_72_hours"] = last_72_hours_crashes_per_time_interval

        unique_crashes = {}
        unique_crashes["all_time"] = all_crashes_per_time_interval
        unique_crashes["last_24_hours"] = last_24_hours_crashes_per_time_interval
        unique_crashes["last_72_hours"] = last_72_hours_crashes_per_time_interval
        return crashes, unique_crashes

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
        project_statistics["number_of_crashes"] = Crash.objects().count()
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
        all_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_project}
            }
        ])
        all_crashes = self.transform_CommandCursorObject_to_list(all_crashes)
        number_of_all_crashes = len(all_crashes)
        project_statistic = self.transform_CommandCursorObject_to_list(project_statistic)[0]
        return {"iteration": project_statistic["iteration"],
                "runtime": project_statistic["runtime"],
                "execs_per_sec": project_statistic["execs_per_sec"],
                "number_of_crashes": number_of_all_crashes}

    def get_selected_project(self):
        return flask.request.args.get("project")

    def transform_CommandCursorObject_to_list(self, CommandCursorObject):
        return list(CommandCursorObject)

    def calculate_crashes_per_time_interval(self, crashes, time_intervall=10):
        if crashes:
            time_intervalls = self.generate_list_of_time_intervalls(crashes[0]["date"], crashes[-1]["date"], time_intervall)
            crashes_per_time_intervall = self.count_crashes_per_time_intervall(time_intervalls, crashes)
        else:
            crashes_per_time_intervall = {}
        return crashes_per_time_intervall

    def generate_list_of_time_intervalls(self, start_time, end_time, intervall_length_in_minutes):
        list = [start_time]
        time = start_time
        while time < end_time:
            time = time + timedelta(minutes=intervall_length_in_minutes)
            list.append(time)
        return list

    def count_crashes_per_time_intervall(self, time_intervalls, crashes):
        crashes_per_time_intervall = collections.OrderedDict()
        crashes_copy = list(crashes)
        for i in range(len(time_intervalls)-1):
            for crash in crashes_copy[:]:
                if crash["date"] >= time_intervalls[i] and crash["date"] < time_intervalls[i+1]:
                    crashes_per_time_intervall[time_intervalls[i]] = self.crash_counter
                    self.crash_counter += 1
                    crashes_copy.remove(crash)
            # uncomment if every interval should get a value in the chart
            # if time_intervalls[i] not in crashes_per_time_intervall:
            #     crashes_per_time_intervall[time_intervalls[i]] = self.crash_counter
        if time_intervalls[len(time_intervalls)-1] == crashes[-1]["date"]:
            self.crash_counter += 1
        return crashes_per_time_intervall


@statistics.route('/statistics/show', methods=['GET'])
@login_required
def show_statistics():
    statistic = StatisticCalculator().calculate_statistics()
    return flask.render_template("stats_show.html",
                                 results=statistic)
