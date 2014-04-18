""" API views responsible for returing and updating the profile info"""
import web
from datetime import datetime

from api.utils import api_response, save_api_request, api_response
from api.views.base import BaseAPI

from mypinnings import auth
from mypinnings import session
from mypinnings.database import connect_db


db = connect_db()


class BaseUserProfile(BaseAPI):
    """
    General class which holds list of fields used by user profile methods
    """
    def __init__(self):
        self._fields = ['name', 'about', 'city', 'hometown', 'about',
                        'email', 'pic', 'website', 'facebook', 'twitter']
        self._birthday_fields = ['birthday_year', 'birthday_month',
                                 'birthday_day']
        self.required = ['csid_from_client', 'logintoken']

    def is_request_valid(self, request_data):
        """
        Checks if required parameters are in request
        """
        for field in self.required:
            if field not in request_data:
                return False
        return True


class UserInfoUpdate(BaseUserProfile):
    """
    Defines a class responsible for updating user data, inide the profile
    """
    def POST(self):
        """
        Updates profile with fields sent from the client, returns saved fields.

        Can be tested in the following way:
        curl --data "logintoken=UaNxct7bJZ&twitter=1&csid_from_client=1" \
        http://localhost:8080/api/profile/userinfo/update
        """
        request_data = web.input()
        if not self.is_request_valid(request_data):
            return api_response(data={}, status=405,
                                error_code="Required args are missing")
        csid_from_client = request_data.pop('csid_from_client')
        status, user = self.authenticate_by_token(
            request_data.pop('logintoken'))
        # User id contains error code
        if not status:
            return user
        to_insert = {}

        birthday = [value for key, value in request_data.items()
                    if key in self._birthday_fields]

        if len(birthday) in [1, 2]:
            error_code = "Birthday date incomplete"
            return api_response(data={}, status=405, error_code=error_code)
        elif len(birthday) == 3:
            to_insert['birthday'] = datetime.strptime("-".join(birthday),
                                                      "%Y-%d-%m")
        for field in self._fields:
            item = request_data.get(field)
            if item:
                to_insert[field] = item
        db.update('users', where='id = %s' % (user['id']), **to_insert)
        csid_from_server = user['seriesid']
        return api_response(data=request_data,
                            csid_from_client=csid_from_client,
                            csid_from_server=csid_from_server,
                            status=200)


class GetProfileInfo(BaseUserProfile):
    """
    Returns profile information.

    Can be tested this way:
    curl --data "logintoken=UaNxct7bJZ&csid_from_client=123" \
    http://localhost:8080/api/profile/userinfo/get
    """
    def POST(self):
        """
        Returns profile information, requires logintoken

        Can be tested in the following way:
        curl --data "logintoken=UaNxct7bJZ&csid_from_client=123" \
        http://localhost:8080/api/profile/userinfo/get

        """
        request_data = web.input()
        if not self.is_request_valid(request_data):
            return api_response(data={}, status=405,
                                error_code="Required args are missing")
        status, user = self.authenticate_by_token(
            request_data.pop('logintoken'))
        csid_from_client = request_data.pop('csid_from_client')
        # User id contains error code
        if not status:
            return user

        response = {field: user[field] for field in self._fields}

        # Formatting response of birthday_ year, day, month from 'birthday'
        if user['birthday']:
            response['birthday_year'] = user['birthday'].year
            response['birthday_day'] = user['birthday'].day
            response['birthday_month'] = user['birthday'].month
        return api_response(data=response,
                            csid_from_client=csid_from_client,
                            csid_from_server=user['seriesid'],
                            status=200)


