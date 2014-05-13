import web
import random

from api.utils import api_response, save_api_request
from api.views.base import BaseAPI

import mypinnings
from mypinnings.database import connect_db
from mypinnings.auth import authenticate_user_email, authenticate_user_username, login_user
from mypinnings.register import add_default_lists, send_activation_email
from mypinnings import auth
from mypinnings import session


db = connect_db()


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
        from ser import sess
        login_user(sess, user_id)
        data = {
            "user_id": user.get("id"),
            "email": user.get("email")
        }
        response = api_response(data, csid_from_client=request_data.get("csid_from_client"),
            csid_from_server=user.get('seriesid'), client_token=user.get('logintoken'))
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


class Register(BaseAPI):
    """
        Register method for API
    """
    def POST(self):
        """
            Method register must receive next additional params:

            uname - user name
            pwd - user password
            email - user email
            complete_name - user first name
            language - user language

            output response also included:

            login_token for new user,
            hashed_activation for activation-email
        """
        request_data = web.input()
        data = {}

        save_api_request(request_data)
        csid_from_client = request_data.get('csid_from_client')

        uname = request_data.get("uname")
        pwd = request_data.get("pwd")
        email = request_data.get("email")
        complete_name = request_data.get("complete_name")
        # last_name = request_data.get("last_name")
        language = str(request_data.get("language", "en"))

        status_error = 200
        error_code = ""

        status, error_code = self.register_validation(uname, pwd, 
                                                      email, complete_name)
        if status:
            activation = random.randint(1, 10000)
            hashed = hash(str(activation))

            user_id = auth.create_user(email, pwd, name=complete_name, username=uname,
                                       activation=activation, locale=language)

            add_default_lists(user_id)
            send_activation_email(email, hashed, user_id)
            sess = session.get_session()
            auth.login_user(sess, user_id)
            user = db.select('users', {'id': user_id}, where='id=$id')[0]
            login_token = user.get('logintoken')
            data.update({
                "logintoken": login_token,
                # "hashed_activation": hashed,
                })
        else:
            status_error = 405

        response = api_response(
            data,
            status=status_error,
            error_code=error_code,
            csid_from_client=csid_from_client,)

        return response

    def register_validation(self, uname, pwd, email, complete_name):
        """
            Validation entered user's request parameters:
            name, password,
            email, complete_name
        """
        request_params = {
            "uname": uname,
            "pwd": pwd,
            "email": email,
            "complete_name": complete_name,
        }
        error_code = ""
        for field, value in request_params.items():
            if value is None:
                error_code = "Not entered necessary parameter '"
                error_code += str(field)+"' for register method SignUp APIs"
                return False, error_code

        pwd_status, error_code = auth.check_password(uname, pwd, email)
        if not pwd_status:
            return False, error_code

        if auth.email_exists(email):
            error_code = 'Sorry, that email already exists.'
            return False, error_code

        if auth.username_exists(uname):
            error_code = 'Sorry, that username already exists.'
            return False, error_code

        return True, error_code

class Confirmuser(BaseAPI):
    """Confirmation of user email

    Response:
        status = 200 or error_code
    """
    def POST(self):
        """
        Compare given activation code with existed. 
        If they are identical - activate new user
        """
        status_error = 200
        error_code = ""
        data = {}

        request_data = web.input()
        save_api_request(request_data)
        login_token = request_data.get("logintoken")
        hashed_activation = request_data.get("hashed_activation")
        csid_from_client = request_data.get('csid_from_client')

        status, response_or_user = self.authenticate_by_token(login_token)
        if not status:
            return response_or_user

        user = db.select('users', {'id': response_or_user['id']}, where='id=$id')[0]
        csid_from_server = user.get('seriesid')
        activation = user.get('activation')
        hashed = hash(str(activation))
 
        if hashed_activation:
            if hashed != int(hashed_activation):
                status_error = 405
                error_code = "wrong activation code given from user"
        else:
            status_error = 405
            error_code = "Not found hashed_activation field in request"

        if status_error == 200:
            db.update('users', activation=0,
                      vars={'id': response_or_user["id"]}, where="id=$id")

        response = api_response(
            data,
            status=status_error,
            error_code=error_code,
            csid_from_client=csid_from_client,
            csid_from_server=csid_from_server,)

        return response


        