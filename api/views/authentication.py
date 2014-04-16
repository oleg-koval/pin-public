import web

from api.utils import api_response, save_api_request
from api.views.base import BaseAPI

import mypinnings
from mypinnings.database import connect_db
from mypinnings.auth import authenticate_user_email, authenticate_user_username, login_user

db = connect_db()
sess = mypinnings.session.sess


class Auth(BaseAPI):
    def POST(self):
        """
            Authentification method for API
        """
        request_data = web.input()
        save_api_request(request_data)
        if not self.is_valid():
            return self.not_enough_data()
        email = request_data.get("email")
        password = request_data.get("password")
        user_id = self.is_authenticated(email, password)
        if not user_id:
            return self.access_denied("Login or password wrong")
        user = self.get_user(user_id)
        login_user(sess, user_id)
        data = {
            "token": user.get("logintoken"),
            "user_id": user.get("id"),
            "email": user.get("email")
        }
        response = api_response(data, csid_from_client=request_data.get("csid_from_client"),
            csid_from_server=user.get('seriesid'))
        return response

    def get_user(self, user_id):
        """
            Get user record by user_id
        """
        users = db.select('users', {"id": user_id}, where="id=$id")
        if len(users) > 0:
            return users.list()[0]
        return False

    def is_authenticated(self, email, password):
        """
            Check if user is is_authenticated
        """
        user_id = authenticate_user_email(email, password)
        if not user_id:
            user_id = authenticate_user_username(email, password)
        return user_id

    def is_valid(self):
        """
            Check it request parameters are valid
        """
        data = web.input()
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return False
        return True

    def not_enough_data(self):
        """
            Response if not enough data in request
        """
        data = {}
        status = 405
        error_code = "Not enough parameters"
        return api_response(data=data, status=status, error_code=error_code)
