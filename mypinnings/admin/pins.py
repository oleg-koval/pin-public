from datetime import date

import web

from mypinnings import template
from mypinnings import database
from mypinnings import session
from mypinnings.admin.auth import login_required


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
        return web.template.frender('t/admin/pin_search_list.html')(results, date)
    
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
            return template.admin.pin_error('No user to search')
        user_id_list = [str(row.id) for row in results]
        user_ids = ','.join(user_id_list)
        results = db.select(tables='pins', where='user_id in ({})'.format(user_ids),
                            limit=PAGE_SIZE, offset=(PAGE_SIZE * self.page),
                            order='{} {}'.format(self.sort, self.sort_direction))
        return web.template.frender('t/admin/pin_search_list.html')(results, date)


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
