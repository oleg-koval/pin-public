import web
import json
import decimal

from mypinnings.database import connect_db
db = connect_db()

def decimal_default(obj):
    """
    Used in order to allow encoding decimal numbers into json
    """
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

def api_response(data, status=200, error_code="", csid_from_server="",
    csid_from_client="", client_token="", notifications={}):
    """
    Function preparation API response
    """
    response = {
        "status": status,
        "error_code": error_code,
        "t_id": "",
        "s_version_id": "1.0",
        "csid_from_client": csid_from_client,
        "csid_from_server": csid_from_server,
        "client_token": client_token,
        "notifications": notifications,
        "data": data
    }
    web.header('Content-Type', 'application/json')
    return json.dumps(response, default=decimal_default)


def save_api_request(request_data):
    """
    Save data from API request
    """
    pass


def photo_id_to_url(photo_id):
    results = db.select('photos',
                        where='id = $id',
                        vars={'id': photo_id})

    if len(results) > 0:
        return results[0]['resized_url']
    return None
