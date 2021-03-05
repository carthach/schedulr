from flask import (
    Blueprint,
    redirect,
    request,
    flash,
    Markup,
    url_for,
    render_template,
    current_app,
    json,
    jsonify,
    session)
from flask_login import (
    login_required,
    login_user,
    current_user,
    logout_user)

import time
import random
import requests
from pprint import pprint
from operator import attrgetter
from flask_cors import cross_origin
from flask_paginate import Pagination, get_page_args
from lib.safe_next_url import safe_next_url
from app.blueprints.user.decorators import anonymous_required

# Functions
from app.blueprints.calendar.functions import get_availability, get_calendar_list, get_busy, get_calendar_ids_for_accounts

# Models
from app.blueprints.user.models.user import User
from app.blueprints.calendar.models.account import Account
from app.blueprints.calendar.models.event_type import EventType
from app.blueprints.calendar.models.event import Event
from app.blueprints.user.forms import (
    SignupForm,
    LoginForm,
    BeginPasswordResetForm,
    PasswordResetForm,
    WelcomeForm,
    UpdateCredentials)

from app.extensions import cache, csrf, timeout, db
from importlib import import_module
from sqlalchemy import or_, and_, exists, inspect, func

user = Blueprint('user', __name__, template_folder='templates')
use_username = False


"""
User
"""


# Login and Credentials -------------------------------------------------------------------
@user.route('/login', methods=['GET', 'POST'])
@anonymous_required()
@csrf.exempt
def login():
    form = LoginForm(next=request.args.get('next'))

    if form.validate_on_submit():
        u = User.find_by_identity(request.form.get('identity'))

        if u and u.is_active() and u.authenticated(password=request.form.get('password')):

            if login_user(u, remember=True) and u.is_active():
                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))

                u.update_activity_tracking(request.remote_addr)

                next_url = request.form.get('next')

                if next_url == url_for('user.login') or next_url == '' or next_url is None:
                    # Take them to the settings page
                    next_url = url_for('user.calendar')

                if next_url:
                    return redirect(safe_next_url(next_url), code=307)

                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
            else:
                flash('This account has been disabled.', 'error')
        else:
            flash('Your username/email or password is incorrect.', 'error')

    else:
        if len(form.errors) > 0:
            print(form.errors)

    return render_template('user/login.html', form=form)


'''
Signup with an account
'''


@user.route('/signup', methods=['GET', 'POST'])
@anonymous_required()
@csrf.exempt
def signup():
    from app.blueprints.base.functions import print_traceback
    form = SignupForm()

    try:
        if form.validate_on_submit():
            if db.session.query(exists().where(User.email == request.form.get('email'))).scalar():
                flash(Markup("There is already an account using this email. Please use another or <a href='" + url_for(
                    'user.login') + "'><span class='text-indigo-700'><u>login</span></u></a>."), category='error')
                return redirect(url_for('user.signup'))

            u = User()

            form.populate_obj(u)
            u.password = User.encrypt_password(request.form.get('password'))
            u.role = 'member'

            # Save the user to the database
            u.save()

            if login_user(u):
                # from app.blueprints.user.tasks import send_owner_welcome_email
                # from app.blueprints.contact.mailerlite import create_subscriber

                # send_owner_welcome_email.delay(current_user.email)
                # create_subscriber(current_user.email)

                # Log the user in
                flash("You've successfully signed up!", 'success')
                return redirect(url_for('user.events'))
    except Exception as e:
        print_traceback(e)

    return render_template('user/signup.html', form=form)


@user.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('user.login'))


@user.route('/account/begin_password_reset', methods=['GET', 'POST'])
@anonymous_required()
def begin_password_reset():
    form = BeginPasswordResetForm()

    if form.validate_on_submit():
        u = User.initialize_password_reset(request.form.get('identity'))

        flash('An email has been sent to {0}.'.format(u.email), 'success')
        return redirect(url_for('user.login'))

    return render_template('user/begin_password_reset.html', form=form)


@user.route('/account/password_reset', methods=['GET', 'POST'])
@anonymous_required()
def password_reset():
    form = PasswordResetForm(reset_token=request.args.get('reset_token'))

    if form.validate_on_submit():
        u = User.deserialize_token(request.form.get('reset_token'))

        if u is None:
            flash('Your reset token has expired or was tampered with.',
                  'error')
            return redirect(url_for('user.begin_password_reset'))

        form.populate_obj(u)
        u.password = User.encrypt_password(request.form.get('password'))
        u.save()

        if login_user(u):
            flash('Your password has been reset.', 'success')
            return redirect(url_for('user.settings'))

    return render_template('user/password_reset.html', form=form)


