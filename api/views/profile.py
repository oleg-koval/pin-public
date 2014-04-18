import web

from api.utils import api_response, save_api_request
from api.views.base import BaseAPI
from api.views.social import share

from mypinnings.database import connect_db
from mypinnings import auth
from mypinnings import session


db = connect_db()


class ManageGetList(BaseAPI):
    def POST(self):
        """
            Manage list of user products: share, add, remove


            Method for image_id_share_list must additional receive next required params:

            access_token - access token for social network
            social_network - name of social network (for example "facebook")
        """
        request_data = web.input(
            image_id_remove_list=[],
            image_id_share_list=[],
            image_id_add_list=[],
        )

        save_api_request(request_data)
        csid_from_client = request_data.get('csid_from_client')
        client_token = request_data.get("client_token")

        access_token = request_data.get("access_token")
        social_network = request_data.get("social_network")

        # Check input social data for posting
        if not access_token or not social_network:
            status_error = 400
            error_code = "Invalid input data"

        status, user_id = self.authenticate_by_token(client_token)
        # User id contains error code
        if not status:
            return user_id

        image_id_add_list = map(int, request_data.get("image_id_add_list"))
        add_list_result = []
        if len(image_id_add_list) > 0:
            add_list_result = self.add(user_id, image_id_add_list)

        image_id_remove_list = map(int, request_data.get("image_id_remove_list"))
        remove_list_result = []
        if len(image_id_remove_list) > 0:
            remove_list_result = self.remove(user_id, image_id_remove_list)

        image_id_share_list = map(int, request_data.get("image_id_share_list"))
        share_list_result = []
        if len(image_id_share_list) > 0:
            share_list_result = self.share(access_token, social_network, image_id_share_list)

        user = db.select('users', {'id': user_id}, where='id=$id')[0]
        csid_from_server = user.get('seriesid')
        data = {
            "added": add_list_result,
            "removed": remove_list_result,
            "shared": share_list_result,
        }
        response = api_response(data,
                        status=status_error,
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
        share_list_result, status, error_code =share(access_token, share_list, social_network)

        return share_list_result

class ChangePassword(BaseAPI):
    def POST(self):
        """
            Change user password and take new client token
        """
        request_data = web.input()
        save_api_request(request_data)
        client_token = request_data.get("client_token")

        status, user_id = self.authenticate_by_token(client_token)
        # User id contains error code
        if not status:
            return user_id

        old_password = request_data.get("old_password")
        new_password = request_data.get("new_password")
        new_password2 = request_data.get("new_password2")

        user = db.select('users', {'id': user_id}, where='id=$id', what='pw_salt, pw_hash')[0]
        pw_salt = user['pw_salt']
        pw_hash = user['pw_hash']  

        status, error = self.passwords_validation(pw_salt, pw_hash, old_password, new_password, new_password2)
        if status:
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
            return error

    def passwords_validation(self, pw_salt, pw_hash, old_pwd=None, new_pwd=None, new_pwd2=None):
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
            return False, self.access_denied("Incorrect confirmation new password")
      
        if str(hash(str(hash(old_pwd)) + pw_salt)) != pw_hash:
            return False, self.access_denied("Incorrect old password")

        return True, "Success"

    def create_password(self, pw_salt, new_pwd):
        new_pwd_hash = str(hash(new_pwd))
        new_pwd_hash = str(hash(new_pwd_hash + pw_salt))
        return new_pwd_hash
