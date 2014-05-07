import os
import web
import uuid

from api.views.base import BaseAPI
from api.utils import api_response, save_api_request
from mypinnings.database import connect_db


db = connect_db()


class ImageUpload(BaseAPI):
    def POST(self):
        data = web.input()
        save_api_request(data)
        userfile = web.input(image_file={})
        file_url = self.upload_file(userfile)
        if file_url:
            data = {
                "file_url": file_url
            }
            return api_response(data=data)
        data = {}
        return api_response(data=data)

    def upload_file(self, file_obj, upload_dir=None):
        if not upload_dir:
            upload_dir = self.get_media_path()
        filename = file_obj.image_file.filename
        filename = self.check_file_existence(filename, upload_dir)
        print filename
        filepath = os.path.join(upload_dir, filename)
        upload_file = open(filepath, 'w')
        upload_file.write(file_obj.image_file.file.read())
        upload_file.close()
        return filepath

    def get_media_path(self, media_dir="media"):
        current_path = os.path.realpath(os.path.dirname(__file__))
        prj_dir = os.path.join(current_path, "..", "..")
        media_path = os.path.join(prj_dir, media_dir)
        if not os.path.exists(media_path):
            os.makedirs(media_path)
        return media_path

    def check_file_existence(self, filename, upload_dir):
        filepath = os.path.join(upload_dir, filename)
        exists = os.path.isfile(filepath)
        if exists:
            filename = "%s.%s" % (uuid.uuid4().hex[:10], filename)
        return filename


class ManageProperties(BaseAPI):
    """
    API method for changing pin properties
    """
    def POST(self):
        request_data = web.input(
            hash_tag_add_list=[],
            hash_tag_remove_list=[],
        )

        update_data = {}
        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        image_id = request_data.get("image_id")
        image_title = request_data.get("image_title")
        image_desc = request_data.get("image_desc")
        product_url = request_data.get("product_url")
        # source_url = request_data.get("source_url")
        hash_tag_add_list = map(str,
                                request_data.get("hash_tag_add_list"))
        hash_tag_remove_list = map(str,
                                   request_data.get("hash_tag_remove_list"))

        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        if not image_id:
            status = 400
            error_code = "Invalid input data"

        data['image_id'] = image_id
        if image_title:
            update_data['name'] = image_title
            data['image_title'] = image_title
        if image_desc:
            update_data['description'] = image_desc
            data['image_desc'] = image_desc
        if product_url:
            update_data['product_url'] = product_url
            data['product_url'] = product_url

        # Temporary unavailable field
        # if source_url:
        #     update_data['source_url'] = source_url
        #     data['source_url'] = source_url

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']

        tags = db.select('tags', where='pin_id = %s' % (image_id))
        if len(tags) > 0:
            tags = tags[0]['tags'].split()
            tags = set(tags) - set(hash_tag_remove_list)
            tags = tags | set(hash_tag_add_list)
            tags = ' '.join(tags)

            db.update('tags', where='pin_id = %s' % (image_id),
                      tags=tags)
        else:
            tags = ' '.join(hash_tag_add_list)
            db.insert('tags', pin_id=image_id, tags=tags)

        if status == 200 and len(update_data) > 0:
            db.update('pins', where='id = %s' % (image_id),
                      **update_data)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


class Categorize(BaseAPI):
    """
    API method for changing category of pin
    """
    def POST(self):
        request_data = web.input(
            category_id_list=[],
        )

        update_data = {}
        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        image_id = request_data.get("image_id")
        category_id_list = map(int,
                               request_data.get("category_id_list"))

        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        if not image_id:
            status = 400
            error_code = "Invalid input data"

        data['image_id'] = image_id

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']

        if status == 200:
            db.delete('pins_categories', where='pin_id = %s' % (image_id))
            for category_id in category_id_list:
                db.insert('pins_categories',
                          pin_id=image_id,
                          category_id=category_id)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response
