import os
import web
import uuid
import datetime
import math

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


class ImageQuery(BaseAPI):
    """
    Image query for getting information about image

    method need some actual "logintoken" in security reason
    """
    def POST(self):
        """
        You can tested it using:
        curl --data "csid_from_client=1&query_type=all&logintoken=2mwvVHVFga&
        query_params=840&query_params=841&&query_params=842"
        http://localhost:8080/api/image/query

        "image_url" in response related with "link" in pins table.
        """
        request_data = web.input(query_params=[],)
        save_api_request(request_data)

        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        # User id contains error code
        if not user_status:
            return user
        csid_from_server = user['seriesid']

        query_type = request_data.get("query_type")
        query_params = map(int, request_data.get("query_params"))
        image_data_list = []
        if len(query_params) > 0:
            image_data_list = self.query_image(query_params)

        csid_from_client = request_data.get("csid_from_client")
        data = {
            "image_data_list": image_data_list,
        }
        response = api_response(data,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response

    def query_image(self, query_params):
        image_data_list = []
        for image_id in query_params:
            image = db.select('pins', where='id = %s' % (image_id)).list()

            if len(image) > 0:
                image_properties = {
                    "image_id": image_id,
                    "image_title": image[0]['name'],
                    "image_desc": image[0]['description'],
                    "image_url": image[0]['link'], }
                image_data_list.append(image_properties)

        return image_data_list


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
            update_data['link'] = product_url
            data['product_url'] = product_url

        # Temporary unavailable field
        # if source_url:
        #     update_data['source_url'] = source_url
        #     data['source_url'] = source_url

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']

        tags = db.select('tags', where='pin_id = %s' % (image_id)).list()
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


class QueryCategory(BaseAPI):
    """
    API for receiving pins by category
    """
    def POST(self):
        request_data = web.input(
            category_id_list=[],
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        query_type = request_data.get("query_type")
        category_id_list = map(int,
                               request_data.get("category_id_list"))
        page = request_data.get("page")
        items_per_page = request_data.get("items_per_page")

        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']

        image_id_list = []
        if query_type == "all" or not query_type:
            for category_id in category_id_list:
                pins = db.select('pins_categories',
                                 where='category_id = %s' % (category_id))

                for pin in pins:
                    if pin['pin_id'] not in image_id_list:
                        image_id_list.append(pin['pin_id'])

        elif query_type == "new":
            timestamp_with_delta = int((datetime.datetime.utcnow() -
                                        datetime.timedelta(days=7))
                                       .strftime("%s"))
            for category_id in category_id_list:
                pins = db.query("SELECT * FROM pins_categories \
                                JOIN pins ON pins_categories.pin_id = pins.id \
                                WHERE pins_categories.category_id = %s and \
                                pins.timestamp >= %d" % (category_id,
                                                         timestamp_with_delta))

                for pin in pins:
                    if pin['pin_id'] not in image_id_list:
                        image_id_list.append(pin['pin_id'])

        elif query_type == "range":
            if not page:
                page = 1
            else:
                page = int(page)
                if page < 1:
                    page = 1
            if not items_per_page:
                items_per_page = 10
                if items_per_page < 1:
                    items_per_page = 1
            else:
                items_per_page = int(items_per_page)

            for category_id in category_id_list:
                pins = db.select('pins_categories',
                                 where='category_id = %s' % (category_id))

                for pin in pins:
                    if pin['pin_id'] not in image_id_list:
                        image_id_list.append(pin['pin_id'])

            data['pages_count'] = math.ceil(float(len(image_id_list)) /
                                            float(items_per_page))
            data['pages_count'] = int(data['pages_count'])
            data['page'] = page
            data['items_per_page'] = items_per_page

            start = (page-1) * items_per_page
            end = start + items_per_page
            image_id_list = image_id_list[start:end]

        data['image_id_list'] = image_id_list

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response
