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
import datetime
from gettext import gettext as _

from PIL import Image

from mypinnings import database
from mypinnings import session
from mypinnings import template
from mypinnings import cached_models
from mypinnings.conf import settings
from mypinnings import form_controls
from mypinnings import auth
from mypinnings.admin.auth import login
from mypinnings.admin import dataloaders
from mypinnings import pin_utils


logger = logging.getLogger('admin')

PASSWORD = 'davidfanisawesome'

urls = ('', 'admin.PageIndex',
        '/', 'admin.PageIndex',
        '/login', 'admin.PageLogin',
        '/search', 'admin.PageSearch',
        '/search/(all)', 'admin.PageSearch',
        '/search-results', 'admin.PageSearchResults',
        '/dataloaders-results', 'mypinnings.admin.dataloaders.Results',
        '/dataloaders-results/pagination', 'mypinnings.admin.dataloaders.ResultsPagination',
        '/create', 'admin.PageCreate',
        '/user/(\d*)/change_password', 'admin.ChangePassword',
        '/user/(\d*)/change_pic/', 'admin.ChangeUserPicture',
        '/user/(\d*)', 'admin.PageUser',
        '/closeuser/(\d*)', 'admin.PageCloseUser',
        '/edituser/(\d*)', 'admin.PageEditUser',
        '/createuser', 'admin.PageCreateUser',
        '/logout', 'admin.PageLogout',
        '/relationships', 'admin.PageRelationships',
        '/categories/(\d*)/?', 'mypinnings.admin.categories.EditCategory',
        '/categories/(\d*)/delete/?', 'mypinnings.admin.categories.DeleteCategory',
        '/categories', 'mypinnings.admin.categories.ListCategories',
        '/categories/add/?', 'mypinnings.admin.categories.AddCategory',
        '/category-manage_cool/(\d*)/more/?', 'mypinnings.admin.categories.EditMoreCoolProductsForCategory',
        '/category-manage_cool/(\d*)', 'mypinnings.admin.categories.EditCoolProductsForCategory',
        '/category-cool-items/(\d*)/?', 'mypinnings.admin.categories.ListCoolProductsForCategory',
        '/api/categories/(\d*)/pins/?', 'mypinnings.admin.categories.ApiCategoryListPins',
        '/api/pin/(\d*)/?', 'mypinnings.admin.categories.ApiCategoryPins',
        '/api/categories/(\d*)/cool_pins/(\d*)/?', 'mypinnings.admin.categories.ApiCategoryCoolPins',
        '/selection/pending_items', 'mypinnings.admin.category_selection.PendingItems',
        '/selection/add_to_categories', 'mypinnings.admin.category_selection.AddPinToCategories',
        '/selection','mypinnings.admin.category_selection.CategorySelection',
        '/remove_from_category/(\d+)', 'mypinnings.admin.category_selection.RemoveFromCategory',
        '/remove_from_category', 'mypinnings.admin.category_selection.RemoveFromCategory',
        '/remove_from_category/set_category/(\d+)', 'mypinnings.admin.category_selection.SetCategoryToRemoveFrom',
        '/remove_from_category/items', 'mypinnings.admin.category_selection.ItemsToRemoveFromCategory',
        '/pins/search', 'mypinnings.admin.pins.Search',
        '/pins/search/pagination', 'mypinnings.admin.pins.SearchPagination',
        '/pins/search/set_search_criteria', 'mypinnings.admin.pins.SearchCriteria',
        '/pins/multiple_delete', 'mypinnings.admin.pins.MultipleDelete',
        '/pin/(\d+)', 'mypinnings.admin.pins.Pin',
        )


LOGIN_SOURCES = (('MP', 'MyPinnings'),
                 ('FB', 'Facebook'),
                 ('TW', 'Twitter'),
                 ('GG', 'Google+'),
                 )


