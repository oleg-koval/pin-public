#!/usr/bin/python
import web
from web import form
import random
import string
import hashlib
import json
import logging
# #
from mypinnings import database
from mypinnings import session
from mypinnings import template
from mypinnings import cached_models

from mypinnings.admin.auth import login_required


logger = logging.getLogger('admin')

urls = ('', 'PageIndex',
        '/', 'PageIndex',
        '/login', 'mypinnings.admin.auth.PageLogin',
        '/logout', 'mypinnings.admin.auth.PageLogout',
        '/search', 'PageSearch',
        '/search/(all)', 'PageSearch',
        '/create', 'PageCreate',
        '/user/(\d*)', 'PageUser',
        '/closeuser/(\d*)', 'PageCloseUser',
        '/edituser/(\d*)', 'PageEditUser',
        '/createuser', 'PageCreateUser',
        '/relationships', 'PageRelationships',
        '/categories', 'ListCategories',
        '/cool-items-category/(\d*)', 'EditCoolProductsForCategory',
        '/api/categories/(\d*)/pins/?', 'ApiCategoryListPins',
        '/api/categories/(\d*)/pins/(\d*)/?', 'ApiCategoryPins',
#         '/api/categories/(\d*)/cool_pins', 'ApiategoryCoolPins'
         '/api/categories/(\d*)/cool_pins/(\d*)/?', 'ApiCategoryCoolPins'
        )


def lmsg(msg):
    return template.admin.msg(msg)


class PageIndex:
    @login_required()
    def GET(self):
        return template.admin.index()


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

    @login_required()
    def GET(self, allusers=None):
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
    @login_required()
    def GET(self, user_id):
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

    @login_required()
    def GET(self, user_id):
        user_id = int(user_id)
        db = database.get_db()
        user = db.select('users', where='id = $id', vars={'id': user_id})
        if not user:
            return 'That user does not exist.'
        return template.admin.edituser(self.make_form(user[0]))

    @login_required()
    def POST(self, user_id):
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

    @login_required()
    def GET(self):
        form = self._form()
        return template.admin.reg(form)

    @login_required()
    def POST(self):
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
    @login_required()
    def GET(self):
        return template.admin.list_categories(cached_models.all_categories)


class EditCoolProductsForCategory(object):
    '''
    Allows edition of cool products for one category
    '''
    @login_required()
    def GET(self, category_id):
        db = database.get_db()
        pins = db.select(tables=['pins', 'cool_pins'], order='pins.name',
                         where='cool_pins.category_id=$category_id and cool_pins.pin_id=pins.id',
                         vars={'category_id': category_id})
        categories = db.where(table='categories', id=category_id)
        for c in categories:
            category = c
        return template.admin.edit_cool_products_category(category, pins)


class ApiCategoryListPins(object):
    '''
    API to list and serach the pins in a category
    '''
    @login_required()
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
    @login_required()
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
    @login_required()
    def PUT(self, category_id, pin_id):
        '''
        Puts the pin in the category's cool pins
        '''
        db = database.get_db()
        try:
            db.insert(tablename='cool_pins', category_id=category_id, pin_id=pin_id)
        except:
            logger.error('Could not add pin ({}) to cool pins for category ({})'.format(pin_id, category_id), exc_info=True)
            raise web.NotFound('Could not add pin to cool pins')
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})

    @login_required()
    def DELETE(self, category_id, pin_id):
        '''
        Deletes the pin from the category's cool pins
        '''
        db = database.get_db()
        try:
            db.delete(table='cool_pins', where='category_id=$category_id and pin_id=$pin_id',
                      vars={'category_id': category_id, 'pin_id': pin_id})
        except:
            logger.error('Could not delete pin ({}) from cool pins for category ({})'.format(pin_id, category_id), exc_info=True)
            raise web.NotFound('Could not delete pin from cool pins')
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})


app = web.application(urls, locals())
