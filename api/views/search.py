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


class SearchItems(BaseAPI):
    """
    API for receiving pins ids by query
    """
    def POST(self):
        request_data = web.input(
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        query = request_data.get("query", None)
        page = request_data.get("page")
        items_per_page = request_data.get("items_per_page", 10)

        csid_from_client = request_data.get('csid_from_client')
        csid_from_server = ""

        if not query:
            status = 400
            error_code = "Invalid input data"
        else:
            data = self.get_range(query,
                                  page,
                                  items_per_page)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response

    def get_range(self, query, page, items_per_page):
        data = {}
        image_id_list = []

        if page:
            page = int(page)
            if page < 1:
                page = 1

        if not items_per_page:
            items_per_page = 10
            if items_per_page < 1:
                items_per_page = 1
        else:
            items_per_page = int(items_per_page)

        query = make_query(query)

        query = """
            select
                pins.id as pin_id,
                ts_rank_cd(to_tsvector(tags.tags), query) as rank1,
                ts_rank_cd(pins.tsv, query) as rank2
            from pins
                left join tags on tags.pin_id = pins.id
                join to_tsquery('""" + query + """') query on true
                left join users on users.id = pins.user_id
                left join categories on categories.id in
                    (select category_id from pins_categories
                    where pin_id = pins.id limit 1)
            where query @@ pins.tsv or query @@ to_tsvector(tags.tags)
            group by tags.tags, categories.id, pins.id, users.id, query.query
            order by rank1, rank2 desc"""

        pins = db.query(query).list()

        for pin in pins:
            if pin['pin_id'] not in image_id_list:
                image_id_list.append(pin['pin_id'])

        if page:
            data['pages_count'] = math.ceil(float(len(image_id_list)) /
                                            float(items_per_page))
            data['pages_count'] = int(data['pages_count'])
            data['page'] = page
            data['items_per_page'] = items_per_page

            start = (page-1) * items_per_page
            end = start + items_per_page
            data['image_id_list'] = image_id_list[start:end]
        else:
            data['image_id_list'] = image_id_list

        return data


class SearchPeople(BaseAPI):
    """
    API for receiving users by query
    """
    def POST(self):
        request_data = web.input(
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        query = request_data.get("query", None)
        page = request_data.get("page")
        items_per_page = request_data.get("items_per_page", 10)

        csid_from_client = request_data.get('csid_from_client')
        csid_from_server = ""

        logintoken = request_data.get('logintoken')

        user_status, user = self.authenticate_by_token(logintoken)
        # User id contains error code
        if not user_status:
            return user

        user_id = user['id']

        if not query:
            status = 400
            error_code = "Invalid input data"
        else:
            data = self.get_range(query,
                                  page,
                                  items_per_page,
                                  user_id)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response

    def get_range(self, query, page, items_per_page, user_id):
        data = {}
        users = []

        if page:
            page = int(page)
            if page < 1:
                page = 1

        if not items_per_page:
            items_per_page = 10
            if items_per_page < 1:
                items_per_page = 1
        else:
            items_per_page = int(items_per_page)

        query = make_query(query)

        query = """
            select
                users.*, ts_rank_cd(users.tsv, query) as rank,
                count(distinct f1) <> 0 as is_following
            from users
                join to_tsquery('""" + query + """') query on true
                left join follows f1 on f1.follower = $user_id
                and f1.follow = users.id
            where query @@ users.tsv group by users.id, query.query
            order by rank desc"""

        users = db.query(query, vars={'user_id': user_id}).list()

        if page:
            data['pages_count'] = math.ceil(float(len(users)) /
                                            float(items_per_page))
            data['pages_count'] = int(data['pages_count'])
            data['page'] = page
            data['items_per_page'] = items_per_page

            start = (page-1) * items_per_page
            end = start + items_per_page
            data['users'] = users[start:end]
        else:
            data['users'] = users

        return data


def make_query(q):
    q = ''.join([x if x.isalnum() else ' ' for x in q])
    while '  ' in q:
        q = q.replace('  ', ' ')

    return q.replace(' ', ' | ')
