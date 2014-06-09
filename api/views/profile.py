""" API views responsible for returing and updating the profile info"""
import os
import uuid
import web
import math
from datetime import datetime

from api.utils import api_response, save_api_request, api_response, \
    photo_id_to_url
from api.views.base import BaseAPI
from api.views.social import share, get_comments_to_photo
from api.entities import UserProfile

from mypinnings import auth
from mypinnings import session
from mypinnings.database import connect_db, redis_get_user_pins
from mypinnings.conf import settings
from mypinnings.media import store_image_from_filename
from mypinnings import pin_utils


db = connect_db()


class BaseUserProfile(BaseAPI):
    """
    General class which holds list of fields used by user profile methods
    """
    def __init__(self):
        self._fields = ['id', 'name', 'about', 'city', 'country', 'hometown',
                        'about', 'email', 'pic', 'website', 'facebook',
                        'twitter', 'getlist_privacy_level', 'private', 'bg',
                        'bgx', 'bgy', 'show_views', 'views', 'username', 'zip',
                        'linkedin', 'gplus', 'bg_resized_url', 'headerbgy', 'headerbgx']
        self._birthday_fields = ['birthday_year', 'birthday_month',
                                 'birthday_day']
        self.required = ['csid_from_client', 'logintoken']
        self.default_fields = ['project_id', 'os_type', 'version_id','format_type']

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
                    field not in self.required and
                    field not in self.default_fields):
                return False
        return True


