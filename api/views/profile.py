""" API views responsible for returing and updating the profile info"""
import web

from api.utils import api_response, save_api_request, api_response
from api.views.base import BaseAPI

from mypinnings.database import connect_db
from datetime import datetime

db = connect_db()


class UserInfoUpdate(BaseAPI):
    """
    Defines a class responsible for updating user data, inide the profile
    """
    _fields = ['name', 'about', 'city', 'hometown', 'about',
               'email', 'pic', 'website', 'facebook', 'twitter']
    _birthday_fields = ['birthday_year', 'birthday_month', 'birthday_day']

    def POST(self):
        """
        Updates profile with fields sent from the client
        """
        request_data = web.input()

        status, user_id = self.authenticate_by_token(
            request_data.get('logintoken'))
        # User id contains error code
        if not status:
            return user_id
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
        db.update('users', where='id = %s' % (user_id), **to_insert)
        user_data = db.select('users', where='id = %s' % (user_id)).list()[0]
        response = {field: user_data[field] for field in self._fields}
        if user_data['birthday']:
            response['birthday_year'] = user_data['birthday'].year
            response['birthday_day'] = user_data['birthday'].day
            response['birthday_month'] = user_data['birthday'].month
        return api_response(data=response, status=200)


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
        client_token = request_data.get("client_token")

        status, user_id = self.authenticate_by_token(client_token)
        # User id contains error code
        if not status:
            return user_id

        image_id_add_list = map(int, request_data.get("image_id_add_list"))
        add_list_result = []
        if len(image_id_add_list) > 0:
            add_list_result = self.add(user_id, image_id_add_list)

        image_id_remove_list = map(
            int,
            request_data.get("image_id_remove_list")
        )
        remove_list_result = []
        if len(image_id_remove_list) > 0:
            remove_list_result = self.remove(user_id, image_id_remove_list)

        image_id_share_list = map(int, request_data.get("image_id_share_list"))
        share_list_result = []
        if len(image_id_share_list) > 0:
            share_list_result = self.share(user_id, image_id_share_list)

        data = {
            "added": add_list_result,
            "removed": remove_list_result,
            "shared": share_list_result,
        }
        response = api_response(data)
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
