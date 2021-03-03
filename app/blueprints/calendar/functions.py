import google
from pprint import pprint
import itertools
from app.blueprints.base.functions import print_traceback
from app.blueprints.calendar.google.calendar import create_calendar_service, refresh_token
from app.blueprints.calendar.models.calendar import Calendar
from googleapiclient.errors import HttpError


def get_availability(calendars, date):
    busy = get_busy_times(calendars, date)

    if not busy:
        return None




def get_busy_times(calendars, date):
    busy = list()
    keyfunc = lambda d: next(iter(d.values()))
    calendars = [{'account': k, 'calendars': [{'id': j['id']} for j in v]} for k, v in
                 itertools.groupby(sorted(calendars, key=keyfunc), key=lambda x: x['account'])]
    try:
        for calendar in calendars:
            c = Calendar.query.filter(Calendar.account_id == calendar['account']).scalar()
            service = create_calendar_service(c.token, c.refresh_token)
            tz = service.settings().get(setting='timezone').execute()
            tz = tz['value'] if 'value' in tz else ''

            freebusy = service.freebusy().query(body=
                                                {"timeMin": date + "T00:00:00.000Z",
                                                 "timeMax": date + "T23:59:59.000Z",
                                                 "timeZone": tz,
                                                 "items": calendar['calendars']
                                                 }).execute()

            pprint(freebusy)
            # There are no busy times, so continue
            if not (freebusy and 'calendars' in freebusy):
                return list()

            c = freebusy['calendars'].keys()
            for k in c:
                if 'busy' in freebusy['calendars'][k]:
                    b = freebusy['calendars'][k]['busy']
                    if len(b) > 0:
                        for item in b:
                            busy.append(item)

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


def get_events(calendar):
    events = list()
    return events


def create_event(calendar):
    return