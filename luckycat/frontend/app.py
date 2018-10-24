import datetime
from flask import Flask, redirect, render_template, flash
from flask_security import Security, login_required, MongoEngineUserDatastore

from luckycat.frontend.JobsApi import jobs_api
from luckycat.frontend.Crashes import crashes
from luckycat.frontend.Jobs import jobs
from luckycat.frontend.Users import users
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
app.register_blueprint(statistics)


def has_user():
    return User.objects.count() != 0


def has_role():
    return Role.objects.count() != 0


@app.before_first_request
def create_default_user():
    if not has_user():
        admin_role = Role.objects.get(name='admin')
        user_datastore.create_user(email=f3c_global_config.default_user_email,
                                   password=f3c_global_config.default_user_password,
                                   api_key=f3c_global_config.default_user_api_key,
                                   registration_date=datetime.datetime.now(),
                                   roles=[admin_role])
        flash('Added default user on first request', 'success')


@app.route("/")
@app.route("/home")
def index():
    return render_template("home.html")


@app.route("/about")
@login_required
def about():
    return render_template("about.html")


@app.route("/logout")
@login_required
def logout():
    return redirect("/home")
