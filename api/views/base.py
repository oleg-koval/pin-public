from api.utils import api_response

from mypinnings.database import connect_db

db = connect_db()


class BaseAPI(object):
    """
        Base class for API handler
    """
    def GET(self):
        """
            Wrong HTTP method for API handling
        """
        status = 405
        error_code = "Method Not Allowed"
        data = {}
        response = api_response(data, status=status, error_code=error_code)
        return response

    def POST(self):
        """
            Handler for API call. Must be overriden
        """
        raise NotImplemented

    def authenticate_by_token(self, client_token):
        """
            Get user_id by client token
        """
        user = db.select('users', {"logintoken": client_token}, where="logintoken=$logintoken")
        if len(user)>0:
            return int(user.list()[0]['id'])
        else:
            if client_token is None:
                error_code = "Not received client token"
            else:
                error_code = "Wrong client token"
            return self.access_denied(error_code)

    def access_denied(self, error_code="Default error: access_denied"):
        """
            Access denied errors
        """
        data = {}
        status = 405
        return api_response(data=data, status=status, error_code=error_code)
