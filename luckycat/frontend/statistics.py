import logging.config
import os
import sys
import web
import json
import collections
from datetime import timedelta

logging.config.fileConfig("../logging.conf")
logging = logging.getLogger(os.path.basename(__file__).split(".")[0])

# TODO use SQLalchemy

# FIXME get rid of this!
render = web.template.render('templates/', base='layout')


class statistics(object):
    crash_counter = 1

    def select_last_24_hours_crashes(self, additional_from="", additional_where=""):
        sql = " select crashes.crash_signal, crashes.date " \
            " from crashes " + additional_from \
            + " where crashes.date > DATE_SUB(NOW(), INTERVAL 24 HOUR) " + additional_where + \
              " order by date "
        last_24_hours_crashes = self.db.query(sql)
        last_24_hours_crashes = self.convert_Iterbetter_db_instance_to_list(last_24_hours_crashes)
        return last_24_hours_crashes

    def select_last_72_hours_crashes_from_db(self, additional_from="", additional_where=""):
        sql = " select crashes.crash_signal, crashes.date " \
            " from crashes " + additional_from \
            + " where crashes.date > DATE_SUB(NOW(), INTERVAL 72 HOUR) " + additional_where + \
              " order by date "
        last_72_hours_crashes = self.db.query(sql)
        last_72_hours_crashes = self.convert_Iterbetter_db_instance_to_list(last_72_hours_crashes)
        return last_72_hours_crashes

    def select_all_crashes_from_db(self, additional_from="", additional_where=""):
        sql = " select crashes.crash_signal, crashes.date " \
            " from crashes " + additional_from \
            + additional_where + \
            " order by date"
        all_crashes = self.db.query(sql)
        all_crashes = self.convert_Iterbetter_db_instance_to_list(all_crashes)
        return all_crashes

    def select_different_crash_signals_from_db(self, additional_where=""):
        sql = " select distinct crash_signal, count(*) count " \
            " from crashes join projects on crashes.project_id = projects.project_id " \
            " where projects.enabled = 1 " + additional_where + \
            " group by crash_signal"
        different_crash_signals = self.db.query(sql)
        return different_crash_signals

    def select_unique_crash_hashes_from_db(self, additional_from="", additional_where=""):
        sql = " select distinct crash_hash, exploitability " \
            " from crashes " + additional_from + additional_where
        unique_crash_hashes = self.db.query(sql)
        unique_crash_hashes = self.convert_Iterbetter_db_instance_to_list(unique_crash_hashes)
        return unique_crash_hashes

    def select_projects_from_db(self):
        sql = """ select *
                    from projects """
        projects = self.db.query(sql)
        projects = self.convert_Iterbetter_db_instance_to_list(projects)
        return projects

    def select_statistics_from_db(self, additional_from="", additional_where=""):
        sql = " select * " \
            " from statistics " + additional_from \
            + additional_where + \
            " order by statistic_id DESC "
        statistics = self.db.query(sql)
        statistics = self.convert_Iterbetter_db_instance_to_list(statistics)
        return statistics

    def convert_Iterbetter_db_instance_to_list(self, Itterbetter_instance):
        list = []
        for item in Itterbetter_instance:
            temp = dict()
            for key in item:
                temp[key] = item[key]
            list.append(temp)

        return list

    def count_crashes_per_time_intervall(self, time_intervalls, crashes):
        crashes_per_time_intervall = collections.OrderedDict()
        for i in range(len(time_intervalls)):
            for crash in crashes:
                if crash["date"] >= time_intervalls[i] and crash["date"] < time_intervalls[i+1]:
                    crashes_per_time_intervall[time_intervalls[i]] = self.crash_counter
                    self.crash_counter += 1
            if time_intervalls[i] not in crashes_per_time_intervall:
                crashes_per_time_intervall[time_intervalls[i]] = self.crash_counter
        return crashes_per_time_intervall

    def generate_list_of_time_intervalls(self, start_time, end_time, intervall_length_in_minutes):
        list = [start_time]
        time = start_time
        while time < end_time:
            time = time + timedelta(minutes=intervall_length_in_minutes)
            list.append(time)
        return list

    def calculate_crashes_per_time_interval(self, crashes, time_intervall=10):
        if crashes:
            time_intervalls = self.generate_list_of_time_intervalls(crashes[0]["date"], crashes[-1]["date"], time_intervall)
            last_24_hours_crashes_per_time_intervall = self.count_crashes_per_time_intervall(time_intervalls, crashes)
        else:
            last_24_hours_crashes_per_time_intervall = {}
        return last_24_hours_crashes_per_time_intervall

    def count_exploitable_hashes(self, crash_hashes):
        exploitable_counter = 0
        for crash in crash_hashes:
            if crash['exploitability'] == "1":
                exploitable_counter += 1
        return exploitable_counter

    def summarize_individual_project_statistics(self, statistics):
        iteration = 0
        runtime = 0
        execs_per_sec = 0
        for project_statistic in statistics:
            iteration += project_statistic["iteration"]
            runtime += project_statistic["runtime"]
            execs_per_sec += project_statistic["execs_per_sec"]
        return {"iteration": iteration, "runtime": runtime, "execs_per_sec": execs_per_sec}

    def list_project_names(self, projects):
        project_names = []
        for project in projects:
            project_names.append(project["name"])
        return project_names

    def GET(self):

        # if not 'user' in session or session.user is None:
        #     f = register_form()
        #     return render.login(f)

        project_query = web.input()
        if project_query == {}:
            different_crash_signals = self.select_different_crash_signals_from_db()

            all_crashes = self.select_all_crashes_from_db()
            all_crashes_per_time_interval = self.calculate_crashes_per_time_interval(all_crashes, 60)
            last_72_hours_crashes = self.select_last_72_hours_crashes_from_db()
            self.crash_counter -= len(last_72_hours_crashes)
            last_72_hours_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_72_hours_crashes)
            last_24_hours_crashes = self.select_last_24_hours_crashes()
            self.crash_counter -= len(last_24_hours_crashes)
            last_24_hours_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_24_hours_crashes)

            statistics = self.select_statistics_from_db()
            general_statistics = self.summarize_individual_project_statistics(statistics)
            projects = self.select_projects_from_db()
            project_names = self.list_project_names(projects)
            unique_crash_hashes = self.select_unique_crash_hashes_from_db()
            general_statistics["number_of_projects"] = len(projects)
            general_statistics["number_of_unique_crashes"] = len(unique_crash_hashes)
            general_statistics["number_of_uniqe_exploitable_hashes"] = self.count_exploitable_hashes(
                unique_crash_hashes)
            general_statistics["number_of_all_crashes"] = len(all_crashes)

            return render.statistics(general_statistics,
                                     project_names,
                                     different_crash_signals,
                                     last_24_hours_crashes_per_time_interval,
                                     last_72_hours_crashes_per_time_interval,
                                     all_crashes_per_time_interval)
        else:
            different_crash_signals = self.select_different_crash_signals_from_db(
                additional_where="and projects.name = \"" + project_query.project + "\"")

            all_crashes = self.select_all_crashes_from_db(additional_from="join projects on crashes.project_id = projects.project_id ",
                                                          additional_where=" where projects.name = \"" + project_query.project + "\" ")
            all_crashes_per_time_interval = self.calculate_crashes_per_time_interval(all_crashes, 60)
            last_72_hours_crashes = self.select_last_72_hours_crashes_from_db(additional_from=" join projects on crashes.project_id = projects.project_id",
                                                                              additional_where=" and projects.name = \"" + project_query.project + "\" ")
            self.crash_counter -= len(last_72_hours_crashes)
            last_72_hours_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_72_hours_crashes)
            last_24_hours_crashes = self.select_last_24_hours_crashes(additional_from="join projects on crashes.project_id = projects.project_id ",
                                                                      additional_where=" and projects.name = \"" + project_query.project + "\" ")
            self.crash_counter -= len(last_24_hours_crashes)
            last_24_hours_crashes_per_time_interval = self.calculate_crashes_per_time_interval(last_24_hours_crashes)

            statistics = self.select_statistics_from_db(additional_from=" join projects on statistics.project_id = projects.project_id",
                                                        additional_where=" where projects.name = \"" + project_query.project + "\" ")
            general_statistics = self.summarize_individual_project_statistics(statistics)
            projects = self.select_projects_from_db()
            project_names = self.list_project_names(projects)
            unique_crash_hashes = self.select_unique_crash_hashes_from_db(additional_from="join projects on crashes.project_id = projects.project_id ",
                                                                          additional_where=" where projects.name = \"" + project_query.project + "\" ")
            general_statistics["number_of_unique_crashes"] = len(unique_crash_hashes)
            general_statistics["number_of_uniqe_exploitable_hashes"] = self.count_exploitable_hashes(unique_crash_hashes)
            general_statistics["number_of_all_crashes"] = len(all_crashes)

            return render.statistics(general_statistics,
                                     project_names,
                                     different_crash_signals,
                                     last_24_hours_crashes_per_time_interval,
                                     last_72_hours_crashes_per_time_interval,
                                     all_crashes_per_time_interval)
