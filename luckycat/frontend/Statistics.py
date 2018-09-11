import flask
from flask_security import login_required
import collections
from datetime import timedelta
from luckycat.database.models.Statistic import Statistic
from luckycat.database.models.Job import Job
statistics = flask.Blueprint('statistics', __name__)

# TODO use SQLalchemy
class StatisticCalculator:
    def calculate_statistics(self):
        statistic = []
        for i in Statistic.objects:
            statistic.append(i.iteration)
        # project_query = web.input()
        project_query = flask.request.args.get("project")
        return statistic


@statistics.route('/statistics/show', methods=['GET'])
@login_required
def show_statistics():
    statistic = StatisticCalculator().calculate_statistics()

    return flask.render_template("stats_show.html",
                                 results=statistic)
