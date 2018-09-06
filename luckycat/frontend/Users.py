from flask import Blueprint, render_template
from flask_security import login_required

users = Blueprint('users', __name__)


@users.route('/user/profile', methods=['GET'])
@login_required
def show_user_profile():
    # TODO
    return render_template("user_profile.html", user={})
