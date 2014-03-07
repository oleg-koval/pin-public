import random
import json

import web

from mypinnings import auth
from mypinnings import template
from mypinnings import session
from mypinnings import database
from mypinnings import cached_models

urls = ('/after-signup/(\d*)', 'PageAfterSignup',
        '/after-signup', 'PageAfterSignup',
        '/api/users/me/category/(\d*)/?', 'ApiRegisterCategoryForUser',
        '', 'PageRegister',
        )

class PageRegister:
    _form = web.form.Form(
        web.form.Textbox('email', autocomplete='off', id='email', placeholder='Where we\'ll never spam you.'),
        web.form.Textbox('username', id='username', autocomplete='off', placeholder='The name in your url.'),
        web.form.Password('password', id='password', autocomplete='off', placeholder='Something you\'ll remember but others won\'t guess.'),
        web.form.Textbox('name', autocomplete='off', placeholder='The name next to your picture.'),
        web.form.Button('Let\'s get started!')
    )

    def msg(self, s):
        raise web.seeother('/register?msg=%s' % s, absolute=False)

    def GET(self):
        auth.force_login(session.get_session(), '/dashboard', True)
        form = self._form()
        message = web.input(msg=None).msg
        if message:
            return template.ltpl('register/reg', form, message)
        return template.tpl('register/reg', form)

    def POST(self):
        form = self._form()
        form.validates()

        if not all([form.d.email, form.d.password, form.d.name, form.d.username]):
            self.msg('Please enter an email, pasword, and username.')

        if auth.email_exists(form.d.email):
            self.msg('Sorry, that email already exists.')

        if auth.username_exists(form.d.username):
            self.msg('Sorry, that username already exists.')

        activation = random.randint(1, 10000)
        hashed = hash(str(activation))

        user_id = auth.create_user(form.d.email, form.d.password, name=form.d.name, username=form.d.username, activation=activation)
        if not user_id:
            self.msg('Sorry, a database error occurred and we couldn\'t create your account.')

        send_activation_email(form.d.email, hashed, user_id)
        auth.login_user(session.get_session(), user_id)
        raise web.seeother('/after-signup')


class PageResendActivation:
    def GET(self):
        sess = session.get_session()
        auth.force_login(sess)

        user = database.dbget('users', sess.user_id)
        if not user:
            raise web.seeother('/')

        if user.activation == 0:
            raise web.seeother('/')

        hashed = hash(str(user.activation))
        send_activation_email(user.email, hashed, user.id)
        return template.lmsg('An email has been resent. <a href="/"><b>Back</b></a> |  <a href=""><b>Send another one</b></a>')


class PageAfterSignup:
    def phase1(self):
        return template.atpl('register/aphase1', cached_models.categories_with_thumbnails, phase=1)

    _form1 = web.form.Form(web.form.Hidden('ids'))

    def phase2(self):
        form = self._form1()
        form.validates()
        ids = map(str, map(int, form.d.ids.split(',')))
        db = database.get_db()
        users = db.query('''
            select
                users.*,
                count(distinct pins) as pin_count
            from users
                left join pins on pins.user_id = users.id
            where pins.category in (%s)
            group by users.id
            order by pin_count desc
            limit 10''' % ', '.join(ids))
        return template.atpl('register/aphase2', users, phase=2)

    def old_phase_post_2(self):
        try:
            form = self._form1()
            form.validates()
            ids = map(str, map(int, form.d.ids.split(',')))

            print ids
            if len(ids) > 10:
                ids = ids[:10]
            sess = session.get_session()
            db = database.get_db()
            follows = [{'follow': x, 'follower': sess.user_id} for x in ids]
            db.multiple_insert('follows', follows)
        except:
            pass
        raise web.seeother('/after-signup/3')

    def phase3(self):
        return template.atpl('register/aphase3', phase=3)

    def GET(self, phase=None):
        auth.force_login(session.get_session())
        phase = int(phase or 1)
        try:
            return getattr(self, 'phase%d' % phase)()
        except AttributeError as e:
            raise web.notfound()

    def POST(self, phase=None):
        auth.force_login(session.get_session())
        phase = int(phase or 1)

        try:
            return getattr(self, 'phase_post_%d' % phase)()
        except AttributeError:
            raise web.notfound()


class ApiRegisterCategoryForUser:
    '''
    '''
    def PUT(self, category_id):
        sess = session.get_session()
        db = database.get_db()
        db.insert(tablename='user_prefered_categories', user_id=sess.user_id, category_id=category_id)
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})

    def DELETE(self, category_id):
        sess = session.get_session()
        db = database.get_db()
        db.delete(table='user_prefered_categories', where='user_id=$user_id and category_id=$category_id',
                  vars={'user_id': sess.user_id, 'category_id': category_id})
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})



def send_activation_email(email, hashed, user_id):
    web.sendmail('noreply@mypinnings.com', email, 'Please activate your MyPinnings account',
                 str(template.tpl('email', hashed, user_id)), headers={'Content-Type': 'text/html;charset=utf-8'})

app = web.application(urls, locals())
