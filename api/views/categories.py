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

db = connect_db()


class GetCategories(BaseAPI):
    """
    API for receiving list of categories
    """
    def POST(self):
        request_data = web.input(
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        csid_from_client = request_data.get('csid_from_client')
        csid_from_server = ""

        data['categories_list'] = list(
        	db.select(
	        	'categories', 
	        	order='position desc, name',
	            where='parent is null'
	        )
	    )

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response