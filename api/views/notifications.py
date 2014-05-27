import web

from api.utils import api_response, save_api_request
from api.views.base import BaseAPI

from mypinnings.database import connect_db, dbget

db = connect_db()


class Notification(BaseAPI):
    def POST(self):
        """
        Return list of user notifications sorted by timestamp
        depeds on user logintoken
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


class CreateNotification(BaseAPI):
    """
    Responsible for notifications creation
    """
    def POST(self):
        """
        Example usage:
        curl --data "csid_from_client=11&user_id=78&msg=message&url=some_url" \
        http://localhost:8080/api/notification/add
        """
        request_data = web.input()
        csid_from_client = request_data.get('csid_from_client', "")
        db.insert('notifs', user_id=request_data["user_id"],
                  message=request_data["msg"],
                  link=request_data["url"])
        return api_response(data={"status": "success"},
                            csid_from_client=csid_from_client,
                            csid_from_server="")

class GetNotification(BaseAPI):
    """
    Allows to get individual notifications
    """
    def POST(self, notification_id):
        """ Method responsible for retuning individual notifications

        :args: logintoken, csid_from_client, notification_id.
        :returns: notification_or_404
        :to_test: curl --data "csid_from_client=1&logintoken=zs4jxj0yM2"\
        http://localhost:8080/api/notification/177
        """
        request_data = web.input()
        save_api_request(request_data)

        logintoken = request_data.get('logintoken')
        csid_from_client = request_data.get('csid_from_client')
        user_status, user = self.authenticate_by_token(logintoken)

        # User id contains error code
        if not user_status:
            return api_response(data={}, status=405,
                                error_code="User was not found")

        csid_from_server = user['seriesid']
        notif = dbget('notifs', notification_id)

        # Do not allow to read notification related to other users
        if int(notif.user_id) != int(user.id):
            return api_response(data={}, status=405,
                                error_code="Access denied")

        # Remove notification which was already reviewed
        db.delete('notifs', where='id = $id', vars={'id': notification_id})
        return api_response(data=notif,
                            csid_from_client=csid_from_client,
                            csid_from_server=csid_from_server)
