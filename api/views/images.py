""" Implements images part of the API """
import os
import web
import uuid
import datetime
import math
import random

from mypinnings import database
from api.views.base import BaseAPI
from api.utils import api_response, save_api_request
from mypinnings.database import connect_db
from mypinnings.conf import settings
from mypinnings.media import store_image_from_filename

db = connect_db()

DIGITS_AND_LETTERS = \
    'abcdefghijklmnopqrstuvwxwzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'


class ImageUpload(BaseAPI):
    """ Handles image upload and storing it on the file system """
    def POST(self):
        """ Images upload main handler

        Can be tested using the following command:
        curl -F "image_title=some_title" -F "image_descr=some_descr" \
        -F "image_file=@/home/oleg/Desktop/hard.jpg" \
        http://localhost:8080/api/image/upload
        """
        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        request_data = web.input(image_file={})
        logintoken = request_data.get('logintoken')

        user_status, user = self.authenticate_by_token(logintoken)
        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        csid_from_client = request_data.get("csid_from_client")

        save_api_request(request_data)
        file_obj = request_data.get('image_file')

        # For some reason, FileStorage object treats itself as False
        if type(file_obj) == dict:
            return api_response(data={}, status=405,
                                error_code="Required args are missing")

        file_path = self.save_file(file_obj)
        images_dict = store_image_from_filename(db,
                                                file_path,
                                                widths=(202, 212))

        external_id = _generate_external_id()

        image_kwargs = {'name': request_data.get("image_title"),
                        'description': request_data.get("image_descr"),
                        'user_id': user['id'],
                        'link': request_data.get("link"),
                        'product_url': request_data.get("product_url"),
                        'price': request_data.get("price"),
                        'price_range': request_data.get("price_range"),
                        'board_id': request_data.get("board_id"),
                        'external_id': external_id,
                        'image_url': images_dict[0]['url'],
                        'image_width': images_dict[0]['width'],
                        'image_height': images_dict[0]['height'],
                        'image_202_url': images_dict[202]['url'],
                        'image_202_height': images_dict[202]['height'],
                        'image_212_url': images_dict[212]['url'],
                        'image_212_height': images_dict[212]['height']}

        pin_id = self.create_db_record(image_kwargs)

        data['image_id'] = pin_id
        data['external_id'] = external_id

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)

        return response

    def create_db_record(self, kwargs):
        """
        Creates image record in the database.
        """
        # Do not record empty fields
        kwargs = {key: value for (key, value) in kwargs.items()
                  if value is not None}
        return db.insert("pins", **kwargs)

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
        link = request_data.get("link")
        price_range = request_data.get("price_range")
        board_id = request_data.get("board_id")
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
        if link:
            update_data['link'] = link
            data['link'] = link
        if price_range:
            update_data['price_range'] = price_range
            data['price_range'] = price_range
        if board_id:
            update_data['board_id'] = board_id
            data['board_id'] = board_id

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

            pins = db.select('pins', where='id = %s' % (image_id)).list()
            if len(pins) > 0:
                 data['external_id'] = pins[0]['external_id']

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

        if query_type == "all" or not query_type:
            data = self.get_all(category_id_list)

        elif query_type == "new":
            data = self.get_new(category_id_list)

        elif query_type == "range":
            data = self.get_range(category_id_list, page, items_per_page)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response

    def get_all(self, category_id_list):
        data = {}
        image_id_list = []
        for category_id in category_id_list:
            pins = db.select('pins_categories',
                             where='category_id = %s' % (category_id))\
                .list()

            for pin in pins:
                if pin['pin_id'] not in image_id_list:
                    image_id_list.append(pin['pin_id'])

        data['image_id_list'] = image_id_list

        return data

    def get_new(self, category_id_list):
        data = {}
        image_id_list = []
        timestamp_with_delta = int(
            (
                datetime.datetime.utcnow() -
                datetime.timedelta(days=settings.PIN_NEW_DAYS)
            )
            .strftime("%s")
        )
        for category_id in category_id_list:
            pins = db.query("SELECT * FROM pins_categories \
                            JOIN pins ON pins_categories.pin_id = pins.id \
                            WHERE pins_categories.category_id = %s and \
                            pins.timestamp >= %d" % (category_id,
                                                     timestamp_with_delta))\
                .list()

            for pin in pins:
                if pin['pin_id'] not in image_id_list:
                    image_id_list.append(pin['pin_id'])

        data['image_id_list'] = image_id_list

        return data

    def get_range(self, category_id_list, page, items_per_page):
        data = {}
        image_id_list = []

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
                             where='category_id = %s' % (category_id))\
                .list()

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
        data['image_id_list'] = image_id_list[start:end]

        return data


class QueryHashtags(BaseAPI):
    """
    API method for get hashtags of pin
    """
    def POST(self):
        request_data = web.input()

        update_data = {}
        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        image_id = request_data.get("image_id")

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
            tags = db.select('tags', where='pin_id = %s' % (image_id)).list()
            if len(tags) > 0:
                tags = tags[0]['tags'].split()
            else:
                tags = []

            data['hashtag_list'] = tags

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


def _generate_external_id():
    id = _new_external_id()
    while _already_exists(id):
        id = _new_external_id()
    return id


def _new_external_id():
    digits_and_letters = random.sample(DIGITS_AND_LETTERS, 9)
    return ''.join(digits_and_letters)


def _already_exists(id):
    db = database.get_db()
    results = db.where('pins', external_id=id)
    for _ in results:
        return True
    return False
