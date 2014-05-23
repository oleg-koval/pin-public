from datetime import date
import urllib
import os.path

import web

from mypinnings import template
from mypinnings import database
from mypinnings import session
from mypinnings.admin.auth import login_required
from mypinnings import pin_utils


class Search(object):
    def GET(self):
        return template.admin.pins_search()


class SearchCriteria(object):
    @login_required
    def GET(self):
        data = web.input(pin_url=None,
                         username=None,
                         name=None,
                         email=None)
        sess = session.get_session()
        sess['search_pin_url'] = data.pin_url
        sess['search_username'] = data.username
        sess['search_name'] = data.name
        sess['search_email'] = data.email
        sess['search_reset_offset'] = True
        return ''


PAGE_SIZE = 100


class SearchPagination(object):
    @login_required
    def GET(self):
        data = web.input(page=1, dir='desc', sort='pins.timestamp')
        sess = session.get_session()
        reset_offset = sess.get('search_reset_offset', False)
        if reset_offset:
            self.page = 0
            sess['search_reset_offset'] = False
        else:
            self.page = int(data.page) - 1
        self.sort = data.sort
        self.sort_direction = data.dir
        self.pin_url = sess.get('search_pin_url', None)
        if self.pin_url:
            return self.find_by_pin_url()
        else:
            self.username = sess.get('search_username', False)
            self.full_name = sess.get('search_name', False)
            self.email = sess.get('search_email', False)
            return self.find_by_user_id()
    
    def find_by_pin_url(self):
        if '/' in self.pin_url:
            # is a path
            external_id = self.pin_url.split('/')[-1]
        else:
            external_id = self.pin_url
        db = database.get_db()
        results = db.where(table='pins', external_id=external_id)
        pins = []
        for row in results:
            pins.append(row)
        if pins:
            return web.template.frender('t/admin/pin_search_list.html')(pins, date)
        else:
            return web.template.frender('t/admin/pin_search_list.html')(self.empty_results(), date)
    
    def find_by_user_id(self):
        db = database.get_db()
        if self.username:
            results = db.select(tables='users', where='username=$username',
                                vars={'username': self.username})
        elif self.full_name:
            results = db.select(tables='users',
                                where="name like '%%{query}%%'".format(query=self.full_name),
                                )
        elif self.email:
            results = db.select(tables='users', where='email=$email',
                                vars={'email': self.emails})
        else:
            return web.template.frender('t/admin/pin_search_list.html')(self.empty_results(), date)
        user_id_list = [str(row.id) for row in results]
        if not user_id_list:
            return web.template.frender('t/admin/pin_search_list.html')(self.empty_results(), date)
        user_ids = ','.join(user_id_list)
        results = db.select(tables='pins', where='user_id in ({})'.format(user_ids),
                            limit=PAGE_SIZE, offset=(PAGE_SIZE * self.page),
                            order='{} {}'.format(self.sort, self.sort_direction))
        pins = []
        for row in results:
            pins.append(row)
        if pins:
            return web.template.frender('t/admin/pin_search_list.html')(pins, date)
        else:
            return web.template.frender('t/admin/pin_search_list.html')(self.empty_results(), date)
    
    def empty_results(self):
        class O(object):
            def __getattr__(self, name):
                if name == 'name':
                    return 'no items'
                elif name == 'timestamp':
                    return 0
                else:
                    return ''
        return [O(),]


class Pin(object):
    @login_required
    def GET(self, pin_id):
        db = database.get_db()
        pin = db.where(table='pins', id=pin_id)[0]
        selected_categories = set([c.category_id for c in db.where(table='pins_categories', pin_id=pin_id)]) 
        tags = db.where(table='tags', pin_id=pin_id)
        categories = [c for c in db.where(table='categories', order='position desc, name')]
        size = len(categories) / 3
        categories1 = categories[:size]
        categories2 = categories[size:2*size]
        categories3 = categories[2*size:]
        return template.admin.pin_edit_form(pin, selected_categories, tags, categories1, categories2, categories3)

    @login_required
    def POST(self, pin_id):
        db = database.get_db()
        pin = db.where(table='pins', id=pin_id)[0]
        data = web.input(image_file={})
        pin_utils.update_base_pin_information(db,
                                              pin_id=pin_id,
                                              user_id=pin.user_id,
                                              title=data.title,
                                              description=data.description,
                                              link=data.link,
                                              tags=data.tags,
                                              price=data.price,
                                              product_url=data.product_url,
                                              price_range=data.price_range,
                                              board_id=pin.board_id)
        categories = [int(v) for k, v in data.items() if k.startswith('category')]
        pin_utils.update_pin_into_categories(db=db,
                                             pin_id=pin_id,
                                             category_id_list=categories)
        if data.image_url:
            filename, _ = urllib.urlretrieve(data.image_url)
            pin_utils.update_pin_images(db=db,
                                        pin_id=pin_id,
                                        user_id=pin.user_id,
                                        image_filename=filename)
        elif data['image_file'].filename:
            filename = os.path.split(data['image_file'].filename)[-1]
            filename = os.path.join('static', 'tmp', filename)
            with open(filename, 'w') as f:
                f.write(data['image_file'].file.read())
            pin_utils.update_pin_images(db=db,
                                        pin_id=pin_id,
                                        user_id=pin.user_id,
                                        image_filename=filename)
        return web.seeother('{}'.format(pin_id))