@user.route('/settings/update_credentials', methods=['GET', 'POST'])
@login_required
def update_credentials():
    form = UpdateCredentials(current_user, uid=current_user.id)

    if form.validate_on_submit():
        name = request.form.get('name', '')
        username = request.form.get('username', '')
        new_password = request.form.get('password', '')
        current_user.email = request.form.get('email')

        if new_password:
            current_user.password = User.encrypt_password(new_password)

        current_user.name = name
        current_user.username = username
        current_user.save()

        flash('Your credentials have been updated.', 'success')
        return redirect(url_for('user.settings'))

    return render_template('user/update_credentials.html', form=form)


"""
Calendars
"""


@user.route('/calendar/', methods=['GET', 'POST'])
@user.route('/calendar/<event_id>', methods=['GET'])
@user.route('/calendar/<username>/<tag>', methods=['GET'])
@csrf.exempt
@cross_origin()
def calendar(event_id=None, username=None, tag=None):
    load_server_side = False
    busy = list()
    if event_id is not None:
        event_type = EventType.query.filter(EventType.event_type_id == event_id).scalar()

        if event_type is not None:
            if load_server_side:
                user_id = event_type.user_id
                accounts = Account.query.filter(Account.user_id == user_id).all()

                ids = get_calendar_ids_for_accounts(accounts)
                busy = get_busy(ids)

            return render_template('user/calendar.html', current_user=current_user, event_type=event_type, busy=busy, loadServerSide=load_server_side)
    elif username is not None and tag is not None:
        u = User.query.filter(User.username == username).scalar()
        if u is None:
            return redirect(url_for('user.events'))

        event_type = EventType.query.filter(and_(EventType.user_id == u.id, EventType.tag == tag)).scalar()

        if event_type is not None:
            if load_server_side:
                user_id = u.id
                accounts = Account.query.filter(Account.user_id == user_id).all()

                ids = get_calendar_ids_for_accounts(accounts)
                busy = get_busy(ids)

            return render_template('user/calendar.html', current_user=current_user, event_type=event_type,
                                   busy=busy, loadServerSide=load_server_side)

    return redirect(url_for('user.events'))


@user.route('/availability/', methods=['GET', 'POST'])
@csrf.exempt
@login_required
@cross_origin()
def availability():
    a = Account.query.filter(Account.user_id == current_user.id).all()
    accounts = [{'id': x.calendar_account_id, 'account': x.email, 'calendars': get_calendar_list(x.token, x.refresh_token)} for x in a]
    if any(d['calendars'] == -1 for d in accounts):
        flash('There was a problem getting calendars. Please try again.', 'error')
        return redirect(url_for('user.availability'))

    return render_template('user/availability.html', current_user=current_user, accounts=accounts)


@user.route('/update_availability/', methods=['POST'])
@csrf.exempt
@login_required
@cross_origin()
def update_availability():
    if request.method == 'POST':
        accounts = json.loads(request.form.get('calendar_ids'))
        date = request.form['date']
        tz = request.form['tz_offset']

        busy = get_busy(accounts, date, tz)
        return jsonify({'success': True, 'busy': busy})
    return jsonify({'error': 'Error'})


@user.route('/get_busy_times/', methods=['POST'])
@csrf.exempt
@login_required
@cross_origin()
def get_busy_times():
    if request.method == 'POST':
        if 'user_id' in request.form and 'date' in request.form and 'tz_offset' in request.form:
            user_id = request.form['user_id']
            date = request.form['date']
            tz = request.form['tz_offset']

            accounts = Account.query.filter(Account.user_id == user_id).all()

            ids = get_calendar_ids_for_accounts(accounts)
            busy = get_busy(ids, date, tz)

            return jsonify({'success': True, 'busy': busy})
    return jsonify({'error': 'Error'})


