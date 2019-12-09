import datetime
import logging
import random
import string

from flask import Blueprint, render_template, request, abort, redirect
from flask_security import login_required, current_user, utils, MongoEngineUserDatastore, roles_required

from luckycat.database.database import db
from luckycat.database.models.Role import Role
from luckycat.database.models.User import User

users = Blueprint('users', __name__)
user_datastore = MongoEngineUserDatastore(db, User, Role)

API_KEY_LENGTH = 32


def generate_api_key():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(API_KEY_LENGTH))


def correct_password(email, password):
    user = User.objects.get(email=email)
    return utils.verify_password(password, user.password)


def change_password(email, new_password):
    user = User.objects.get(email=email)
    user.update(password=utils.hash_password(new_password))


def is_valid_email(email):
    return '@' in email


def is_valid_password(password):
    # TODO improve me
    return len(password) > 5


def user_exists(email):
    return User.objects(email=email).count() != 0


@users.route('/user/profile', methods=['GET', 'POST'])
@login_required
def show_user_profile():
    if request.method == 'GET':
        return render_template("user_profile.html", user=current_user)
    else:
        new_password = request.form['new_password']
        new_password_confirm = request.form['new_password_confirm']
        old_password = request.form['old_password']
        if new_password != new_password_confirm:
            logging.warning('Error: new password did not match')
        elif not correct_password(current_user.email, old_password):
            logging.warning('Error: wrong password')
        else:
            change_password(current_user.email, new_password)
            logging.warning('password change successful')
        return render_template("user_profile.html", user=current_user)


@users.route('/user/manage')
@roles_required('admin')
def manage_user():
    return render_template("user_manage.html", users=User.objects)


@users.route('/user/add', methods=['GET', 'POST'])
@roles_required('admin')
def add_user():
    if request.method == 'GET':
        return render_template("user_add.html", roles=Role.objects)
    else:
        data = request.form
        if not is_valid_email(data.get('email')):
            logging.error('Invalid email address.')
            return redirect('user/manage')

        if user_exists(data.get('email')):
            logging.error('User with email %s does already exist.' % data.get('email'))
            return redirect('user/manage')

        if data.get('password') != data.get('retype_password'):
            logging.error('Passwords do not match.')
            return redirect('user/manage')

        requested_role = Role.objects.get(name=data.get('role'))
        if not requested_role:
            logging.error('Role %s not known' % data.get('role'))
            return redirect('user/manage')

        user_datastore.create_user(email=data.get('email'),
                                   password=data.get('password'),
                                   api_key=generate_api_key(),
                                   roles=[requested_role],
                                   registration_date=datetime.datetime.now())

        logging.warning('Created user %s' % data.get('email'))
        return redirect('user/manage')


@users.route('/user/delete/<user_id>')
@roles_required('admin')
def delete_user(user_id):
    if user_id is None:
        abort(400, description='Invalid user_id')
    else:
        user = User.objects.get(id=user_id)
        if user:
            # TODO check if not current user!
            user.delete()
            # TODO delete all jobs of user
            logging.warning("Deleted user with user_id %s" % user_id)
        return redirect('user/manage')


@users.route('/user/activation/<user_id>')
@roles_required('admin')
def toggle_user_activation(user_id):
    if user_id is None:
        abort(400, description='Invalid user_id')
    else:
        user = User.objects.get(id=user_id)
        if user:
            # TODO check if not current user!
            user.update(active=(not user.active))
            logging.warning("Set activation of user with user_id %s to %r" % (user_id, user.active))
        return redirect('user/manage')
