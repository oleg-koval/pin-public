#!/usr/bin/python
import web
from web import form
import random
import string
import hashlib
import json
import logging
import os
import os.path

from PIL import Image

from mypinnings import database
from mypinnings import session
from mypinnings import template
from mypinnings import cached_models


logger = logging.getLogger('admin')

PASSWORD = 'davidfanisawesome'

urls = ('', 'admin.PageIndex',
        '/', 'admin.PageIndex',
        '/login', 'admin.PageLogin',
        '/search', 'admin.PageSearch',
        '/search/(all)', 'admin.PageSearch',
        '/create', 'admin.PageCreate',
        '/user/(\d*)', 'admin.PageUser',
        '/closeuser/(\d*)', 'admin.PageCloseUser',
        '/edituser/(\d*)', 'admin.PageEditUser',
        '/createuser', 'admin.PageCreateUser',
        '/logout', 'admin.PageLogout',
        '/relationships', 'admin.PageRelationships',
        '/categories', 'ListCategories',
        '/category-manage_cool/(\d*)', 'EditCoolProductsForCategory',
        '/category-cool-items/(\d*)/?', 'ListCoolProductsForCategory',
        '/api/categories/(\d*)/pins/?', 'ApiCategoryListPins',
        '/api/categories/(\d*)/pins/(\d*)/?', 'ApiCategoryPins',
#         '/api/categories/(\d*)/cool_pins', 'ApiategoryCoolPins'
         '/api/categories/(\d*)/cool_pins/(\d*)/?', 'ApiCategoryCoolPins'
        )


def lmsg(msg):
    return template.admin.msg(msg)


def login():
    sess = session.get_session()
    if 'ok' not in sess or not sess['ok']:
        raise web.seeother('/login')

def login_required(f):
    '''
    Decorator to force login
    '''
    def not_logged_in(self, *args, **kwargs):
        sess = session.get_session()
        if 'ok' not in sess or not sess['ok']:
            raise web.seeother('/login')
        else:
            return f(self, *args, **kwargs)
    return not_logged_in


class PageIndex:
    def GET(self):
        login()
        return template.admin.index()


class PageLogin:
    _form = form.Form(
        form.Password('password'),
        form.Button('login')
    )

    def GET(self):
        sess = session.get_session()
        sess['ok'] = False
        return web.template.frender('t/admin/form.html')(self._form, 'Login')
        return template.admin.form(self._form, 'Login')

    def POST(self):
        sess = session.get_session()
        form = self._form()
        if not form.validates():
            return 'houston we have a problem'

        if form.d.password != PASSWORD:
            return 'password incorrect'

        sess.ok = True
        raise web.seeother('/')


class PageLogout:
    def GET(self):
        sess = session.get_session()
        sess.kill()
        raise web.seeother('/')


class PageRelationships:
    def GET(self):
        db = database.get_db()
        follows = db.query('''
            select
                follows.*,
                u1.name as follower_name,
                u2.name as following_name,
                u1.username as follower_username,
                u2.username as following_username
            from follows
                join users u1 on u1.id = follows.follower
                join users u2 on u2.id = follows.follow''')

        friends = db.query('''
            select
                friends.*,
                u1.name as u1_name,
                u2.name as u2_name,
                u1.username as u1_username,
                u2.username as u2_username
            from friends
                join users u1 on u1.id = friends.id1
                join users u2 on u2.id = friends.id2''')
        return template.admin.relations(follows, friends)



USERS_QUERY = '''
    select
        users.*,
        count(distinct f1) as follower_count,
        count(distinct f2) as follow_count,
        count(distinct p1) as repin_count,
        count(distinct p2) as pin_count,
        count(distinct friends) as friend_count
    from users
        left join follows f1 on f1.follow = users.id
        left join follows f2 on f2.follower = users.id
        left join friends on (friends.id1 = users.id or
                              friends.id2 = users.id)
        left join pins p1 on p1.repin = users.id
        left join pins p2 on p2.user_id = users.id
        %s
        group by users.id'''


class PageSearch:
    _form = form.Form(
        form.Textbox('query'),
        form.Button('search')
    )

    def GET(self, allusers=None):
        login()

        params = web.input(order=None, query=None)
        order = params.order

        def make_query(query):
            if order is not None:
                return query + (' order by %s desc' % order)
            return query

        if allusers is not None:
            query = make_query(USERS_QUERY % '')
            db = database.get_db()
            results = db.query(query)
            return template.admin.search(results)

        search_query = params.query
        if search_query is None:
            return template.admin.searchform(self._form(), params)

        query = make_query(USERS_QUERY % '''
            where
                users.email ilike $search or
                users.name ilike $search or
                users.about ilike $search''')

        results = db.query(query, vars={'search': '%%%s%%' % search_query})
        return template.admin.search(results)


