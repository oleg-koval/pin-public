""" API views responsible for returing and updating the profile info"""
import web
from datetime import datetime

from api.utils import api_response, save_api_request, api_response
from api.views.base import BaseAPI
from api.views.social import share

from mypinnings import auth
from mypinnings import session
from mypinnings.database import connect_db


db = connect_db()


class BaseUserProfile(BaseAPI):
    """
    General class which holds list of fields used by user profile methods
    """
    def __init__(self):
        self._fields = ['id', 'name', 'about', 'city', 'hometown', 'about',
                        'email', 'pic', 'website', 'facebook', 'twitter',
                        'getlist_privacy_level', 'private']
        self._birthday_fields = ['birthday_year', 'birthday_month',
                                 'birthday_day']
        self.required = ['csid_from_client', 'logintoken']

    @staticmethod
    def format_birthday(user, response):
        """
        Composes birthday response, returning year, day and month
        as separate response fields
        """
        if user['birthday']:
            response['birthday_year'] = user['birthday'].year
            response['birthday_day'] = user['birthday'].day
            response['birthday_month'] = user['birthday'].month
        return response


    def is_request_valid(self, request_data):
        """
        Checks if all required parameters are sent from the client.
        Also checks if no extra arguments was passed
        """
        for field in self.required:
            if field not in request_data:
                return False

        for field in request_data:
            # Checking if current field is among the fields we have in the db
            if (field not in self._fields and
                    field not in self._birthday_fields and
                    field not in self.required):
                return False
        return True


class SetPrivacy(BaseUserProfile):
    """
    Allows to set privacy level of the profile.
    """
    def POST(self):
        """
        Updates profile with fields sent from the client, returns saved fields.

        Can be tested in the following way:
        curl --data "logintoken=UaNxct7bJZ&twitter=1&csid_from_client=1" \
        http://localhost:8080/api/profile/userinfo/update
        """
        request_data = web.input()

        # Adding field to the list of required fields
        # self.required.append('getlist_privacy_level')

        if not self.is_request_valid(request_data):
            return api_response(data={}, status=405,
                                error_code="Required args are missing")

        csid_from_client = request_data.pop('csid_from_client')

        data = {}

        privacy_level = request_data.get('getlist_privacy_level')
        private = request_data.get('private')

        if privacy_level:
            data['getlist_privacy_level'] = privacy_level
        if private:
            data['private'] = private

        status, response_or_user = self.authenticate_by_token(
            request_data.pop('logintoken'))
        # Login was not successful
        if not status:
            return response_or_user

        if len(data) > 0:
            db.update('users', where='id = %s' % (response_or_user['id']),
                      **data)

        csid_from_server = response_or_user['seriesid']
        return api_response(data=data,
                            csid_from_client=csid_from_client,
                            csid_from_server=csid_from_server)


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

        status, response_or_user = self.authenticate_by_token(
            request_data.pop('logintoken'))
        # Login was not successful
        if not status:
            return response_or_user
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

        if len(to_insert) > 0:
            db.update('users', where='id = %s' % (response_or_user['id']),
                      **to_insert)
        csid_from_server = response_or_user['seriesid']
        return api_response(data=request_data,
                            csid_from_client=csid_from_client,
                            csid_from_server=csid_from_server)


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
        status, response_or_user = self.authenticate_by_token(
            request_data.pop('logintoken'))
        # Login was not successful
        if not status:
            return response_or_user


        # User id contains error code
        if not status:
            return response_or_user

        response = {field: response_or_user[field] for field in self._fields}
        csid_from_client = request_data.pop('csid_from_client')
        csid_from_server = response_or_user['seriesid']
        self.format_birthday(response_or_user, response)
        return api_response(data=response,
                            csid_from_client=csid_from_client,
                            csid_from_server=csid_from_server)


