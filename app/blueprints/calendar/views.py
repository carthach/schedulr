from flask import Blueprint, redirect, url_for, flash
from app.extensions import csrf

calendar = Blueprint('calendar', __name__, template_folder='templates')


@calendar.route('/google_auth/', methods=['GET', 'POST'])
@csrf.exempt
def google_auth():
    from app.blueprints.calendar.google.calendar import get_credentials

    result = get_credentials()

    if result == 1:
        flash("This account has already been added.", 'warning')
    elif result:
        flash("Successfully added your calendar.", 'success')
    else:
        flash("There was a problem adding your calendar. Please try again.", 'error')

    return redirect(url_for('user.availability'))