class PageUser:
    def GET(self, user_id):
        user_id = int(user_id)
        db = database.get_db()
        user = db.query('''
            select
                users.*,
                count(f1.follow) as follower_count,
                count(f2.follow) as follow_count,
                count(pins.id) as repin_count,
                count(friends) as friend_count
            from users
                left join follows f1 on f1.follow = users.id
                left join follows f2 on f2.follower = users.id
                left join friends on (friends.id1 = users.id or
                                 friends.id2 = users.id)
                left join pins on pins.repin = users.id
            where users.id = $id
            group by users.id''', vars={'id': user_id})
        if not user:
            return 'user not found'
        return template.admin.user(user[0])


class PageCloseUser:
    def GET(self, user_id):
        login()
        user_id = int(user_id)
        db = database.get_db()
        db.query('delete from pins where user_id = $id', vars={'id': user_id})
        db.query('delete from users where id = $id', vars={'id': user_id})
        raise web.seeother('/')


class PageEditUser:
    def make_form(self, user=None):
        user = user or dict()
        return form.Form(
            form.Textbox('name', value=user.get('name')),
            form.Textbox('email', value=user.get('email')),
            form.Textarea('about', value=user.get('about')),
            form.Button('update'))()

    def GET(self, user_id):
        login()
        user_id = int(user_id)
        db = database.get_db()
        user = db.select('users', where='id = $id', vars={'id': user_id})
        if not user:
            return 'That user does not exist.'
        return template.admin.edituser(self.make_form(user[0]))

    def POST(self, user_id):
        login()
        user_id = int(user_id)
        form = self.make_form()
        if not form.validates():
            return 'invalid form input'

        d = dict(form.d)
        del d['update']
        db = database.get_db()
        db.update('users', where='id = $id', vars={'id': user_id}, **d)
        raise web.seeother('/edituser/%d' % user_id)


def email_exists(email):
    db = database.get_db()
    result = db.select('users',
        what='1',
        where='email=$email',
        vars={'email': email},
        limit=1)
    return bool(result)


def hash(data):
    return hashlib.sha1(data).hexdigest()


def create_user(email, password, **params):
    pw_hash = hash(password)
    pw_salt = generate_salt()
    pw_hash = hash(pw_hash + pw_salt)
    db = database.get_db()
    return db.insert('users', email=email, pw_hash=pw_hash, pw_salt=pw_salt, **params)


def generate_salt(length=10):
    random.seed()
    pool = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(pool) for i in range(length))


def username_exists(username):
    db = database.get_db()
    result = db.select('users',
        what='1',
        where='username=$username',
        vars={'username': username},
        limit=1)
    return bool(result)


class PageCreateUser:
    _form = form.Form(
        form.Textbox('email'),
        form.Textbox('name'),
        form.Textbox('username'),
        form.Password('password'),
        form.Button('create account')
    )

    def GET(self):
        login()
        form = self._form()
        return template.admin.reg(form)

    def POST(self):
        login()
        form = self._form()
        if not form.validates():
            return 'bad input'

        if email_exists(form.d.email):
            return 'email already exists'

        if username_exists(form.d.username):
            return 'username already exists'

        user_id = create_user(form.d.email, form.d.password, name=form.d.name, username=form.d.username)
        if not user_id:
            return 'couldn\'t create user'

        raise web.seeother('/user/%d' % user_id)


class ListCategories(object):
    '''
    Shows the category list to edit them and change its properties
    '''
    @login_required
    def GET(self):
        return template.admin.list_categories(cached_models.all_categories)


COOL_LIST_LIMIT = 50

class EditCoolProductsForCategory(object):
    '''
    Allows edition of cool products for one category
    '''
    @login_required
    def GET(self, category_id):
        db = database.get_db()
        offset = int(web.input(offset=0)['offset'])
        if offset < 0:
            offset = 0
        pins = db.select(tables=['pins'], what="pins.*", order='timestamp desc',
                         where='pins.category=$category_id and pins.id not in (select pin_id from cool_pins where cool_pins.category_id=$category_id)',
                         vars={'category_id': category_id}, offset=offset, limit=COOL_LIST_LIMIT)
        categories = db.where(table='categories', id=category_id)
        for c in categories:
            category = c
        json_pins = []
        for pin in pins:
            image_name = 'static/tmp/{}.png'.format(pin.id)
            thumb_image_name = 'static/tmp/pinthumb{}.png'.format(pin.id)
            if os.path.exists(thumb_image_name):
                pin.image_name = '/' + thumb_image_name
            elif os.path.exists(image_name):
                pin.image_name = '/' + image_name
            else:
                continue
            json_pins.append(json.dumps(pin))
        prev = offset - COOL_LIST_LIMIT if offset > COOL_LIST_LIMIT else 0
        next = offset + COOL_LIST_LIMIT
        return template.admin.edit_cool_products_category(category, json_pins, prev, next)


