import web

from api.utils import api_response, save_api_request
from api.views.base import BaseAPI

from mypinnings.database import connect_db

db = connect_db()


class Notification(BaseAPI):
    def POST(self):
        """
            Return list of all notifications sorted by timestamp
        """
        request_data = web.input()
        save_api_request(request_data)
        notification_list = db.select('notifs', order="timestamp DESC")
        data = notification_list.list()
        response = api_response(data)
        return response