class ManageGetList(BaseAPI):
    def POST(self):
        """
        Manage list of user products: share, add, remove
        """
        request_data = web.input(
            image_id_remove_list=[],
            image_id_share_list=[],
            image_id_add_list=[],
        )

        save_api_request(request_data)
        client_token = request_data.get("logintoken")

        status, user = self.authenticate_by_token(client_token)
        # User id contains error code
        if not status:
            return user

        image_id_add_list = map(int, request_data.get("image_id_add_list"))
        add_list_result = []
        if len(image_id_add_list) > 0:
            add_list_result = self.add(user["id"], image_id_add_list)

        image_id_remove_list = map(
            int,
            request_data.get("image_id_remove_list")
        )
        remove_list_result = []
        if len(image_id_remove_list) > 0:
            remove_list_result = self.remove(user["id"], image_id_remove_list)

        image_id_share_list = map(int, request_data.get("image_id_share_list"))
        share_list_result = []
        if len(image_id_share_list) > 0:
            share_list_result = self.share(user["id"], image_id_share_list)

        user = db.select('users', {'id': user_id}, where='id=$id')[0]
        csid_from_server = user.get('seriesid')
        data = {
            "added": add_list_result,
            "removed": remove_list_result,
            "shared": share_list_result,
        }
        response = api_response(data, csid_from_client=request_data.get("csid_from_client"),
            csid_from_server=csid_from_server)

        return response

    def add(self, user_id, add_list):
        """
            Add new products to user profile
        """
        add_list_result = []
        for pin in add_list:
            user_product = {"user_id": user_id, "pin_id": pin}
            exist_product = db.select(
                'user_prefered_pins',
                where=web.db.sqlwhere(user_product)
            )
            if len(exist_product) == 0:
                add_list_result.append(pin)
                db.insert('user_prefered_pins', user_id=user_id, pin_id=pin)
        return add_list_result

    def remove(self, user_id, remove_list):
        """
        Remove products from user profile
        """
        remove_list_result = []
        for pin in remove_list:
            user_product = {"user_id": user_id, "pin_id": pin}
            exist_product = db.select(
                'user_prefered_pins',
                where=web.db.sqlwhere(user_product)
            )
            if len(exist_product) > 0:
                remove_list_result.append(pin)
                db.delete(
                    'user_prefered_pins',
                    where=web.db.sqlwhere(user_product)
                )
        return remove_list_result

    def share(self, user_id, share_list):
        """
        Share products from user profile
        """
        pass


class ChangePassword(BaseAPI):
    def POST(self):
        """
            Change user password and take new client token
        """
        request_data = web.input()
        save_api_request(request_data)
        client_token = request_data.get("client_token")
        user_id = self.authenticate_by_token(client_token)

        old_password = request_data.get("old_password")
        new_password = request_data.get("new_password")
        new_password2 = request_data.get("new_password2")

        user = db.select('users', {'id': user_id}, where='id=$id', what='pw_salt, pw_hash')[0]
        pw_salt = user['pw_salt']
        pw_hash = user['pw_hash']

        if self.passwords_validation(pw_salt, pw_hash, old_password, new_password, new_password2):
            new_password_hash = self.create_password(pw_salt, new_password)
            db.update('users', pw_hash = new_password_hash, vars={'id': user_id}, where="id=$id")

            # re_login user with new password
            sess = session.get_session()
            auth.login_user(sess, user_id)

            user = db.select('users', {'id': user_id}, where='id=$id')[0]
            new_client_token = user.get('logintoken')
            csid_from_server = user.get('seriesid')
            data = {
                "client_token": new_client_token,
            }
            response = api_response(data, csid_from_client=request_data.get("csid_from_client"),
                csid_from_server=csid_from_server)
            return response
        else:
            return self.access_denied("Wrong entered information")

    def passwords_validation(self, pw_salt, pw_hash, old_pwd=None, new_pwd=None, new_pwd2=None):
        """
            Check if new password match with confirmation.
            Check relevance old password.
            Check empty field.
        """
        if new_pwd is None:
            return self.access_denied("New password is empty")

        if old_pwd is None:
            return self.access_denied("Old password is empty")

        if new_pwd != new_pwd2:
            return self.access_denied("Incorrect confirmation new password")

        if str(hash(str(hash(old_pwd)) + pw_salt)) != pw_hash:
            return self.access_denied("Incorrect old password")

        return True

    def create_password(self, pw_salt, new_pwd):
        new_pwd_hash = str(hash(new_pwd))
        new_pwd_hash = str(hash(new_pwd_hash + pw_salt))
        return new_pwd_hash