class SetPrivacy(BaseUserProfile):
    """
    Allows to set privacy level of the profile.

    :link: /api/profile/userinfo/update
    """
    def POST(self):
        """ Updates profile with fields sent from the client,
        returns saved fields.

        :param str csid_from_client: csid from client key
        :param str getlist_privacy_level/private: controls privacy level
        :param str logintoken: logintoken
        :response_data: Returns api response with 'getlist_privacy_level/private.'
        :to test: curl --data "logintoken=UaNxct7bJZ&twitter=1&csid_from_client=1" http://localhost:8080/api/profile/userinfo/update
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
    Defines a class responsible for updating user data, inside the profile

    :link: /api/profile/userinfo/update
    """
    def POST(self):
        """  Updates profile with fields sent from the client,
        returns saved fields.

        :param str csid_from_client: Csid string from client
        :param str logintoken: Logintoken
        :param str <field>: The field which will be changed
        :response_data: returns changed field
        :to test: curl --data "logintoken=UaNxct7bJZ&twitter=1&csid_from_client=1" http://localhost:8080/api/profile/userinfo/update

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
    """ Allows to render profile information, by token

    :url: /api/profile/userinfo/get
    """
    def POST(self):
        """
        :param str csid_from_client: Csid string from client
        :param str logintoken: Logintoken

        :response_data: 'id', 'name', 'about', 'city', 'country','hometown', 'about', 'email', 'pic', 'website', 'facebook', 'twitter', 'getlist_privacy_level', 'private', 'bg', 'bgx', 'bgy', 'show_views', 'views', 'username', 'zip', 'linkedin', 'gplus', 'bg_resized_url', 'headerbgy', 'headerbgx'
        :to test: curl --data "logintoken=UaNxct7bJZ&csid_from_client=123" http://localhost:8080/api/profile/userinfo/get
        """
        request_data = web.input()
        if not self.is_request_valid(request_data):
            return api_response(data={}, status=405,
                                error_code="Required args are missing")
        status, response_or_user = self.authenticate_by_token(
            request_data.pop('logintoken'))

        # User id contains error code
        if not status:
            return response_or_user

        response = {field: response_or_user[field] for field in self._fields}
        response['resized_url'] = photo_id_to_url(response['pic'])
        csid_from_client = request_data.pop('csid_from_client')
        csid_from_server = response_or_user['seriesid']
        self.format_birthday(response_or_user, response)
        return api_response(data=response,
                            csid_from_client=csid_from_client,
                            csid_from_server=csid_from_server)


class ProfileInfo(BaseUserProfile):
    """
    Returns public profile information

    :url: /api/profile/userinfo/info
    """
    def POST(self):
        """
        :param str csid_from_client: Csid string from client
        :param str logintoken: Logintoken
        :param str username: Username
        :param str username: id
        :response_data: 'id', 'name', 'about', 'city', 'country','hometown', 'about', 'email', 'pic', 'website', 'facebook', 'twitter', 'getlist_privacy_level', 'private', 'bg', 'bgx', 'bgy', 'show_views', 'views', 'username', 'zip', 'linkedin', 'gplus', 'bg_resized_url', 'headerbgy', 'headerbgx'

        :to test:
        - curl --data "csid_from_client=11&id=78&logintoken=RxPu7fLYgv" http://localhost:8080/api/profile/userinfo/info
        - curl --data "csid_from_client=11&username=Oleg&logintoken=RxPu7fLYgv" http://localhost:8080/api/profile/userinfo/info
        """
        request_data = web.input()
        profile = request_data.get("username", "")
        user_id = request_data.get("id", 0)
        logintoken = request_data.get("logintoken", "")

        if not self.is_request_valid(request_data):
            return api_response(data={}, status=405,
                                error_code="Required args are missing")

        if not profile and not user_id:
            error_code = "This function requires either profile or user_id"
            return api_response(data={}, status=405,
                                error_code=error_code)

        status, response_or_user = self.authenticate_by_token(logintoken)
        if not status:
            return api_response(data={}, status=405,
                                error_code="You need to log in first")

        user = UserProfile.query_user(profile=profile, user_id=user_id)
        if not user:
            return api_response(data={}, status=405,
                                error_code="User was not found")

        followers = UserProfile\
            .query_followed_by(profile_owner=user["id"],
                               current_user=response_or_user["id"])
        user['follower_count'] = len(followers)

        follow = UserProfile\
            .query_following(profile_owner=user["id"],
                             current_user=response_or_user["id"])
        user['follow_count'] = len(follow)

        csid_from_client = request_data.pop('csid_from_client')
        csid_from_server = ""

        return api_response(data=user,
                            csid_from_client=csid_from_client,
                            csid_from_server=csid_from_server)

    def get_user_info(self, profile="", user_id=0):
        query = db.select('users',
                          vars={'username': profile, 'id': user_id},
                          where="username=$username or id=$id")

        if len(query) > 0:
            user = query.list()[0]
            user['pic'] = photo_id_to_url(user['pic'])
        else:
            return False
        response = {field: user[field] for field in self._fields}
        response = self.format_birthday(user, response)
        return response

class UpdateProfileViews(BaseUserProfile):
    """
    Responsible for updating count of pofile views

    :link: /api/profile/updateviews/<username>
    """
    def POST(self, profile):
        """
        :param str csid_from_client: Csid string from client
        :param str profile: must be in url
        :response_data: returns a dict with 'status' key
        :to test: curl --data "csid_from_client=11&logintoken=RxPu7fLYgv" http://localhost:8080/api/profile/updateviews/oleg
        """
        request_data = web.input()

        if not self.is_request_valid(request_data):
            return api_response(data={}, status=405,
                                error_code="Required args are missing")

        # Checking if user has a valid logintoken
        status, response_or_user = self.authenticate_by_token(
            request_data.pop('logintoken'))
        # Login was not successful
        if not status:
            return response_or_user

        db.update('users', where='user = $username',
                  vars={'username': profile},
                  views=web.SQLLiteral('views + 1'))

        csid_from_client = request_data.pop('csid_from_client')
        csid_from_server = ""

        return api_response(data={"status": "success"},
                            csid_from_client=csid_from_client,
                            csid_from_server=csid_from_server)


class ManageGetList(BaseAPI):
    """
    :link: /api/profile/mgl
    """
    def POST(self):
        """
        Manage list of user products: sharing, add, remove

        Method for image_id_share_list must additional receive next
        :param str csid_from_client: Csid string from client
        :param str logintoken: Logintoken
        :param str social_network: e.g. facebook
        :response_data: returns added/removed/shared getlists
        """
        request_data = web.input(
            image_id_remove_list=[],
            image_id_share_list=[],
            image_id_add_list=[],
        )

        # Setting default status code as 200
        status = 200
        # Setting empty error
        error_code = ""

        save_api_request(request_data)
        login_token = request_data.get("logintoken")

        status_success, response_or_user = self.authenticate_by_token(login_token)
        if not status_success:
            return response_or_user

        csid_from_client = request_data.get('csid_from_client')

        access_token = request_data.get("access_token")
        social_network = request_data.get("social_network")

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
            # Check input social data for posting
            if not access_token or not social_network:
                status = 400
                error_code = "Invalid input data"
            else:
                share_list_result, status, error_code = self.sharing(access_token, social_network,
                                                                 image_id_share_list)

        csid_from_server = response_or_user.get('seriesid')

        data = {
            "added": add_list_result,
            "removed": remove_list_result,
            "shared": share_list_result,
        }
        response = api_response(data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
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

    def sharing(self, access_token, social_network, share_list):
        """
        Share products from user profile
        """

        share_list_result, status, error_code = share(access_token,
                                                      share_list,
                                                      social_network)

        return share_list_result, status, error_code


class ChangePassword(BaseAPI):
    """
    :link: /api/profile/pwd
    """
    def POST(self):
        """ Change user password and get/store new logintoken
        :param str csid_from_client: Csid string from client
        :param str logintoken: Logintoken
        :param str old_password: current password of the user
        :param str new_password, new_password2: The new password typed 2 times

        :response_data: new clinet token
        :to test:
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

    :link: /api/profile/userinfo/boards
    """
    def POST(self):
        """ Returns all boards associated with a given user

        :param str csid_from_client: Csid string from client
        :param str user_id: id of the queried user
        :response_data: returns all boards of a given user as a list
        :to test: curl --data "user_id=2&csid_from_client=1" http://localhost:8080/api/profile/userinfo/boards
        """
        request_data = web.input()
        csid_from_client = request_data.get('csid_from_client')
        csid_from_server = ""
        user_id = request_data.get('user_id')

        if not user_id:
            return api_response(data={}, status=405,
                                error_code="Missing user_id")
        boards_tmp = db.select('boards',
                           where='user_id=$user_id',
                           vars={'user_id': user_id})

        boards = []
        for board in boards_tmp:
            pins_from_board = db.select('pins',
                               where='board_id=$board_id',
                               vars={'board_id': board['id']})
            board['pins_ids'] = []
            for pin_from_board in pins_from_board:
                if pin_from_board['id'] not in board['pins_ids']:
                    board['pins_ids'].append(pin_from_board['id'])
            boards.append(board)

        return api_response(data=boards,
                            csid_from_server=csid_from_server,
                            csid_from_client=csid_from_client)


class QueryPins(BaseAPI):
    """
    Responsible for getting pins of a given user

    :url: /api/profile/userinfo/pins
    """
    def POST(self):
        """ Returns all pins associated with a given user

        :param str csid_from_client: Csid string from client
        :param str user_id: id of the queried user
        :response_data: Returns list of pins of a current user

        :to test: curl --data "user_id=78&csid_from_client=1" http://localhost:8080/api/profile/userinfo/pins
        """
        query = '''
        select tags.tags, pins.*, users.pic as user_pic,
        users.username as user_username, users.name as user_name,
        count(distinct p1) as repin_count,
        count(distinct l1) as like_count
        from users
        left join pins on pins.user_id = users.id
        left join tags on tags.pin_id = pins.id
        left join pins p1 on p1.repin = pins.id
        left join likes l1 on l1.pin_id = pins.id
        where users.id = $id
        group by tags.tags, pins.id, users.id
        order by timestamp desc'''

        request_data = web.input()
        csid_from_client = request_data.get('csid_from_client')
        csid_from_server = ""
        user_id = request_data.get('user_id')

        if not user_id:
            return api_response(data={}, status=405,
                                error_code="Missing user_id")
        results = db.query(query, vars={'id': user_id})

        pins = []
        current_row = None
        pins_counter = len(results)
        owned_pins_counter = 0
        for row in results:
            if not row.id:
                continue
            if not current_row or current_row.id != row.id:
                current_row = row
                tag = row.tags
                current_row.tags = []
                if tag:
                    current_row.tags.append(tag)

                current_row_dt = datetime.fromtimestamp(current_row.timestamp)

                pins.append(current_row)
                if not current_row.get("repin"):
                    owned_pins_counter += 1
            else:
                tag = row.tags
                if tag not in current_row.tags:
                    current_row.tags.append(tag)

        data = {
            "total": pins_counter,
            "total_owned": owned_pins_counter
        }
        page = int(request_data.get("page", 1))
        if page is not None:
            items_per_page = int(request_data.get("items_per_page", 10))
            if items_per_page < 1:
                items_per_page = 1

            data['pages_count'] = math.ceil(float(len(pins)) /
                                            float(items_per_page))
            data['pages_count'] = int(data['pages_count'])
            data['page'] = page
            data['items_per_page'] = items_per_page

            start = (page-1) * items_per_page
            end = start + items_per_page
            data['pins_list'] = pins[start:end]
        else:
            data['pins_list'] = pins

        return api_response(data=data,
                            csid_from_server=csid_from_server,
                            csid_from_client=csid_from_client)

class TestUsernameOrEmail(BaseAPI):
    """
    Checks if given username or email is already added to database.
    in case if a username

    :link: /api/profile/test-username
    """
    def POST(self):
        """
        :param str csid_from_client: Csid string from client
        :param str logintoken: username_or_email
        :response data: returns 'ok' or 'notfound'
        :to test: curl --data "csid_from_client=1&username_or_email=oleg" http://localhost:8080/api/profile/test-username
        """
        request_data = web.input()
        username_or_email = request_data.get('username_or_email')

        vars={'username_or_email': username_or_email}
        # Trying to find a user with same username
        result = db.select('users', vars=vars,
                           where='username=$username_or_email')
        # Fallback, trying to find user with same email
        if len(result.list()) == 0:
            result = db.select('users', vars=vars,
                               where='email=$username_or_email')

        if len(result.list()) == 0:
            status = 'notfound'
        else:
            status = 'ok'

        csid_from_client = request_data.get('csid_from_client')
        csid_from_server = ""
        return api_response(data=status,
                            csid_from_server=csid_from_server,
                            csid_from_client=csid_from_client)


class PicUpload(BaseAPI):
    """ Upload profile picture and save it in database """
    def POST(self):
        """
        Picture upload main handler
        """
        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        request_data = web.input(file={})
        logintoken = request_data.get('logintoken')

        user_status, user = self.authenticate_by_token(logintoken)
        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        csid_from_client = request_data.get("csid_from_client")

        file_obj = request_data.get('file')

        # For some reason, FileStorage object treats itself as False
        if type(file_obj) == dict:
            return api_response(data={}, status=405,
                                error_code="Required args are missing")

        file_path = self.save_file(file_obj)
        images_dict = store_image_from_filename(db,
                                                file_path,
                                                widths=[80])

        photo_kwargs = {
            'original_url': images_dict[0]['url'],
            'resized_url': images_dict.get(80, images_dict[0]).get('url', None),
            'album_id': user['id']
        }

        pid = db.insert('photos', **photo_kwargs)

        db.update('users',
                  where='id = $id',
                  vars={'id': user['id']},
                  pic=pid)

        data['pid'] = pid
        data['original_url'] = photo_kwargs['original_url']
        data['resized_url'] = photo_kwargs['resized_url']

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)

        return response

    def save_file(self, file_obj, upload_dir=None):
        """
        Saves uploaded file to a given upload dir.
        """
        if not upload_dir:
            upload_dir = self.get_media_path()
        filename = file_obj.filename
        filename = self.get_file_name(filename, upload_dir)
        filepath = os.path.join(upload_dir, filename)
        upload_file = open(filepath, 'w')
        upload_file.write(file_obj.file.read())
        upload_file.close()
        return filepath

    def get_media_path(self):
        """
        Returns or creates media directory.
        """
        media_path = settings.MEDIA_PATH
        if not os.path.exists(media_path):
            os.makedirs(media_path)
        return media_path

    def get_file_name(self, filename, upload_dir):
        """
        Method responsible for avoiding duplicated filenames.
        """
        filepath = os.path.join(upload_dir, filename)
        exists = os.path.isfile(filepath)
        # Suggest uuid hex as a filename to avoid duplicates
        if exists:
            filename = "%s.%s" % (uuid.uuid4().hex[:10], filename)
        return filename


class BgUpload(BaseAPI):
    """ Upload profile background and save it in database """
    def POST(self):
        """
        Background upload main handler
        """
        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        request_data = web.input(file={})
        logintoken = request_data.get('logintoken')

        user_status, user = self.authenticate_by_token(logintoken)
        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        csid_from_client = request_data.get("csid_from_client")

        file_obj = request_data.get('file')

        # For some reason, FileStorage object treats itself as False
        if type(file_obj) == dict:
            return api_response(data={}, status=405,
                                error_code="Required args are missing")

        file_path = self.save_file(file_obj)
        images_dict = store_image_from_filename(db,
                                                file_path,
                                                widths=[1100])

        bg_kwargs = {
            'bg_original_url': images_dict[0]['url'],
            'bg_resized_url': images_dict.get(1100, images_dict[0]).get('url', None),
            'bg': True,
            'bgx': 0,
            'bgy': 0
        }

        db.update('users',
                  where='id = $id',
                  vars={'id': user['id']},
                  **bg_kwargs)

        data['bg_original_url'] = bg_kwargs['bg_original_url']
        data['bg_resized_url'] = bg_kwargs['bg_resized_url']

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)

        return response

    def save_file(self, file_obj, upload_dir=None):
        """
        Saves uploaded file to a given upload dir.
        """
        if not upload_dir:
            upload_dir = self.get_media_path()
        filename = file_obj.filename
        filename = self.get_file_name(filename, upload_dir)
        filepath = os.path.join(upload_dir, filename)
        upload_file = open(filepath, 'w')
        upload_file.write(file_obj.file.read())
        upload_file.close()
        return filepath

    def get_media_path(self):
        """
        Returns or creates media directory.
        """
        media_path = settings.MEDIA_PATH
        if not os.path.exists(media_path):
            os.makedirs(media_path)
        return media_path

    def get_file_name(self, filename, upload_dir):
        """
        Method responsible for avoiding duplicated filenames.
        """
        filepath = os.path.join(upload_dir, filename)
        exists = os.path.isfile(filepath)
        # Suggest uuid hex as a filename to avoid duplicates
        if exists:
            filename = "%s.%s" % (uuid.uuid4().hex[:10], filename)
        return filename


class GetProfilePictures(BaseAPI):
    """
    API method for get photos of user
    """
    def POST(self):
        request_data = web.input()

        update_data = {}
        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        user_id = request_data.get("user_id")

        csid_from_client = request_data.get('csid_from_client')

        select_str = "0 AS self_like_count,"
        join_str = ""
        logintoken = request_data.get('logintoken', None)
        if logintoken:
            user_status, user = self.authenticate_by_token(logintoken)
            if user_status:
                select_str = "count(distinct l2) as self_like_count,"
                join_str = "LEFT JOIN profile_photo_likes l2 \
                            ON l2.photo_id = photos.id \
                            AND l2.user_id = %s" % user['id']

        if not user_id:
            status = 400
            error_code = "Invalid input data"

        data['user_id'] = user_id

        if status == 200:
            photos = db.query("SELECT photos.*, users.id as user_id, \
                        users.pic as user_pic, \
                        " + select_str + " \
                        count(distinct l1) as like_count \
                        FROM photos \
                        LEFT JOIN users ON photos.album_id = users.id \
                        LEFT JOIN profile_photo_likes l1 \
                        ON l1.photo_id = photos.id \
                        " + join_str + " \
                        WHERE photos.album_id=%s \
                        GROUP BY photos.id, users.id \
                        ORDER BY photos.id desc" % (user_id))\
            .list()

            data['photos'] = []
            for photo in photos:
                photo['comments'] = get_comments_to_photo(photo['id'])
                data['photos'].append(photo)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


class PicRemove(BaseAPI):
    """ Remove profile picture and save changes in database """
    def POST(self):
        """
        Picture remove main handler
        """
        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        request_data = web.input()
        logintoken = request_data.get('logintoken')
        photo_id = request_data.get('photo_id')

        user_status, user = self.authenticate_by_token(logintoken)
        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        csid_from_client = request_data.get("csid_from_client")

        photos = db.select('photos',
                           where='id = $id and album_id = $album_id',
                           vars={'id': photo_id, 'album_id': user['id']})

        if len(photos) > 0:
            db.delete('photos',
                      where='id = $id',
                      vars={'id': photo_id})
            if str(user['pic']) == photo_id:
                photos = db.select('photos',
                                   where='album_id = $album_id',
                                   vars={'album_id': user['id']})
                if len(photos) > 0:
                    pid = photos[0]['id']
                else:
                    pid = None

                db.update('users',
                          where='id = $id',
                          vars={'id': user['id']},
                          pic=pid)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)

        return response


class BgRemove(BaseAPI):
    """ Remove profile picture and save changes in database """
    def POST(self):
        """
        Picture remove main handler
        """
        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        request_data = web.input()
        logintoken = request_data.get('logintoken')

        user_status, user = self.authenticate_by_token(logintoken)
        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        csid_from_client = request_data.get("csid_from_client")

        bg_kwargs = {
            'bg_original_url': None,
            'bg_resized_url': None,
            'bg': False,
            'bgx': 0,
            'bgy': 0
        }

        db.update('users',
                  where='id = $id',
                  vars={'id': user['id']},
                  **bg_kwargs)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)

        return response


class UserFeed(BaseAPI):
    def POST(self):
        request_data = web.input()

        update_data = {}
        data = {}
        default_limit = 50
        status = 200
        csid_from_server = None
        error_code = ""
        csid_from_client = request_data.get('csid_from_client')

        # Get user id from data from request
        user_id = request_data.get('user_id')
        csid_from_client = request_data.get('csid_from_client', '')
        logintoken = request_data.get('logintoken', None)
        limit = int(request_data.get('limit', default_limit))
        offset = int(request_data.get('offset', 0))
        use_redis = request_data.get('use_redis', False)

        if logintoken:
            user_status, user = self.authenticate_by_token(logintoken)
            
        if not user_id:
            status = 400
            error_code = "Invalid input data"

        data['user_id'] = user_id
        data['feeds'] = list()
        feeds = None

        if status == 200:

#                 SELECT pins.*, tags.tags, categories.id as category, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
#                         count(distinct p1) as repin_count, count(distinct l1) as like_count
#                 FROM pins
#                 LEFT JOIN tags on tags.pin_id = pins.id
#                 LEFT JOIN pins p1 on p1.repin = pins.id
#                 LEFT JOIN likes l1 on l1.pin_id = pins.id
#                 LEFT JOIN users on users.id = pins.user_id
#                 LEFT JOIN follows on follows.follow = users.id
#                 LEFT JOIN categories on categories.id in
#                     (SELECT category_id FROM pins_categories WHERE pin_id = pins.id limit 1)
#                 WHERE pins.user_id IN (
#                     SELECT follows.follow FROM follows WHERE follows.follower = $id
#                     UNION
#                     SELECT friends.id1 FROM friends WHERE friends.id2 = $id
#                 ) OR pins.id IN (
#                     SELECT board.id FROM boards WHERE user_id = $id AND public=true  
#                 )
#                 GROUP BY tags.tags, categories.id, pins.id, users.id
#                 LIMIT $limit OFFSET $offset'''

            feed_query = '''
                SELECT pins.*, tags.tags, categories.id as category, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count, count(distinct l1) as like_count
                FROM pins
                    LEFT JOIN tags on tags.pin_id = pins.id
                    LEFT JOIN pins p1 on p1.repin = pins.id
                    LEFT JOIN likes l1 on l1.pin_id = pins.id
                    LEFT JOIN users on users.id = pins.user_id
                    LEFT JOIN follows on follows.follow = users.id
                    LEFT JOIN categories on categories.id in
                        (SELECT category_id FROM pins_categories WHERE pin_id = pins.id limit 1)
                WHERE pins.user_id IN (
                        SELECT follows.follow FROM follows WHERE follows.follower = $id
                        UNION
                        SELECT friends.id1 FROM friends WHERE friends.id2 = $id
                    ) OR pins.board_id IN (
                        SELECT boards.id FROM boards WHERE user_id IN(
                            SELECT follows.follow FROM follows WHERE follows.follower = $id
                        ) AND public=true  
                    ) OR pins.id IN (
                        SELECT pins_categories.pin_id FROM pins_categories WHERE category_id IN (
                            SELECT user_prefered_categories.category_id FROM user_prefered_categories WHERE user_id = $id
                        )
                    )
                GROUP BY tags.tags, categories.id, pins.id, users.id
                LIMIT $limit OFFSET $offset'''


            if use_redis == 'True':
                if limit == 0 and offset == 0:
                    # Get all feed
                    feeds = redis_get_user_pins(user_id)
                    data['solution'] = 'REDIS'
                    check_feeds = [pin_utils.dotdict(feed) for feed in feeds]
                else:
                    # Get limited count of feed
                    if limit <= 0:
                        limit = default_limit

                    feeds = redis_get_user_pins(user_id, offset, limit+offset-1, True)
                    data['solution'] = 'REDIS with options'
                    # redis_get_user_pins returns in the last element count of
                    # items, so feeds.pop() returns and delete the last item
                    # from the list
                    feed_len = feeds.pop()

                    # if the redis don't have all element trigger db query as a
                    # fallback
                    if feed_len < limit:
                        qvars = {'id': user_id, 'limit': int(limit), 'offset': int(offset)}
                        feeds = db.query(feed_query, vars=qvars)
                        data['solution'] = 'POSTGRES'
            else:
                if limit <= 0:
                    limit = default_limit

                qvars = {'id': user_id, 'limit': int(limit), 'offset': int(offset)}
                feeds = db.query(feed_query, vars=qvars)
                data['solution'] = 'POSTGRES'

            # offset = int(web.input(offset=0).offset)
            # ajax = int(web.input(ajax=0).ajax)
            if feeds is not None:
                for feed in feeds:
                    data['feeds'].append(feed)
            else:
                print 'No results'

        response = api_response(data=data, 
                                status=status, 
                                error_code=error_code, 
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)

        return response
