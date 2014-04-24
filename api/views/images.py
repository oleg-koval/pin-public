""" Implements images part of the API """
import os
import web
import uuid

from api.views.base import BaseAPI
from api.utils import api_response, save_api_request
from mypinnings.conf import settings
from mypinnings.database import connect_db

db = connect_db()


class ImageUpload(BaseAPI):
    """ Handles image upload and storing it on the file system """
    def POST(self):
        """ Images upload main handler

        Can be tested using the following command:
        curl -F -F "image_title=some_title" -F "image_descr=some_descr" \
        -F "use_for=some text" -F "image_file=@/home/oleg/Desktop/hard.jpg" \
        http://localhost:8080/api/image/upload
        """
        request_data = web.input(image_file={})
        save_api_request(request_data)
        file_obj = request_data.get('image_file')
        # For some reason, FileStorage object treats itself as False
        if type(file_obj) == dict:
            return api_response(data={}, status=405,
                                error_code="Required args are missing")

        file_path = self.save_file(file_obj)
        image_kwargs = {'image_title': request_data.get("image_title"),
                        'image_descr': request_data.get("image_descr"),
                        'use_for': request_data.get("use_for")}
        self.create_db_record(file_path, image_kwargs)
        response = {}
        if file_path:
            response["image_file"] = file_path
        return api_response(data=response)

    def create_db_record(self, file_path, kwargs):
        """
        Creates image record in the database.
        """
        # Do not record empty fields
        kwargs = {key: value for (key, value) in kwargs.items()
                  if value is not None}
        db.insert("images", image_file=file_path, **kwargs)

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
