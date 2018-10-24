import collections
import datetime
from datetime import timedelta

import flask
from flask_security import login_required

from luckycat.database.models.Crash import Crash
from luckycat.database.models.Job import Job
from luckycat.database.models.Statistic import Statistic

statistics = flask.Blueprint('statistics', __name__)

class StatisticCalculator:
    crash_counter = 1
    date_now = datetime.datetime.now()

    def calculate_statistics(self):
        selected_job = self.get_selected_job()
        if selected_job:
            statistic = self.calculate_statistic_for_selected_job(selected_job)
        else:
            statistic = self.calculate_statistic_for_all_jobs()
        statistic["test"] = "In progress..."
        return statistic

    def calculate_statistic_for_all_jobs(self):
        statistic = {}
        statistic["general"] = self.calculate_general_statistics()
        statistic["job_names"] = self.list_job_names()
        statistic["diffierent_crash_signals"] = self.calculate_different_crash_signals()
        statistic["crashes_over_time"] = {}
        statistic["crashes_over_time"]["crashes"], statistic["crashes_over_time"]["iterations"]\
            , statistic["crashes_over_time"]["unique_crashes"] = self.calculate_crashes_over_time()
        return statistic

    def calculate_statistic_for_selected_job(self, selected_job):
        statistic = {}
        statistic["general"] = self.calculate_general_statistics_for_specific_job(selected_job)
        statistic["job_names"] = self.list_job_names()
        statistic["diffierent_crash_signals"] = self.calculate_different_crash_signals_for_selected_job(selected_job)
        statistic["crashes_over_time"] = {}
        statistic["crashes_over_time"]["crashes"], statistic["crashes_over_time"]["iterations"]\
            , statistic["crashes_over_time"]["unique_crashes"] = self.calculate_crashes_over_time_for_selected_job(selected_job)
        return statistic

    def calculate_crashes_over_time(self):
        crashes, iterations = self.calculate_normal_crashes_over_time()
        unique_crashes = self.calculate_unique_crashes_over_time()
        return crashes, iterations, unique_crashes

    def calculate_unique_crashes_over_time(self):
        unique_crashes = {}
        unique_crashes["all_time"] = self.calculate_all_unique_crashes_per_time_interval()
        unique_crashes["last_72_hours"] = self.calculate_last_72_hours_uniqe_crashes_per_time_interval()
        unique_crashes["last_24_hours"] = self.calculate_last_24_hours_unique_crashes_per_time_interval()
        return unique_crashes

    def calculate_last_72_hours_uniqe_crashes_per_time_interval(self):
        last_72_hours_unique_crashes = Crash.objects.aggregate(*[
            {
                "$match": {"date": {"$gte": self.date_now - timedelta(days=1)}}
            },
            {
                "$group": {"_id": "$crash_hash", "date": {"$min": "$date"}}
            },
            {
                "$sort": {"date": 1}
            }
        ])
        last_72_hours_unique_crashes = list(last_72_hours_unique_crashes)
        self.crash_counter -= len(last_72_hours_unique_crashes)
        last_72_hours_unique_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_72_hours_unique_crashes)
        return last_72_hours_unique_crashes_per_time_interval

    def calculate_last_24_hours_unique_crashes_per_time_interval(self):
        last_24_hours_unique_crashes = Crash.objects.aggregate(*[
            {
                "$match": {"date": {"$gte": self.date_now - timedelta(days=1)}}
            },
            {
                "$group": {"_id": "$crash_hash", "date": {"$min": "$date"}}
            },
            {
                "$sort": {"date": 1}
            }
        ])
        last_24_hours_unique_crashes = list(last_24_hours_unique_crashes)
        self.crash_counter -= len(last_24_hours_unique_crashes)
        last_24_hours_unique_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_24_hours_unique_crashes)
        return last_24_hours_unique_crashes_per_time_interval

    def calculate_all_unique_crashes_per_time_interval(self):
        all_unique_crashes = Crash.objects.aggregate(*[
            {
                "$group": {"_id": "$crash_hash", "date": {"$min": "$date"}}
            },
            {
                "$sort": {"date": 1}
            }
        ])
        all_unique_crashes_per_time_interval = self.calculate_crashes_per_time_interval(list(all_unique_crashes))
        return all_unique_crashes_per_time_interval

    def calculate_normal_crashes_over_time(self):
        crashes = {}
        iterations = {}
        crashes["all_time"], iterations["all_time"] = self.calculate_all_crashes_per_time_interval()
        crashes["last_72_hours"], iterations["last_72_hours"] = self.calculate_last_72_hours_crashes_per_time_interval()
        crashes["last_24_hours"], iterations["last_24_hours"] = self.calculate_last_24_hours_crashes_per_time_interval()
        self.crash_counter = 1
        return crashes, iterations

    def calculate_last_72_hours_crashes_per_time_interval(self):
        last_72_hours_crashes = Crash.objects(date__gte=self.date_now - timedelta(days=3)).only("date", "iteration").order_by("date")
        last_72_hours_crashes = list(last_72_hours_crashes)
        self.crash_counter -= len(last_72_hours_crashes)
        last_72_hours_crashes_per_time_interval, last_72_hours_iterations_per_time_interval = self.calculate_crashes_and_iterations_per_time_interval(list(last_72_hours_crashes))
        return last_72_hours_crashes_per_time_interval, last_72_hours_iterations_per_time_interval

    def calculate_last_24_hours_crashes_per_time_interval(self):
        last_24_hours_crashes = Crash.objects(date__gte=self.date_now - timedelta(days=1)).only("date", "iteration").order_by("date")
        last_24_hours_crashes = list(last_24_hours_crashes)
        self.crash_counter -= len(last_24_hours_crashes)
        last_24_hours_crashes_per_time_interval, last_24_hours_iterations_per_time_interval = self.calculate_crashes_and_iterations_per_time_interval(list(last_24_hours_crashes))
        return last_24_hours_crashes_per_time_interval, last_24_hours_iterations_per_time_interval

    def calculate_all_crashes_per_time_interval(self):
        all_crashes = Crash.objects().only("date", "iteration").order_by("date")
        all_crashes_per_time_interval, iterations_per_time_interval = self.calculate_crashes_and_iterations_per_time_interval(list(all_crashes))
        return all_crashes_per_time_interval, iterations_per_time_interval

    def calculate_crashes_over_time_for_selected_job(self, selected_job):
        crashes, iterations = self.calculate_normal_crashes_over_time_for_selected_job(selected_job)
        unique_crashes = self.calculate_unique_crashes_over_time_for_selected_job(selected_job)

        return crashes, iterations, unique_crashes

    def calculate_unique_crashes_over_time_for_selected_job(self, selected_job):
        unique_crashes = {}
        unique_crashes["all_time"] = self.calculate_all_unique_crashes_per_time_interval_for_selected_job(selected_job)
        unique_crashes["last_72_hours"] = self.calculate_last_72_hours_uniqe_crashes_per_time_interval_for_selected_job(selected_job)
        unique_crashes["last_24_hours"] = self.calculate_last_24_hours_unique_crashes_per_time_interval_for_selected_job(selected_job)
        return unique_crashes

    def calculate_last_72_hours_uniqe_crashes_per_time_interval_for_selected_job(self, selected_job):
        last_72_hours_unique_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job, "date": {"$gte": self.date_now - timedelta(days=3)}}
            },
            {
                "$group": {"_id": "$crash_hash", "date": {"$min": "$date"}}
            },
            {
                "$sort": {"date": 1}
            }
        ])
        last_72_hours_unique_crashes = list(last_72_hours_unique_crashes)
        self.crash_counter -= len(last_72_hours_unique_crashes)
        last_72_hours_unique_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_72_hours_unique_crashes)
        return last_72_hours_unique_crashes_per_time_interval

    def calculate_last_24_hours_unique_crashes_per_time_interval_for_selected_job(self, selected_job):
        last_24_hours_unique_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job, "date": {"$gte": self.date_now - timedelta(days=1)}}
            },
            {
                "$group": {"_id": "$crash_hash", "date": {"$min": "$date"}}
            },
            {
                "$sort": {"date": 1}
            }
        ])
        last_24_hours_unique_crashes = list(last_24_hours_unique_crashes)
        self.crash_counter -= len(last_24_hours_unique_crashes)
        last_24_hours_unique_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_24_hours_unique_crashes)
        return last_24_hours_unique_crashes_per_time_interval

    def calculate_all_unique_crashes_per_time_interval_for_selected_job(self, selected_job):
        all_unique_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job}
            },
            {
                "$group": {"_id": "$crash_hash", "date": {"$min": "$date"}}
            },
            {
                "$sort": {"date": 1}
            }
        ])
        all_unique_crashes_per_time_interval = self.calculate_crashes_per_time_interval(list(all_unique_crashes))
        return all_unique_crashes_per_time_interval

    def calculate_normal_crashes_over_time_for_selected_job(self, selected_job):
        crashes = {}
        iterations = {}
        crashes["all_time"], iterations["all_time"] = self.calculate_all_crashes_per_time_interval_for_selected_job(selected_job)
        crashes["last_72_hours"], iterations["last_24_hours"] = self.calculate_last_72_hours_crashes_per_time_interval_for_selected_job(selected_job)
        crashes["last_24_hours"], iterations["last_72_hours"] = self.calculate_last_24_hours_crashes_per_time_interval_for_selected_job(selected_job)
        self.crash_counter = 1
        return crashes, iterations

    def calculate_last_72_hours_crashes_per_time_interval_for_selected_job(self, selected_job):
        last_72_hours_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job, "date": {"$gte": self.date_now - timedelta(days=3)}}
            },
            {
                "$sort": {"date": 1}
            },
            {
                "$project": {"date": 1, "iteration": 1}
            }
        ])
        last_72_hours_crashes = list(last_72_hours_crashes)
        self.crash_counter -= len(last_72_hours_crashes)
        last_72_hours_crashes_per_time_interval, last_72_hours_iterations_per_time_interval = self.calculate_crashes_and_iterations_per_time_interval(last_72_hours_crashes)
        return last_72_hours_crashes_per_time_interval, last_72_hours_iterations_per_time_interval

    def calculate_last_24_hours_crashes_per_time_interval_for_selected_job(self, selected_job):
        last_24_hours_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job, "date": {"$gte": self.date_now - timedelta(days=1)}}
            },
            {
                "$sort": {"date": 1}
            },
            {
                "$project": {"date": 1, "iteration": 1}
            }
        ])
        last_24_hours_crashes = list(last_24_hours_crashes)
        self.crash_counter -= len(last_24_hours_crashes)
        last_24_hours_crashes_per_time_interval, last_24_hours_iterations_per_time_interval = self.calculate_crashes_and_iterations_per_time_interval(last_24_hours_crashes)
        return last_24_hours_crashes_per_time_interval, last_24_hours_iterations_per_time_interval

    def calculate_all_crashes_per_time_interval_for_selected_job(self, selected_job):
        all_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job}
            },
            {
                "$sort": {"date": 1}
            },
            {
                "$project": {"date": 1, "iteration": 1}
            }
        ])
        all_crashes_per_time_interval, iterations_per_time_interval = self.calculate_crashes_and_iterations_per_time_interval(list(all_crashes))
        return all_crashes_per_time_interval, iterations_per_time_interval

    def calculate_different_crash_signals_for_selected_job(self, selected_job):
        different_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job}
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

    def summarize_individual_job_statistics(self):
        iteration = 0
        runtime = 0
        execs_per_sec = 0
        for job_statistic in Statistic.objects:
            iteration += job_statistic.iteration
            runtime += job_statistic.runtime
            execs_per_sec += job_statistic.execs_per_sec
        return iteration, runtime, execs_per_sec

    def list_job_names(self):
        job_names = []
        for job in Job.objects:
            job_names.append(job.name)
        return job_names

    def calculate_general_statistics(self):
        iteration, runtime, execs_per_sec = self.summarize_individual_job_statistics()
        return {"iteration": iteration,
                "runtime": runtime,
                "execs_per_sec": execs_per_sec,
                "number_of_job_names": Job.objects.count(),
                "number_of_crashes": Crash.objects().count(),
                "number_of_unique_crashes": self.calculate_number_of_unique_crashes(),
                "number_of_unique_exploitable_crashes": self.calculate_number_of_unique_and_exploitable_crashes()}

    def calculate_number_of_unique_crashes(self):
        unique_crashes = Crash.objects.aggregate(*[
            {
                "$group": {"_id": "$crash_hash"}
            }
        ])
        return len(list(unique_crashes))

    def calculate_number_of_unique_and_exploitable_crashes(self):
        unique_exploitable_crashes = Crash.objects.aggregate(*[
            {
                "$match": {"exploitability": "EXPLOITABLE"}
            },
            {
                "$group": {"_id": "$crash_hash"}
            }
        ])
        return len(list(unique_exploitable_crashes))

    def calculate_general_statistics_for_specific_job(self, selected_job):
        # what to do if two jobs have the same name. which one should be selected?
        job_statistic = self.get_job_information_from_Statistic_table(selected_job)
        return {"iteration": job_statistic["iteration"],
                "runtime": job_statistic["runtime"],
                "execs_per_sec": job_statistic["execs_per_sec"],
                "number_of_crashes": self.calculate_number_of_crashes_for_selected_job(selected_job),
                "number_of_unique_crashes": self.calculate_number_of_unique_crashes_for_selected_job(selected_job),
                "number_of_unique_exploitable_crashes": self.calculate_number_of_unique_and_exploitable_crashes_for_selected_job(selected_job)}

    def calculate_number_of_unique_and_exploitable_crashes_for_selected_job(self, selected_job):
        unique_exploitable_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job, "exploitability": "EXPLOITABLE"}
            },
            {
                "$group": {"_id": "$crash_hash"}
            }
        ])
        return len(list(unique_exploitable_crashes))

    def calculate_number_of_unique_crashes_for_selected_job(self, selected_job):
        unique_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job}
            },
            {
                "$group": {"_id": "$crash_hash"}
            }
        ])
        return len(list(unique_crashes))

    def calculate_number_of_crashes_for_selected_job(self, selected_job):
        all_crashes = Crash.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job}
            }
        ])
        return len(list(all_crashes))

    def get_job_information_from_Statistic_table(self, selected_job):
        job_statistic = Statistic.objects.aggregate(*[
            {
                '$lookup':
                    {'from': Job._get_collection_name(),
                     'localField': 'job_id',
                     'foreignField': '_id',
                     'as': 'relation'}
            },
            {
                "$match": {"relation.name": selected_job}
            },
        ])
        return list(job_statistic)[0]

    def get_selected_job(self):
        return flask.request.args.get("job")

    def calculate_crashes_and_iterations_per_time_interval(self, crashes, time_intervall=10):
        if crashes:
            time_intervalls = self.generate_list_of_time_intervalls(crashes[0]["date"], crashes[-1]["date"], time_intervall)
            crashes_per_time_intervall, iterations_per_time_interval = self.count_crashes_and_iterations_per_time_intervall(time_intervalls, crashes)
        else:
            crashes_per_time_intervall, iterations_per_time_interval = {}, {}
        return crashes_per_time_intervall, iterations_per_time_interval

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

    def count_crashes_and_iterations_per_time_intervall(self, time_intervalls, crashes):
        crashes_per_time_intervall = collections.OrderedDict()
        iterations_per_time_interval = collections.OrderedDict()
        crashes_copy = list(crashes)
        for i in range(len(time_intervalls)-1):
            for crash in crashes_copy[:]:
                if crash["date"] >= time_intervalls[i] and crash["date"] < time_intervalls[i+1]:
                    crashes_per_time_intervall[time_intervalls[i]] = self.crash_counter
                    iterations_per_time_interval[time_intervalls[i]] = crash["iteration"]
                    self.crash_counter += 1
                    crashes_copy.remove(crash)
            # uncomment if every interval should get a value in the chart
            # if time_intervalls[i] not in crashes_per_time_intervall:
            #     crashes_per_time_intervall[time_intervalls[i]] = self.crash_counter
        if time_intervalls[len(time_intervalls)-1] == crashes[-1]["date"]:
            crashes_per_time_intervall[time_intervalls[len(time_intervalls)-1]] = self.crash_counter
            iterations_per_time_interval[time_intervalls[len(time_intervalls)-1]] = crashes[-1]["iteration"]
            self.crash_counter += 1
        return crashes_per_time_intervall, iterations_per_time_interval

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
            crashes_per_time_intervall[time_intervalls[len(time_intervalls)-1]] = self.crash_counter
            self.crash_counter += 1
        return crashes_per_time_intervall


@statistics.route('/statistics/show', methods=['GET'])
@login_required
def show_statistics():
    statistic = StatisticCalculator().calculate_statistics()
    return flask.render_template("stats_show.html",
                                 statistics=statistic)
