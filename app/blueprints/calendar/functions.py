from app.blueprints.calendar.google.calendar import create_calendar_service


def get_availability(calendars):
    availability = list()
    return availability


def get_calendar_list(token, refresh):
    calendars = list()

    service = create_calendar_service(token, refresh)

    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list['items']:
        calendars.append({'name': cal['summary'],
                          'id': cal['id']})

    return calendars


def get_events(calendar):
    events = list()
    return events


def create_event(calendar):
    return