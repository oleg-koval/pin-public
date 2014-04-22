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

    def authenticate_by_token(self, logintoken):
        """Authenticates user by given logintoken

        Returns:
        status - flag set to True in case if user was successfully logged in
        user_dict - dictionary with users  profile data (if login success)
        access_denied - if login failure
        """
        success = False
        user = db.select(
            'users',
            {"logintoken": logintoken},
            where="logintoken=$logintoken"
        )
        if len(user) > 0:
            success = True
            return success, user.list()[0]
        else:
            if logintoken is None:
                error_code = "Not received login token"
            else:
                error_code = "Wrong login token"
            return success, self.access_denied(error_code)

    def access_denied(self, error_code="Default error: access_denied"):
        """
        Access denied errors
        """
        data = {}
        status = 405
        return api_response(data=data, status=status, error_code=error_code)
