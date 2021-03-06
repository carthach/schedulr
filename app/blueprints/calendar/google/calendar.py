import requests
import google_auth_oauthlib.flow
from flask import request, current_app, redirect, url_for
from flask_login import current_user
from app.blueprints.calendar.models.account import Account
from app.blueprints.base.functions import print_traceback
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import google.oauth2.credentials
from app.extensions import db
from sqlalchemy import exists, and_


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
        prompt='consent',
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
        # If credentials don't exist, return an error
        if not credentials:
            return False

        # There is a refresh token in the request, so this is a new access (or refreshed access)
        if credentials.refresh_token is not None:
            # Refresh the credentials if they're expired
            if credentials.expired:
                credentials.refresh(Request())

            # This user is already in the database, so we are refreshing the access token.
            if db.session.query(exists().where(Account.imported_account_id == info['id'])).scalar():
                account = Account.query.filter(Account.imported_account_id == info['id']).scalar()
                account.token = credentials.token
                account.refresh_token = credentials.refresh_token
                account.save()

                # Create the calendars in the db for this account
                from app.blueprints.calendar.functions import create_calendars_in_db
                create_calendars_in_db(account.account_id, current_user.id, credentials.token, credentials.refresh_token)
            else:
                account = Account()
                account.user_id = current_user.id
                account.imported_account_id = info['id']
                account.email = info['email']
                account.token = credentials.token,
                account.refresh_token = credentials.refresh_token
                account.save()

                # Create the calendars in the db for this account
                from app.blueprints.calendar.functions import create_calendars_in_db
                create_calendars_in_db(account.account_id, current_user.id, credentials.token, credentials.refresh_token)

            return True
        else:
            # Otherwise the account is already connected
            return 1

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


def refresh_token(refresh):
    try:
        url = 'https://www.googleapis.com/oauth2/v4/token'

        data = {
            'client_id': current_app.config.get('GOOGLE_CLIENT_ID'),
            'client_secret': current_app.config.get('GOOGLE_CLIENT_SECRET'),
            'grant_type': 'refresh_token',
            'refresh_token': refresh
        }

        r = requests.post(url, data=data)

        if r.status_code == 200:
            return 0
        else:
            # Delete the calendar if unable to refresh the token.
            Account.query.filter(Account.refresh_token == refresh).scalar().delete()
            return -1

    except Exception as e:
        print_traceback(e)

        # Delete the calendar if unable to refresh the token.
        Account.query.filter(Account.refresh_token == refresh).scalar().delete()
        return -1


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