class ListCoolProductsForCategory(object):
    @login_required
    def GET(self, category_id):
        db = database.get_db()
        offset = int(web.input(offset=0)['offset'])
        if offset < 0:
            offset = 0
        pins = db.select(tables=['pins', 'cool_pins'], what="pins.*", order='timestamp desc',
                         where='pins.category=$category_id and pins.id=cool_pins.pin_id',
                         vars={'category_id': category_id})
        pins_list = []
        for pin in pins:
            image_name = 'static/tmp/{}.png'.format(pin.id)
            thumb_image_name = 'static/tmp/pinthumb{}.png'.format(pin.id)
            if os.path.exists(thumb_image_name):
                pin.image_name = '/' + thumb_image_name
            elif os.path.exists(image_name):
                pin.image_name = '/' + image_name
            else:
                pin.image_name = ''
            pins_list.append(pin)
        return web.template.frender('t/admin/category_cool_items_list.html')(pins_list)


class ApiCategoryListPins(object):
    '''
    API to list and serach the pins in a category
    '''
    @login_required
    def GET(self, category_id):
        '''
        Searches or returns all pins in this category_id.

        The results are paginated using offset and limit
        '''
        db = database.get_db()
        search_terms = web.input(search_terms=None)['search_terms']
        try:
            search_limit = int(web.input(limit='10')['limit'])
        except ValueError:
            search_limit = 10
        else:
            if search_limit > 50: search_limit = 50
            if search_limit < 5: search_limit = 5
        try:
            search_offset = int(web.input(offset='0')['offset'])
        except ValueError:
            search_offset = 0
        else:
            if search_offset < 0: search_offset = 0
        if search_terms:
            search_terms = "%{}%".format(search_terms.lower())
            pins = db.select(tables=['pins'], order='name',
                             where='category=$category_id and (lower(name) like $search or lower(description) like $search)'
                                ' and id not in (select pin_id from cool_pins where category=$category_id)',
                             vars={'category_id': category_id, 'search': search_terms},
                             limit=search_limit, offset=search_offset)
        else:
            pins = db.select(tables='pins', order='name',
                             where='category=$category_id'
                                ' and id not in (select pin_id from cool_pins where category=$category_id)',
                             vars={'category_id': category_id, 'search': search_terms},
                             limit=search_limit, offset=search_offset)
        list_of_pins = []
        for p in pins:
            list_of_pins.append(dict(p))
        web.header('Content-Type', 'application/json')
        return json.dumps({'limit': search_limit, 'offset': search_offset, 'list_of_pins': list_of_pins,
                           'search_terms': search_terms})


class ApiCategoryPins(object):
    '''
    '''
    @login_required
    def GET(self, pin_id):
        db = database.get_db()
        query_results = db.where(table='pins', id=pin_id)
        pin = None
        for p in query_results:
            pin = dict(p)
        if pin:
            web.header('Content-Type', 'application/json')
            return json.dumps(pin)


class ApiCategoryCoolPins(object):
    '''
    API to manage cool pins in a category
    '''
    @login_required
    def PUT(self, category_id, pin_id):
        '''
        Puts the pin in the category's cool pins
        '''
        db = database.get_db()
        try:
            db.insert(tablename='cool_pins', category_id=category_id, pin_id=pin_id)
            image_name = os.path.join('static', 'tmp', str(pin_id)) + '.png'
            image = Image.open(image_name)
            if image.size[0] <= image.size[1]:
                ratio = 72.0 / float(image.size[0])
                height = int(ratio * image.size[1])
                image = image.resize((72, height), Image.ANTIALIAS)
                margin = (height - 72) / 2
                crop_box = (0, margin, 72, 72 + margin)
            else:
                ratio = 72.0 / float(image.size[1])
                width = int(ratio * image.size[0])
                image = image.resize((width, 72), Image.ANTIALIAS)
                margin = (width - 72) / 2
                crop_box = (margin, 0, 72 + margin, 72)
            image = image.crop(crop_box)
            new_name = os.path.join('static', 'tmp', str(pin_id)) + '_cool.png'
            image.save(new_name)
        except:
            db.delete(table='cool_pins', where='category_id=$category_id and pin_id=$pin_id',
                      vars={'category_id': category_id, 'pin_id': pin_id})
            logger.error('Could not add pin ({}) to cool pins for category ({})'.format(pin_id, category_id), exc_info=True)
            raise web.NotFound('Could not add pin to cool pins')
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})

    @login_required
    def DELETE(self, category_id, pin_id):
        '''
        Deletes the pin from the category's cool pins
        '''
        db = database.get_db()
        try:
            db.delete(table='cool_pins', where='category_id=$category_id and pin_id=$pin_id',
                      vars={'category_id': category_id, 'pin_id': pin_id})
            image_name = os.path.join('static', 'tmp', str(pin_id)) + '_cool.png'
            os.unlink(image_name)
        except OSError:
            # could not delete the image, nothing happens
            pass
        except:
            logger.error('Could not delete pin ({}) from cool pins for category ({})'.format(pin_id, category_id), exc_info=True)
            raise web.NotFound('Could not delete pin from cool pins')
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})


app = web.application(urls, locals())
