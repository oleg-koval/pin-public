import json
import logging

import web

from mypinnings import database
from mypinnings import session
from mypinnings import template
from mypinnings import cached_models
from mypinnings.conf import settings
from mypinnings import auth
from mypinnings.api import api_request, convert_to_id, convert_to_logintoken


logger = logging.getLogger('mypinnings.categories')


class PageCategory:
    def GET(self, slug=None):
        self.db = database.get_db()
        self.sess = session.get_session()
        auth.force_login(self.sess)
        if slug:
            results = self.db.where('categories', slug=slug)
            for r in results:
                self.category = r
                break
            else:
                self.category = {'name': 'Random', 'id': 0}
        else:
            self.category = {'name': 'Random', 'id': 0}

        self.ajax = int(web.input(ajax=0).ajax)

        if self.ajax:
            return self.get_more_items_as_json()
        else:
            return self.template_for_showing_categories()

    def get_items_query(self):
        if self.category['id'] == 0:
            self.where = 'random() < 0.1'
        else:
            results = self.db.where(table='categories',
                                    parent=self.category['id'])
            subcategories_ids = [str(self.category['id'])]
            for row in results:
                subcategories_ids.append(str(row.id))
            subcategories_string = ','.join(subcategories_ids)
            self.where = 'categories.id in ({})'.format(subcategories_string)
        start = web.input(start=False).start
        if start:
            offset = 0
            self.sess['offset'] = 0
        else:
            offset = self.sess.get('offset', 0)
        self.query = '''
            select
                tags.tags, pins.*, categories.id as category,
                categories.name as cat_name, users.pic as user_pic,
                users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join follows on follows.follow = users.id
                join pins_categories on pins.id=pins_categories.pin_id
                join categories
                on pins_categories.category_id = categories.id
            where ''' + self.where + '''
            group by tags.tags, categories.id, pins.id, users.id
            order by timestamp desc
            offset %d limit %d''' % \
            (offset * settings.PIN_COUNT, settings.PIN_COUNT)
        return self.query

    def template_for_showing_categories(self):
        subcategories = self.db.where(
            table='categories',
            parent=self.category['id'],
            order='is_default_sub_category desc, name'
        )
        results = self.db.where(table='categories',
                                parent=self.category.get('parent'),
                                order='is_default_sub_category desc, name')
        siblings_categories = []
        for row in results:
            if row.id != self.category['id']:
                siblings_categories.append(row)
        results = self.db.where(table='categories',
                                id=self.category.get('parent'))
        for row in results:
            parent = row
            break
        else:
            parent = None
        boards = self.db.where(table='boards',
                               order='name',
                               user_id=self.sess.user_id)

        return template.ltpl('category',
                             self.category,
                             cached_models.all_categories,
                             subcategories,
                             boards,
                             siblings_categories,
                             parent)

    def get_items(self):
        start = web.input(start=False).start
        if start:
            offset = 1
            self.sess['offset'] = 1
        else:
            offset = self.sess.get('offset', 1)

        if offset == 0:
            return []

        logintoken = convert_to_logintoken(self.sess.get('user_id'))
        data = {
            "csid_from_client": '',
            "logintoken": logintoken,
            "page": offset,
            "query_type": "range",
            "items_per_page": settings.PIN_COUNT
        }

        if self.category['id'] != 0:
            results = self.db.where(table='categories',
                                    parent=self.category['id'])
            data['category_id_list'] = [self.category['id']]
            for row in results:
                data['category_id_list'].append(str(row.id))

        data = api_request("api/image/query/category", "POST", data)
        if data['status'] == 200:
            if offset >= data['data']['pages_count']:
                self.sess['offset'] = 0
            data_for_image_query = {
                "csid_from_client": '',
                "logintoken": logintoken,
                "query_params": data['data']['image_id_list']
            }
            data_from_image_query = api_request("api/image/query",
                                                "POST",
                                                data_for_image_query)

            if data_from_image_query['status'] == 200:
                return data_from_image_query['data']['image_data_list']

        return []

    def get_more_items_as_json(self):
        # self.get_items_query()
        # pins = self.db.query(self.query)
        pins = self.get_items()
        pin_list = []
        for pin in pins:
            pin_list.append(pin)

        offset = self.sess.get('offset', 1)
        if offset > 0 and len(pin_list) > 0:
            offset = offset + 1
        self.sess['offset'] = offset
        json_pins = json.dumps(pin_list)
        return json_pins
