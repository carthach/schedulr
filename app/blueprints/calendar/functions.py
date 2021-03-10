from app.extensions import db
import pytz
import google
import datetime
import dateutil.parser
from pprint import pprint
import itertools
from flask import current_app
from sqlalchemy import and_, exists
from app.blueprints.base.functions import print_traceback
from app.blueprints.calendar.google.calendar import create_calendar_service, refresh_token
from app.blueprints.calendar.models.account import Account
from app.blueprints.calendar.models.calendar import Calendar
from googleapiclient.errors import HttpError


def get_availability(accounts, date, tz):
    busy = get_busy(accounts, date, tz)
    pprint(busy)

    if not busy:
        return None


def get_busy(accounts, date=None, tz=None):
    busy = list()
    keyfunc = lambda d: next(iter(d.values()))
    accounts = [{'account': k, 'calendars': [{'id': j['id']} for j in v]} for k, v in
                itertools.groupby(sorted(accounts, key=keyfunc), key=lambda x: x['account'])]
    try:
        for account in accounts:
            a = Account.query.filter(Account.imported_account_id == account['account']).scalar()
            service = create_calendar_service(a.token, a.refresh_token)

            # Get the user's calendar time zone if it doesn't exist
            if not tz or not date:
                tz_string = service.settings().get(setting='timezone').execute()['value']
                tz = datetime.datetime.now(pytz.timezone(tz_string)).strftime('%z')

                time_min = datetime.datetime.now(pytz.timezone(tz_string)).strftime('%Y-%m-%dT00:00:00%z')
                time_max = datetime.datetime.now(pytz.timezone(tz_string)).strftime('%Y-%m-%dT23:59:59%z')
            else:
                time_min = date + "T00:00:00" + tz
                time_max = date + "T23:59:59" + tz

            for calendar in account['calendars']:
                events = service.events().list(calendarId=calendar['id'], timeZone=tz,
                                               timeMin=time_min, timeMax=time_max,
                                               singleEvents=True, orderBy='startTime').execute()

                if events and 'items' in events:
                    # pprint(events)
                    for event in events['items']:
                        if 'end' in event and 'start' in event and 'dateTime' in event['start'] and 'dateTime' in event['end']:
                            busy.append({'start': event['start']['dateTime'].replace('T', ' '), 'end': event['end']['dateTime'].replace('T', ' ')})

        return busy
    except HttpError as e:
        print(e)
    except Exception as e:
        print_traceback(e)
    return None


def get_calendars_for_accounts(accounts):
    return [{'id': x.imported_account_id,
             'account': x.email,
             'calendars': get_calendar_list_from_db(x)} for x in accounts]


def create_calendars_in_db(account_id, user_id, token, refresh):
    calendars = get_calendar_list_from_api(token, refresh)
    existing_primary = db.session.query(exists().where(and_(Calendar.primary.is_(True), Calendar.user_id == user_id))).scalar()
    for calendar in calendars:
        # If the calendar exists, don't import it again!
        if db.session.query(exists().where(and_(Calendar.imported_calendar_id == calendar['id'], Calendar.account_id == account_id))).scalar():
            continue

        c = Calendar()
        c.user_id = user_id
        c.account_id = account_id
        c.imported_calendar_id = calendar['id']
        c.name = calendar['name']
        c.primary = False if existing_primary else calendar['primary']
        c.imported_primary = calendar['primary']

        c.save()


def get_calendar_list_from_db(account):
    calendars = Calendar.query.filter(Calendar.account_id == account.account_id).all()
    return [{'name': c.name, 'id': c.imported_calendar_id,
             'calendar_id': c.calendar_id, 'primary': c.primary} for c in calendars]


def get_calendar_list_from_api(token, refresh):
    calendars = list()

    try:
        service = create_calendar_service(token, refresh)

        calendar_list = service.calendarList().list().execute()

        for cal in calendar_list['items']:
            primary = True if 'primary' in cal and cal['primary'] else False
            calendars.append({'name': cal['summary'],
                              'id': cal['id'],
                              'primary': primary})

        return calendars
    except google.auth.exceptions.RefreshError:
        return refresh_token(refresh)


def get_calendar_id_list(token, refresh):
    calendar_ids = list()

    try:
        service = create_calendar_service(token, refresh)

        calendar_list = service.calendarList().list().execute()
        for cal in calendar_list['items']:
            calendar_ids.append(cal['id'])

        return calendar_ids
    except google.auth.exceptions.RefreshError:
        return refresh_token(refresh)


def get_calendar_ids_for_accounts(accounts):
    calendar_ids = list()
    for account in accounts:
        for calendar in get_calendar_id_list(account.token, account.refresh_token):
            calendar_ids.append({'account': account.imported_account_id, 'id': calendar})

    return calendar_ids


def update_primary_calendar(primary, user_id):
    try:
        calendars = Calendar.query.filter(Calendar.user_id == user_id).all()
        if calendars is None:
            return

        for calendar in calendars:
            calendar.primary = False if not (str(calendar.calendar_id) == primary['id']) else True
            calendar.save()
    except Exception:
        return


def get_events(calendar):
    events = list()
    return events


def create_event_on_calendar(user, **data):
    try:
        calendar = Calendar.query.filter(and_(Calendar.user_id == user.id, Calendar.primary.is_(True))).scalar()
        if calendar is None:
            calendar = Calendar.query.filter(and_(Calendar.user_id == user.id, Calendar.imported_primary.is_(True))).scalar()

        account = Account.query.filter(Account.account_id == calendar.account_id).scalar()
        if account is None:
            return False

        # Format the event description
        if 'zoom' in data and data['zoom']:
            description = 'Zoom link:\n' + data['zoom'] + '\n\n' + data['notes']
        else:
            description = data['notes']

        # Get the end time
        end_time = get_end_time(data['event_datetime'], data['duration_minutes'], data['tz_offset'])

        e = {'summary': current_app.config.get('SITE_NAME') + ' meeting with ' + data['requester_name'],
             'description': description,
             'start': {'dateTime': data['event_datetime'], 'timeZone': data['tz_name']},
             'end': {'dateTime': end_time, 'timeZone': data['tz_name']},
             'attendees': [{'email': data['requester_email']},
                           {'email': user.email}]
             }

        pprint(e)

        service = create_calendar_service(account.token, account.refresh_token)
        event = service.events().insert(calendarId=calendar.imported_calendar_id, body=e).execute()
        print('Event created: %s' % (event.get('htmlLink')))

        # TODO: Create the event in the events table
        # e = Event(u.id, None, **data)
        # e.save()

        # TODO: Send the confirmation email
        return True
    except Exception as e:
        print_traceback(e)
        return False


def get_end_time(time_string, duration, tz_offset):
    try:
        dt = dateutil.parser.isoparse(time_string)
        return (dt + datetime.timedelta(minutes=int(duration))).strftime('%Y-%m-%dT%H:%M:%S') + tz_offset
    except Exception as e:
        print_traceback(e)
        return None
