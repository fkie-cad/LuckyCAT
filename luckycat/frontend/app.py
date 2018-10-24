from flask import Flask, redirect, render_template

from flask_security import Security, login_required, MongoEngineUserDatastore


from luckycat.frontend.JobsApi import jobs_api
from luckycat.frontend.Crashes import crashes
from luckycat.frontend.Jobs import jobs
from luckycat.frontend.Users import users
from luckycat.frontend.StatisticsApi import statistics_api
from luckycat.frontend.Statistics import statistics

from luckycat import f3c_global_config
from luckycat.database.database import db
from luckycat.database.models.Role import Role
from luckycat.database.models.User import User

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = f3c_global_config.secret_key
app.config['SECURITY_PASSWORD_SALT'] = f3c_global_config.secret_key
app.config['MONGODB_DB'] = 'luckycat'
app.config['MONGODB_HOST'] = 'database'
app.config['MONGODB_PORT'] = 27017
# https://mandarvaze.github.io/2015/01/token-auth-with-flask-security.html
app.config['WTF_CSRF_ENABLED'] = False
db.init_app(app)


user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)

app.register_blueprint(jobs_api)
app.register_blueprint(jobs)
app.register_blueprint(crashes)
app.register_blueprint(users)
app.register_blueprint(statistics_api)
app.register_blueprint(statistics)


@app.before_first_request
def create_user():
    user_datastore.create_user(email='donald@great.again', password='password')


@app.route("/")
@app.route("/home")
def index():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/logout")
@login_required
def logout():
    return redirect("/home")

