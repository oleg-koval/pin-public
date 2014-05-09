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

        logintoken = request_data.get('logintoken')
        csid_from_client = request_data.get('csid_from_client')
        user_status, user = self.authenticate_by_token(logintoken)

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']

        notification_list = db.select('notifs', {"user_id": user['id']}, 
            where='user_id=$user_id', order="timestamp DESC")
        data = notification_list.list()

        response = api_response(data=data,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response
