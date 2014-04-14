import web

from api.utils import api_response, save_api_request
from api.views.base import BaseAPI

from mypinnings.database import connect_db


db = connect_db()


class ManageGetList(BaseAPI):
    def POST(self):
        """
            Manage list of user products: share, add, remove
        """
        request_data = web.input(image_id_remove_list=[],image_id_share_list=[],image_id_add_list=[])

        save_api_request(request_data)
        client_token = request_data.get("client_token")
        user_id = self.authenticate_by_token(client_token)

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
            exist_product = db.select('user_prefered_pins', where=web.db.sqlwhere(user_product))
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
            exist_product = db.select('user_prefered_pins', where=web.db.sqlwhere(user_product))
            if len(exist_product) > 0:
                remove_list_result.append(pin)
                db.delete('user_prefered_pins', where=web.db.sqlwhere(user_product))
        return remove_list_result
        

    def share(self, user_id, share_list):
        """
            Share products from user profile
        """
        pass



