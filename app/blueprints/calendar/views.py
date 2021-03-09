from flask import Blueprint, redirect, url_for, flash
from app.extensions import csrf

calendar = Blueprint('calendar', __name__, template_folder='templates')


@calendar.route('/google_auth/', methods=['GET', 'POST'])
@csrf.exempt
def google_auth():
    from app.blueprints.calendar.google.calendar import get_credentials

    result = get_credentials()

    if result:
        flash("Successfully added your account.", 'success')
    elif result == 1:
        flash("This account has already been connected.", 'warning')
    else:
        flash("There was a problem adding your account. Please try again.", 'danger')

    return redirect(url_for('user.availability'))

