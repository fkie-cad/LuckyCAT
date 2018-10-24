import random
import string
import logging
from flask import Blueprint, render_template, request, flash
from flask_security import login_required, current_user, utils

from luckycat.database.models.User import User

users = Blueprint('users', __name__)

API_KEY_LENGTH = 32

def generate_api_key():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(API_KEY_LENGTH))

def correct_password(email, password):
    user = User.objects.get(email=email)
    return utils.verify_password(password, user.password)

def change_password(email, new_password):
    user = User.objects.get(email=email)
    user.update(password=utils.hash_password(new_password))

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

