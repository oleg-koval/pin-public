import requests
import json
import urlparse
from mypinnings import database
from mypinnings.conf import settings


def api_request(url, method="GET", data=None):
    """
    Sends http request to api server and returns server response in json,
    or none, if http status_code of the response is not 200
    """
    url = urlparse.urljoin(settings.API_URL, url)

    if method == "GET":
        result = requests.get(
            url,
            data=data
        )

    if method == "POST":
        result = requests.post(
            url,
            data=data
        )
    data = None

    if result.status_code == 200:
        data = json.loads(result.content)

    if not data:
        data = {}
        data['status'] = 500
        data['error_code'] = "Internal server error."

    return data


def convert_to_id(logintoken):
    '''
    Returns id of user by logintoken.
    '''
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
    '''
    Returns logintoken of user by id.
    '''
    user = database.get_db().select(
        'users',
        {"id": id},
        where="id=$id"
    )
    if len(user) > 0:
        return user.list()[0]['logintoken']
    else:
        return None