@user.route('/get_calendars/', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def get_calendars():
    accounts = Account.query.filter(Account.user_id == current_user.id).all()
    for account in accounts:
        calendars = get_calendar_list(account.token, account.refresh_token)

    return redirect(url_for('user.availability'))


@user.route('/add_calendar/', methods=['GET', 'POST'])
@csrf.exempt
@login_required
@cross_origin()
def add_calendar():
    from app.blueprints.calendar.google.calendar import authorize

    auth_url = authorize()
    return redirect(auth_url)

"""
Events
"""


@user.route('/events/', methods=['GET', 'POST'])
@user.route('/events/<event_type_id>', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def events(event_type_id=None):
    if event_type_id is not None:
        event_type = EventType.query.filter(EventType.event_type_id == event_type_id).scalar()
        return render_template('user/event_type.html', current_user=current_user, event_type=event_type)
    else:
        event_types = EventType.query.filter(EventType.user_id == current_user.id).all()
        event_types.sort(key=lambda x: x.created_on)
        return render_template('user/events.html', current_user=current_user, event_types=event_types)


@user.route('/confirm_event', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def confirm_event():
    if request.method == 'POST':
        if 'name' in request.form and 'email' in request.form and 'duration-minutes' in request.form \
                and 'datetime' in request.form and 'date' in request.form and 'start-time' in request.form \
                and 'tz-offset' in request.form and 'event-type-id' in request.form:

            # Get the event type from the database
            event_type = EventType.query.filter(EventType.event_type_id == request.form['event-type-id']).scalar()
            if event_type is None:
                flash("There was an error creating this event. Please try again.", 'error')
                return redirect(url_for('user.events'))

            # Get the user that owns this event type
            u = User.query.filter(User.id == event_type.user_id).scalar()
            if u is None:
                flash("There was an error creating this event. Please try again.", 'error')
                return redirect(url_for('user.events'))

            data = {'event_type_id': request.form['event-type-id'],
                    'requester_name': request.form['name'],
                    'requester_email': request.form['email'],
                    'date': request.form['date'],
                    'event_datetime': request.form['datetime'],
                    'start_time': request.form['start-time'],
                    'tz_offset': request.form['tz-offset'],
                    'duration_minutes': request.form['duration-minutes'],
                    'zoom': request.form['zoom'],
                    'notes': request.form['notes']
            }

            e = Event(u.id, None, **data)
            e.save()

            flash("Successfully created your meeting! You'll get an email confirmation soon.", 'success')
    return redirect(url_for('user.events'))


"""
Event Types
"""


@user.route('/create_event_type/', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def create_event_type():
    event_type = EventType(user_id=current_user.id)
    if event_type is not None:
        return render_template('user/event_type.html', current_user=current_user, event_type=event_type)
    else:
        return redirect(url_for('user.events'))


@user.route('/save_event_type', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def save_event_type():
    if request.method == 'POST':
        if 'event_type_id' in request.form and 'name' in request.form \
                and 'duration' in request.form and 'description' in request.form and 'tag' in request.form:
            event_type_id = request.form['event_type_id']
            name = request.form['name']
            duration = request.form['duration']
            description = request.form['description']
            tag = request.form['tag']

            if tag.endswith('-'):
                tag = tag[:-1]

            # Create a new event type
            if not db.session.query(exists().where(EventType.event_type_id == event_type_id)).scalar():
                data = {
                    'title': name,
                    'description': description,
                    'duration_minutes': duration,
                    'tag': tag
                }

                e = EventType(user_id=current_user.id, **data)
                e.event_type_id = event_type_id
                e.save()
            else:
                e = EventType.query.filter(EventType.event_type_id == event_type_id).scalar()
                if e is not None:
                    e.title = name
                    e.description = description
                    e.duration_minutes = duration
                    e.tag = tag
                    e.save()
    return redirect(url_for('user.events'))


# @user.route('/start', methods=['GET', 'POST'])
# @user.route('/start/<shop_url>', methods=['GET', 'POST'])
# @login_required
# def start(shop_url):
#     if not current_user.is_authenticated:
#         return redirect(url_for('user.login'))
#
#     shop = Shop.query.filter(Shop.url == shop_url).scalar()
#     if shop is None:
#         return redirect(url_for('user.calendar'))
#
#     pending = Sync.query.filter(and_(Sync.destination_url == shop_url, Sync.active.is_(False))).all()
#     plans = Plan.query.all()
#
#     return render_template('user/start.html', current_user=current_user, shop_id=shop.shop_id, pending=pending, plans=plans)


# Settings -------------------------------------------------------------------
@user.route('/settings', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def settings():
    return render_template('user/settings.html', current_user=current_user)


# Actions -------------------------------------------------------------------
@user.route('/get_private_key', methods=['GET', 'POST'])
@csrf.exempt
@cross_origin()
def get_private_key():
    try:
        if request.method == 'POST':
            if 'domain_id' in request.form and 'user_id' in request.form:
                domain_id = request.form['domain_id']
                user_id = request.form['user_id']

                from app.blueprints.base.functions import get_private_key
                key = get_private_key(domain_id, user_id)
                return jsonify({'success': True, 'key': key})
    except Exception as e:
        return jsonify({'success': False})
    return jsonify({'success': False})


# Contact us -------------------------------------------------------------------
@user.route('/contact', methods=['GET', 'POST'])
@csrf.exempt
def contact():
    if request.method == 'POST':
        from app.blueprints.user.tasks import send_contact_us_email
        send_contact_us_email.delay(request.form['email'], request.form['message'])

        flash('Thanks for your email! You can expect a response shortly.', 'success')
        return redirect(url_for('user.contact'))
    return render_template('user/contact.html', current_user=current_user)
