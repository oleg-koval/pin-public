import requests
import json

from mypinnings import database
from mypinnings.conf import settings


def api_request(url, method="GET", data=None):
    url = settings.API_URL + url

    if method == "GET":
        result = requests.get(
            url
        )

    if method == "POST":
        result = requests.post(
            url,
            data=data
        )

    data = None
    if result.status_code == 200:
        data = json.loads(result.content)

    return data


def convert_to_id(logintoken):
    user = database.get_db().select(
        'users',
        {"logintoken": logintoken},
        where="logintoken=$logintoken"
    )

    if len(user) > 0:
        return user.list()[0]['id']
    else:
        return None


def convert_to_logintoken(id):
    user = database.get_db().select(
        'users',
        {"id": id},
        where="id=$id"
    )
    if len(user) > 0:
        return user.list()[0]['logintoken']
    else:
        return None