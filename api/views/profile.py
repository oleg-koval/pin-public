import web

from api.utils import api_response, save_api_request
from api.views.base import BaseAPI

from mypinnings.database import connect_db
from mypinnings import auth
from mypinnings import session


db = connect_db()


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
        user_id = self.authenticate_by_token(client_token)

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

            user = db.select('users', {'id': user_id}, where='id=$id', what='logintoken')[0]
            new_client_token = user['logintoken']
            csid_from_server = user['seriesid']
            data = {
                "client_token": new_client_token,
                "csid_from_server": csid_from_server,
            }
            response = api_response(data)
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
