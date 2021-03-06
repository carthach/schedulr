import pytz
import google
import datetime
from pprint import pprint
import itertools
from app.blueprints.base.functions import print_traceback
from app.blueprints.calendar.google.calendar import create_calendar_service, refresh_token
from app.blueprints.calendar.models.account import Account
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
            a = Account.query.filter(Account.calendar_account_id == account['account']).scalar()
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


def get_calendar_list(token, refresh):
    calendars = list()

    try:
        service = create_calendar_service(token, refresh)

        calendar_list = service.calendarList().list().execute()
        for cal in calendar_list['items']:
            calendars.append({'name': cal['summary'],
                              'id': cal['id']})

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
            calendar_ids.append({'account': account.calendar_account_id, 'id': calendar})

    return calendar_ids


def get_events(calendar):
    events = list()
    return events


def create_event(calendar, **data):
    return