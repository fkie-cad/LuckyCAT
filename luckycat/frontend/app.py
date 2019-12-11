from flask import Flask, redirect, render_template
from flask_security import login_required

from luckycat.database.database import db
from luckycat.frontend.Crashes import crashes
from luckycat.frontend.Jobs import jobs
from luckycat.frontend.JobsApi import jobs_api
from luckycat.frontend.Statistics import statistics
from luckycat.frontend.StatisticsApi import statistics_api
from luckycat.frontend.Users import users
from luckycat.frontend.jinja2_custom import exploitable_color, map_signal_to_string
from luckycat.frontend.security.init_security import add_flask_security

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['MONGODB_DB'] = 'luckycat'
app.config['MONGODB_HOST'] = 'database'
app.config['MONGODB_PORT'] = 27017

db.init_app(app)
add_flask_security(app)

app.register_blueprint(jobs_api)
app.register_blueprint(jobs)
app.register_blueprint(crashes)
app.register_blueprint(users)
app.register_blueprint(statistics_api)
app.register_blueprint(statistics)

app.jinja_env.globals.update(exploitable_color=exploitable_color)
app.jinja_env.globals.update(map_signal_to_string=map_signal_to_string)


@app.route('/')
@app.route('/home')
def index():
    return render_template('home.html')


@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/logout')
@login_required
def logout():
    return redirect('/home')