def lmsg(msg):
    return template.admin.msg(msg)


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
    {where}
    group by users.id
    order by {sort} {dir}
    offset {offset} limit {limit}'''


class PageSearch:
    _form = form.Form(
        form.Textbox('query'),
        form.Button('search')
    )

    def GET(self, allusers=None):
        login()
        params = web.input(query='')
        query = params.query
        if allusers:
            return template.admin.search('')
        elif query:
            return template.admin.search(query)
        else:
            return template.admin.searchform(self._form())


class PageSearchResults(dataloaders.FixCreationDateMixin):
    page_size = 50

    def GET(self, allusers=None):
        login()

        params = web.input(page=1, sort='users.name', dir='asc', query='')
        page = int(params.page) - 1
        sort = params.sort
        direction = params.dir
        search_query = params.query

        if search_query:
            where = """where
            users.email ilike '%%{query}%%' or
            users.name ilike '%%{query}%%' or
            users.about ilike '%%{query}%%'""".format(query=search_query)
        else:
            where = ''
        query = USERS_QUERY.format(where=where,
                                  sort=sort,
                                  dir=direction,
                                  offset=page * self.page_size,
                                  limit=self.page_size)
            
        db = database.get_db()
        results = db.query(query)
        results = self.fix_creation_date(results)
        return web.template.frender('t/admin/search_results.html')(results)


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
        return template.admin.user(user[0], datetime)


class PageCloseUser:
    def GET(self, user_id):
        login()
        user_id = int(user_id)
        db = database.get_db()
        db.delete(table='photos', where='album_id in (select id from albums where user_id=$id)', vars={'id': user_id})
        db.delete(table='albums', where='user_id=$id', vars={'id': user_id})
        db.delete(table='boards', where='user_id=$id', vars={'id': user_id})
        db.delete(table='comments', where='user_id=$id', vars={'id': user_id})
        db.delete(table='messages', where='sender=$id', vars={'id': user_id})
        db.delete(table='convos', where='id1=$id or id2=$id', vars={'id': user_id})
        db.delete(table='follows', where='follower=$id or follow=$id', vars={'id': user_id})
        db.delete(table='friends', where='id1=$id or id2=$id', vars={'id': user_id})
        db.delete(table='likes', where='user_id=$id', vars={'id': user_id})
        db.delete(table='notifs', where='user_id=$id', vars={'id': user_id})
        db.delete(table='password_change_tokens', where='user_id=$id', vars={'id': user_id})
        db.delete(table='ratings', where='user_id=$id', vars={'id': user_id})
        db.delete(table='user_prefered_categories', where='user_id=$id', vars={'id': user_id})
        pin_utils.delete_all_pins_for_user(db, user_id)
        db.query('delete from users where id = $id', vars={'id': user_id})
        raise web.seeother('/')


class PageEditUser:
    def make_form(self, user=None):
        user = user or dict()
        my_countries = [('', '')] + list((c, c) for c in settings.COUNTRIES)
        return form.Form(
            form.Textbox('name', form.notnull, description="Full Name", value=user.get('name'), **{'class': 'form-control'}),
            form.Textbox('username', form.notnull, description="Username", value=user.get('username'), **{'class': 'form-control'}),
            form_controls.EMail('email', form.notnull, description="e-mail", value=user.get('email'), **{'class': 'form-control'}),
            form.Textarea('about', description="About the user", value=user.get('about'), **{'class': 'form-control'}),
            form.Dropdown('country', args=my_countries, description="Country", value=user.get('country'), **{'class': 'form-control'}),
            form.Textbox('city', description="City", value=user.get('city'), **{'class': 'form-control'}),
            form.Textbox('hometown', description="Home Town", value=user.get('hometown'), **{'class': 'form-control'}),
            form.Textbox('zip', description="ZIP Code", value=user.get('zip'), **{'class': 'form-control'}),
            form_controls.URL('website', description="Website URL", value=user.get('website'), **{'class': 'form-control'}),
            form.Textbox('facebook', description="Facebook user", value=user.get('facebook'), **{'class': 'form-control'}),
            form.Textbox('linkedin', description="LinkedIn user", value=user.get('linkedin'), **{'class': 'form-control'}),
            form.Textbox('twitter', description="Twitter user", value=user.get('twitter'), **{'class': 'form-control'}),
            form.Textbox('gplus', description="Google+ user", value=user.get('gplus'), **{'class': 'form-control'}),
            form.Checkbox('private', description="Is private?", value='on', checked=user.get('private')),
            form.Dropdown('login_source', args=LOGIN_SOURCES, description="Login source", value=user.get('login_source'), **{'class': 'form-control'}),
            form_controls.Date('birthday', description="Birthday", value=user.get('birthday'), **{'class': 'form-control'}),
            form.Dropdown('locale', args=settings.LANGUAGES, description="Locale", value=user.get('locale'), **{'class': 'form-control'}),
            form_controls.Number('views', description="# of views", value=user.get('views'), **{'class': 'form-control'}),
            form.Checkbox('show_views', description="Show views?", value='on', checked=user.get('show_views')),
            form.Checkbox('is_pin_loader', description="Is a Pin data loader?", value='on', checked=user.get('is_pin_loader')),
            form_controls.Number('activation', description="Activation", value=user.get('activation'), **{'class': 'form-control'}),
            form.Textbox('tsv', description="TSV", value=user.get('tsv'), **{'class': 'form-control'}),
            form.Checkbox('bg', description="BG", value='on', checked=user.get('bg')),
            form.Textbox('bgx', description="BG x", value=user.get('bgx')),
            form.Textbox('bgy', description="BG y", value=user.get('bgy')),
            form.Button('update'))()

    def GET(self, user_id):
        login()
        user_id = int(user_id)
        db = database.get_db()
        results = db.select('users', where='id = $id', vars={'id': user_id})
        for row in results:
            user = row
            break
        else:
            return 'That user does not exist.'
        return template.admin.edituser(self.make_form(user), user)

    def POST(self, user_id):
        login()
        user_id = int(user_id)
        form = self.make_form()
        if not form.validates():
            return 'invalid form input'

        d = dict(form.d)
        del d['update']
        d['zip'] = d.get('zip', None) or None
        d['birthday'] = d.get('birthday', None) or None
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
        form.Checkbox('is_pin_loader', value='on'),
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

        user_id = create_user(form.d.email, form.d.password, name=form.d.name, username=form.d.username,
                              is_pin_loader=form['is_pin_loader'].checked)
        if not user_id:
            return 'couldn\'t create user'

        raise web.seeother('/user/%d' % user_id)


class ChangePassword(object):
    form = web.form.Form(web.form.Password('pwd1', web.form.notnull, description="New password"),
                         web.form.Password('pwd2', web.form.notnull, description="Repeat password"),
                         web.form.Button('Change password'),
                         validators = [web.form.Validator('Password do not match', lambda i: i.pwd1 == i.pwd2)])
    
    def GET(self, user_id):
        return template.admin.form(self.form(), "Change password")
    
    def POST(self, user_id):
        form = self.form()
        if form.validates():
            auth.chage_user_password(user_id, form.d.pwd1)
            web.seeother('/user/{}'.format(user_id), absolute=False)
        else:
            return template.admin.form(self.form(), "Change password", "Password not changed, verify.")


class ChangeUserPicture(object):
    form = web.form.Form(web.form.File('newpic', web.form.notnull, description="New picture", **{'class': 'form-control'}),
                         web.form.Button('submit', description="Change image", **{'class': 'btn btn-default btn-xs'}))
    
    def GET(self, user_id):
        return template.admin.form(self.form(), 'Change user picture')
    
    def POST(self, user_id):
        try:
            input = web.input(newpic={})
            self.file = input.newpic
            self.user_id = user_id
            self.update_profile_picture()
            return web.seeother('/user/{}'.format(user_id), absolute=False)
        except Exception as e:
            logger.error('Cannot upload user picture', exc_info=True)
            return template.admin.upload_form(self.form(), 'Change user picture', str(e))
        
    def update_profile_picture(self):
        '''
        Grabs the profile image from google into this user
        '''
        new_filename = 'static/tmp/{}'.format(self.file.filename)
        with open(new_filename, 'w') as f:
            f.write(self.file.file.read())
        db = database.get_db()
        results = db.where(table='users', id=self.user_id)
        for row in results:
            self.user = row
        if not self.user.pic:
            album_id = db.insert(tablename='albums', name=_('Profile Pictures'), user_id=self.user_id)
            photo_id = db.insert(tablename='photos', album_id=album_id)
        else:
            photo_id = self.user.pic
        picture_filename = 'static/pics/{0}.png'.format(photo_id)
        filename = new_filename
        if filename.endswith('.png'):
            os.renames(old=filename, new=picture_filename)
        else:
            img = Image.open(filename)
            img.save(picture_filename)
        img = Image.open(picture_filename)
        width, height = img.size
        ratio = 80.8 / float(width)
        width = 80
        height *= ratio
        img.thumbnail((width, height), Image.ANTIALIAS)
        picture_thumb_filename = 'static/pics/userthumb{0}.png'.format(photo_id)
        if not self.user.pic:
            db.update(tables='users', where='id=$id', vars={'id': self.user_id}, pic=photo_id)
        img.save(picture_thumb_filename)


app = web.application(urls, locals())
