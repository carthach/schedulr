from flask import Blueprint, render_template, flash
from app.extensions import cache, timeout
from config import settings
import uuid
from app.extensions import db, csrf
from flask import redirect, url_for, request, current_app
from flask_login import current_user, login_required
from flask_cors import cross_origin

page = Blueprint('page', __name__, template_folder='templates')


@page.route('/', methods=['GET', 'POST'])
@cross_origin()
def home():
    if current_user.is_authenticated:
        return redirect(url_for('user.availability'))

    if current_app.config.get('BETA'):
        return render_template('page/landing.html', success=False)

    return render_template('page/index.html', plans=settings.STRIPE_PLANS)


@page.route('/subscribe', methods=['GET', 'POST'])
@cross_origin()
def subscribe():
    if request.method == 'POST':
        if 'email' in request.form:
            email = request.form['email']
            from app.blueprints.contact.mailerlite import create_subscriber
            if create_subscriber(email):
                return render_template('page/landing.html', success=True)
    return redirect(url_for('page.home'))


@page.route('/terms')
@cross_origin()
def terms():
    return render_template('page/terms.html')


@page.route('/privacy')
@cross_origin()
def privacy():
    return render_template('page/privacy.html')

