import datetime
import logging

from flask_security import Security, MongoEngineUserDatastore

from luckycat import luckycat_global_config
from luckycat.database.database import db
from luckycat.database.models.Role import Role
from luckycat.database.models.User import User


def has_user():
    return User.objects.count() != 0


def has_role():
    return Role.objects.count() != 0


def create_default_user_and_roles(user_datastore):
    if not has_role():
        user_datastore.create_role(name='admin',
                                   description='Administrative user of LuckyCat')
        user_datastore.create_role(name='analyst',
                                   description='General LuckyCat user without admin privileges')

    if not has_user():
        admin_role = Role.objects.get(name='admin')
        user_datastore.create_user(email=luckycat_global_config.default_user_email,
                                   password=luckycat_global_config.default_user_password,
                                   api_key=luckycat_global_config.default_user_api_key,
                                   registration_date=datetime.datetime.now(),
                                   roles=[admin_role])
        logging.info('Added default user on first request')


def _add_apikey_handler(security, user_datastore):
    @security.login_manager.request_loader
    def load_user_from_request(request):
        api_key = request.headers.get('Authorization')
        if api_key:
            user = user_datastore.find_user(api_key=api_key)
            if user:
                return user

    return None


def add_flask_security(app):
    with app.app_context():
        app.config['SECURITY_UNAUTHORIZED_VIEW'] = '/'
        app.config['SECRET_KEY'] = luckycat_global_config.secret_key
        app.config['SECURITY_PASSWORD_SALT'] = luckycat_global_config.secret_key

        user_datastore = MongoEngineUserDatastore(db, User, Role)
        security = Security(app, user_datastore)
        create_default_user_and_roles(user_datastore)
        _add_apikey_handler(security, user_datastore)
