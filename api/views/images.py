import os
import web
import uuid

from api.views.base import BaseAPI
from api.utils import api_response, save_api_request


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
        upload_file = open(filepath,'w')
        upload_file.write(file_obj.image_file.file.read())
        upload_file.close()
        return filepath

    def get_media_path(self, media_dir="media"):
        current_path = os.path.realpath(os.path.dirname(__file__))
        prj_dir = os.path.join(current_path,"..", "..")
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
    """
    def POST(self):
        """
        You can tested it using:
        curl --data "csid_from_client=1&query_type=all&image_data_list=[200,890]" \
        http://localhost:8080/api/image/query
        """
        request_data = web.input(query_params=[],)
        save_api_request(request_data)

        query_type = request_data.get("query_type")
        query_params = map(int, request_data.get("query_params"))
        image_data_list = []
        if len(query_params) > 0:
            image_data_list = self.query_image(query_params)
        
        csid_from_server = ''
        csid_from_client = request_data.get("csid_from_client")
        data = {
            "image_data_list": image_data_list,
        }
        response = api_response(data, 
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response

    def query_image(self, image_data_list):
        for param in query_params:
            pass
            
        image_properties = {
            "image_id":image_id,
            "image_title":image_title,
            "image_desc":image_desc,
            "image_url":image_url,
            "image_hash_tag":image_hash_tag,
            }
        return True
