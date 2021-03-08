import requests, json
from flask import current_app
from pprint import pprint


def create_subscriber(email):
    url = "https://base.mailerlite.com/base/v2/groups/106463104/subscribers"

    data = {
        'email': email,
    }

    payload = json.dumps(data)

    headers = {
        'content-type': "application/json",
        'x-mailerlite-apikey': current_app.config.get('MAILERLITE_API_KEY')
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    pprint(response.status_code)

    if response.status_code == 200:
        return True
    return False


def get_groups():
    url = "https://base.mailerlite.com/base/v2/groups"

    headers = {
        'content-type': "application/json",
        'x-mailerlite-apikey': current_app.config.get('MAILERLITE_API_KEY')
    }

    response = requests.request("GET", url, headers=headers)

    print(response.text)