class ProfileInfo(BaseUserProfile):
    """
    Returns publically available profile information
    """

    def POST(self, profile):
        """ Returns profile information

        Required fields:
        - profile (sent via url)
        - csid_from_client

        Example usage:
        curl --data "csid_from_client=11" \
        http://localhost:8080/api/profile/userinfo/info/oleg
        """
        request_data = web.input()
        # Removing logintoken from request check
        self.required.remove('logintoken')
        if not self.is_request_valid(request_data):
            return api_response(data={}, status=405,
                                error_code="Required args are missing")
        query = db.select('users', vars={'username': profile},
                         where='username=$username')
        if query is not None:
            user = query.list()[0]

        response = {field: user[field] for field in self._fields}
        csid_from_client = request_data.pop('csid_from_client')
        csid_from_server = user['seriesid']
        self.format_birthday(user, response)
        return api_response(data=response,
                            csid_from_client=csid_from_client,
                            csid_from_server=csid_from_server)



class ManageGetList(BaseAPI):
    def POST(self):
        """
        Manage list of user products: share, add, remove

        Method for image_id_share_list must additional receive next
        required params:
        access_token - access token for social network
        social_network - name of social network (for example "facebook")
        """
        request_data = web.input(
            image_id_remove_list=[],
            image_id_share_list=[],
            image_id_add_list=[],
        )

        save_api_request(request_data)
        login_token = request_data.get("logintoken")

        status, response_or_user = self.authenticate_by_token(login_token)
        if not status:
            return response_or_user

        csid_from_client = request_data.get('csid_from_client')

        access_token = request_data.get("access_token")
        social_network = request_data.get("social_network")

        # Check input social data for posting
        if not access_token or not social_network:
            status_error = 400
            error_code = "Invalid input data"

        image_id_add_list = map(int, request_data.get("image_id_add_list"))
        add_list_result = []
        if len(image_id_add_list) > 0:
            add_list_result = self.add(response_or_user["id"],
                                       image_id_add_list)

        image_id_remove_list = map(int,
                                   request_data.get("image_id_remove_list"))
        remove_list_result = []
        if len(image_id_remove_list) > 0:
            remove_list_result = self.remove(response_or_user["id"],
                                             image_id_remove_list)

        image_id_share_list = map(int, request_data.get("image_id_share_list"))
        share_list_result = []
        if len(image_id_share_list) > 0:
            share_list_result = self.share(access_token, social_network,
                                           image_id_share_list)

        csid_from_server = response_or_user.get('seriesid')

        data = {
            "added": add_list_result,
            "removed": remove_list_result,
            "shared": share_list_result,
        }
        response = api_response(data, csid_from_client,
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

    def share(self, access_token, social_network, share_list):
        """
        Share products from user profile
        """
        # for testing only
        # access_token = 'CAACEdEose0cBABun8SJm4YuGGlT8vTKp51BJZCNPwjd\
        # X0sWHVrhitlZBm7JagMMDjFj2cZAtadWodSZA0PLitbKubDTFI1ZB6scvaIB9\
        # c6PkwuhzsiFd9SXoms9zIkVthr7OE2aWpHXhEqGrhD1HBLyNaCXZBz4eq5MovP\
        # lPZAape19eL9mrxOROsYWrYEbnKsZD'
        social_network = "facebook"
        share_list_result, status, error_code = share(access_token,
                                                      share_list,
                                                      social_network)

        return share_list_result


class ChangePassword(BaseAPI):
    def POST(self):
        """
        Change user password and take new client token
        """
        request_data = web.input()
        save_api_request(request_data)
        client_token = request_data.get("logintoken")
        status, response_or_user = self.authenticate_by_token(client_token)
        if not status:
            return response_or_user

        old_password = request_data.get("old_password")
        new_password = request_data.get("new_password")
        new_password2 = request_data.get("new_password2")

        pw_salt = response_or_user['pw_salt']
        pw_hash = response_or_user['pw_hash']

        status, error = self.passwords_validation(pw_salt, pw_hash,
                                                  old_password, new_password,
                                                  new_password2,
                                                  response_or_user["username"],
                                                  response_or_user["email"])
        if status:
            new_password_hash = self.create_password(pw_salt, new_password)
            db.update('users', pw_hash=new_password_hash,
                      vars={'id': response_or_user["id"]}, where="id=$id")

            # re_login user with new password
            sess = session.get_session()
            auth.login_user(sess, response_or_user["id"])

            user = db.select('users', {'id': response_or_user["id"]},
                             where='id=$id')[0]
            new_client_token = user.get('logintoken')
            csid_from_server = user.get('seriesid')
            csid_from_client = request_data.get("csid_from_client")
            data = {
                "client_token": new_client_token,
            }
            response = api_response(data, csid_from_client,
                                    csid_from_server=csid_from_server)
        else:
            data = {}
            user = db.select('users', {'id': response_or_user["id"]},
                             where='id=$id')[0]
            csid_from_server = user.get('seriesid')
            csid_from_client = request_data.get("csid_from_client")

            response = api_response(data=data,
                                    status=400,
                                    error_code=error,
                                    csid_from_client=csid_from_client,
                                    csid_from_server=csid_from_server)

        return response

    def passwords_validation(self, pw_salt, pw_hash, old_pwd=None,
                             new_pwd=None, new_pwd2=None, uname=None,
                             email=None):
        """
        Check if new password match with confirmation.
        Check relevance old password.
        Check empty field.
        """
        if new_pwd is None:
            return False, self.access_denied("New password is empty")

        if old_pwd is None:
            return False, self.access_denied("Old password is empty")

        if new_pwd != new_pwd2:
            return False, self.access_denied("Passwords do not match")

        if str(hash(str(hash(old_pwd)) + pw_salt)) != pw_hash:
            return False, self.access_denied("Incorrect old password")

        pwd_status, error_code = auth.check_password(uname, new_pwd, email)
        if not pwd_status:
            return False, error_code

        return True, "Success"

    def create_password(self, pw_salt, new_pwd):
        new_pwd_hash = str(hash(new_pwd))
        new_pwd_hash = str(hash(new_pwd_hash + pw_salt))
        return new_pwd_hash


class QueryBoards(BaseAPI):
    """
    Class responsible for getting boards of a given user
    """
    def POST(self):
        """ Returns all boards associated with a given user

        Required parameters:
        user_id: required parameter, sent via request data
        csid_from_client

        Can be tested using the following command:
        curl --data "user_id=2&csid_from_client=1" \
        http://localhost:8080/api/profile/userinfo/boards
        """
        request_data = web.input()
        csid_from_client = request_data.get('csid_from_client')
        csid_from_server = ""
        user_id = request_data.get('user_id')

        if not user_id:
            return api_response(data={}, status=405,
                                error_code="Missing user_id")
        boards = db.select('boards',
                           where='user_id=$user_id',
                           vars={'user_id': user_id})


        return api_response(data=boards.list(),
                            csid_from_server=csid_from_server,
                            csid_from_client=csid_from_client)


class QueryPins(BaseAPI):
    """
    Responsible for getting pins of a given user
    """
    def POST(self):
        """ Returns all pins associated with a given user

        Required parameters:
        user_id: required parameter, sent via request data
        csid_from_client

        Can be tested using the following command:
        curl --data "user_id=2&csid_from_client=1" \
        http://localhost:8080/api/profile/userinfo/pins
        """
        request_data = web.input()
        csid_from_client = request_data.get('csid_from_client')
        csid_from_server = ""
        user_id = request_data.get('user_id')

        if not user_id:
            return api_response(data={}, status=405,
                                error_code="Missing user_id")
        pins = db.select('pins',
                           where='user_id=$user_id',
                           vars={'user_id': user_id})

        return api_response(data=pins.list(),
                            csid_from_server=csid_from_server,
                            csid_from_client=csid_from_client)
