#!/usr/bin/python
import web
from web import form
import random
import string
import hashlib
##
from db import connect_db
import ser

PASSWORD = 'davidfanisawesome'

db = connect_db()


sess = ser.sess


def tpl(*params):
    global template_obj
    return template_obj(*params)


def template_closure(directory):
    global settings
    templates = web.template.render(directory,
        globals={'sess': sess, 'tpl': tpl})
    def render(name, *params):
        return getattr(templates, name)(*params)
    return render

template_obj = template_closure('t/admin')


def ltpl(*params):
    return tpl('layout', tpl(*params))


def lmsg(msg):
    return tpl('layout', '<div class="prose">%s</div>' % msg)



def login():
    global sess

    good = False
    if 'ok' in sess:
        good = True
    else:
        cookies = web.cookies()
        if cookies.get('adminpw') == PASSWORD:
            good = True

    if not good:
        raise web.seeother('/admin/login')


class PageIndex:
    def GET(self):
        login()
        return ltpl('index')


class PageLogin:
    _form = form.Form(
        form.Password('password'),
        form.Button('login')
    )

    def GET(self):
        return ltpl('form', self._form(), 'Login')

    def POST(self):
        form = self._form()
        if not form.validates():
            return 'houston we have a problem'

        if form.d.password != PASSWORD:
            return 'password incorrect'

        web.setcookie('adminpw', PASSWORD, 99999999)
        sess.ok = True
        raise web.seeother('/admin/')


class PageLogout:
    def GET(self):
        sess.kill()
        web.setcookie('adminpw', '', expires=-1)
        raise web.seeother('/admin')


class PageRelationships:
    def GET(self):
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

        return ltpl('relations', follows, friends)



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
            results = db.query(query)
            return ltpl('search', results)

        search_query = params.query
        if search_query is None:
            return ltpl('searchform', self._form(), params)

        query = make_query(USERS_QUERY % '''
            where
                users.email ilike $search or
                users.name ilike $search or
                users.about ilike $search''')

        results = db.query(query, vars={'search': '%%%s%%' % search_query})
        return ltpl('search', results)


class PageUser:
    def GET(self, user_id):
        user_id = int(user_id)
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

        return ltpl('user', user[0])


class PageCloseUser:
    def GET(self, user_id):
        login()
        user_id = int(user_id)
        db.query('delete from pins where user_id = $id', vars={'id': user_id})
        db.query('delete from users where id = $id', vars={'id': user_id})
        raise web.seeother('/admin/')


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
        user = db.select('users', where='id = $id', vars={'id': user_id})
        if not user:
            return 'That user does not exist.'

        return ltpl('edituser', self.make_form(user[0]))

    def POST(self, user_id):
        login()
        user_id = int(user_id)
        form = self.make_form()
        if not form.validates():
            return 'invalid form input'

        d = dict(form.d)
        del d['update']
        db.update('users', where='id = $id', vars={'id': user_id}, **d)
        raise web.seeother('/admin/edituser/%d' % user_id)


def email_exists(email):
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
    pw_hash = hash(pw_hash+pw_salt)

    return db.insert('users', email=email, pw_hash=pw_hash, pw_salt=pw_salt, **params)


def generate_salt(length=10):
    random.seed()
    pool = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(pool) for i in range(length))


def username_exists(username):
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
        return ltpl('reg', form)

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

        raise web.seeother('/admin/user/%d' % user_id)


if __name__ == '__main__':
    app.run()
