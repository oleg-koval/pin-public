import json
import os.path
import logging

import web
from PIL import Image

from mypinnings import database
from mypinnings import session
from mypinnings import template
from mypinnings import cached_models
from mypinnings.conf import settings
from mypinnings import image_utils
from mypinnings import auth


logger = logging.getLogger('mypinnings.categories')


class PageCategory:
    def GET(self, cid):
        self.cid = int(cid)
        self.db = database.get_db()
        self.sess = session.get_session()
        auth.force_login(self.sess)
        if self.cid == 0:
            self.category = {'name':'Random', 'id': 0}
        else:
            results = self.db.where('categories', id=cid)
            for r in results:
                self.category = r
                break
            else:
                return 'Category not found.'

        self.ajax = int(web.input(ajax=0).ajax)
        
        if self.ajax:
            return self.get_more_items_as_json()
        else:
            return self.template_for_showing_categories()
        
    def get_items_query(self):
        if self.cid == 0:
            self.where = 'random() < 0.1'
        else:
            self.where = 'categories.id = $cid'
        start = web.input(start=False).start
        if start:
            offset = 0
            self.sess['offset'] = 0
        else:
            offset = self.sess.get('offset', 0)
        self.query = '''
            select
                tags.tags, pins.*, categories.id as category, categories.name as cat_name, users.pic as user_pic,
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
                join categories on pins_categories.category_id = categories.id
            where ''' + self.where + '''
            group by tags.tags, categories.id, pins.id, users.id
            order by timestamp desc offset %d limit %d''' % (offset * settings.PIN_COUNT, settings.PIN_COUNT)
        return self.query

    def template_for_showing_categories(self):
        self.get_items_query()
        subcategories = self.db.where(table='categories', parent=self.cid, order='is_default_sub_category desc, name')
        existsrs = self.db.query('select exists(' + self.query + ') as exists', vars={'cid': self.cid})
        for r in existsrs:
            if not r.exists:
                subcatrs = self.db.where(table='categories', parent=self.cid, is_default_sub_category=True)
                for scrow in subcatrs:
                    cid = scrow.id
                    name = scrow.name
                    return web.seeother('/category/{}/{}'.format(name, cid), absolute=True)
        boards = self.db.where(table='boards', order='name', user_id=self.sess.user_id)
        return template.ltpl('category', self.category, cached_models.all_categories, subcategories, boards)

    def get_more_items_as_json(self):
        self.get_items_query()
        pins = self.db.query(self.query, vars={'cid': self.cid})
        pin_list = []
        for pin in pins:
            if not image_utils.create_thumbnail_212px_for_pin(pin):
                continue
            pin_list.append(pin)
            pin.price = str(pin.price)
        offset = self.sess.get('offset', 0)
        if len(pin_list) > 0:
            offset = offset + 1
        self.sess['offset'] = offset
        json_pins = json.dumps(pin_list)
        return json_pins
