import google_auth_oauthlib.flow
from flask import request, current_app
from flask_login import current_user
from app.blueprints.calendar.models.calendar import Calendar
from app.blueprints.base.functions import print_traceback
from googleapiclient.discovery import build
import google.oauth2.credentials
from app.extensions import db
from sqlalchemy import exists


SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events', 'openid',
          'https://www.googleapis.com/auth/userinfo.email']


def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'credentials.json', scopes=SCOPES)

    flow.redirect_uri = current_app.config.get('GOOGLE_REDIRECT')

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        prompt='select_account',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='false')

    return authorization_url


def get_credentials():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES)
    flow.redirect_uri = current_app.config.get('GOOGLE_REDIRECT')

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Get the credentials
    credentials = flow.credentials

    # Get the account's info to save with the calendar
    info = get_user_info(credentials)

    try:
        if not credentials:
            return False

        # The credentials already exist in the db, so this account has already been added.
        if db.session.query(exists().where(Calendar.account_id == info['id'])).scalar():
            return 1
        else:
            calendar = Calendar()
            calendar.user_id = current_user.id
            calendar.account_id = info['id']
            calendar.email = info['email']
            calendar.token = credentials.token,
            calendar.refresh_token = credentials.refresh_token
            calendar.save()

        return True

    except Exception as e:
        print_traceback(e)
        return False

    # flask.session['credentials'] = {
    #     'token': credentials.token,
    #     'refresh_token': credentials.refresh_token,
    #     'token_uri': credentials.token_uri,
    #     'client_id': credentials.client_id,
    #     'client_secret': credentials.client_secret,
    #     'scopes': credentials.scopes}


def create_calendar_service(token, refresh):
    # scopes = 'https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/calendar.events'

    creds = {'token': token,
             'refresh_token': refresh,
             'token_uri': 'https://oauth2.googleapis.com/token',
             'client_id': current_app.config.get('GOOGLE_CLIENT_ID'),
             'client_secret': current_app.config.get('GOOGLE_CLIENT_SECRET'),
             'scopes': SCOPES}

    credentials = google.oauth2.credentials.Credentials(**creds)

    cal = build('calendar', 'v3', credentials=credentials)

    return cal


def get_service(api, version, credentials):
    return build(api, version, credentials=credentials)


def get_user_info(credentials):
    service = get_service('oauth2', 'v2', credentials)
    user_info = None
    try:
        user_info = service.userinfo().get().execute()
    except Exception as e:
        pass
    if user_info and user_info.get('id'):
        return user_info
    else:
        return None
