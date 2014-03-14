import random
import json
import calendar
import datetime
import os.path

import web

from mypinnings import auth
from mypinnings import template
from mypinnings import session
from mypinnings import database
from mypinnings import cached_models
from mypinnings.conf import settings


urls = ('/after-signup/(\d*)', 'PageAfterSignup',
        '/after-signup', 'PageAfterSignup',
        '/api/users/me/category/(\d*)/?', 'ApiRegisterCategoryForUser',
        '/api/users/me/coolpins/(\d*)/?', 'ApiRegisterCoolPinForUser',
        '', 'PageRegister',
        )

class PageRegister:
    days = tuple((x, x) for x in range(0, 32))
    months = tuple(enumerate(calendar.month_name[1:]))
    current_year = datetime.date.today().year
    years = tuple((x, x) for x in range(current_year, current_year - 100, -1))
    if not hasattr(settings, 'LANGUAGES') or not settings.LANGUAGES:
        languages = (('en', 'English'),)
    else:
        languages = settings.LANGUAGES
    _form = web.form.Form(
        web.form.Textbox('username', id='username', autocomplete='off', placeholder='The name in your url.'),
        web.form.Textbox('name', autocomplete='off', placeholder='The name next to your picture.',
                         description="Complete name"),
        web.form.Textbox('email', autocomplete='off', id='email', placeholder='Where we\'ll never spam you.'),
        web.form.Password('password', id='password', autocomplete='off', placeholder='Something you\'ll remember but others won\'t guess.'),
        web.form.Textbox('name', autocomplete='off', placeholder='The name next to your picture.'),
        web.form.Dropdown('language', args=languages),
        web.form.Dropdown('day', args=days),
        web.form.Dropdown('month', args=months),
        web.form.Dropdown('year', args=years),
        web.form.Button('Let\'s get started!')
    )

    def msg(self, s):
        raise web.seeother('?msg=%s' % s, absolute=False)

    def GET(self):
        auth.force_login(session.get_session(), '/dashboard', True)
        form = self._form()
        message = web.input(msg=None).msg
        if message:
            return template.tpl('register/reg', form, message)
        return template.tpl('register/reg', form)

    def POST(self):
        form = self._form()
        form.validates()

        if not all([form.d.email, form.d.password, form.d.name, form.d.username, form.d.language,
                    form.d.day, form.d.month, form.d.year]):
            self.msg('Please enter an username, full name, email, pasword, and birthday and language.')

        if auth.email_exists(form.d.email):
            self.msg('Sorry, that email already exists.')

        if auth.username_exists(form.d.username):
            self.msg('Sorry, that username already exists.')

        activation = random.randint(1, 10000)
        hashed = hash(str(activation))

        birthday = '{}-{}-{}'.format(form.d.year, form.d.month, form.d.day)
        user_id = auth.create_user(form.d.email, form.d.password, name=form.d.name, username=form.d.username, activation=activation,
                                   locale=form.d.language, birthday=birthday)
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
        '''
        Select at least 3 categories from the list
        '''
        db = database.get_db()
        categories_results = db.where(table='categories', order='name')
        categories = []
        for category in categories_results:
            cool_items_resutls = db.select(tables=['pins', 'cool_pins'], what="pins.*",
                         where='pins.category=$category_id and pins.id=cool_pins.pin_id',
                         vars={'category_id': category.id})
            cool_items_list = list(cool_items_resutls)
            random_cool_items = []
            if len(cool_items_list) > 0:
                for _ in range(6):
                    if len(cool_items_list) == 0:
                        break
                    cool_item = random.choice(cool_items_list)
                    cool_items_list.remove(cool_item)
                    image_name = os.path.join('static', 'tmp', str(cool_item.id)) + '_cool.png'
                    if not os.path.exists(image_name):
                        continue
                    random_cool_items.append(cool_item)
                if len(random_cool_items) > 0:
                    category.cool_items = random_cool_items
                    categories.append(category)
        return template.atpl('register/aphase1', categories, phase=1)

    _form1 = web.form.Form(web.form.Hidden('ids'))

    def phase2(self):
        '''
        Select at least 5 pins from the list
        '''
        sess = session.get_session()
        db = database.get_db()
        cool_pins = db.select(tables=['pins', 'cool_pins', 'user_prefered_categories'], what='pins.*',
                              where='pins.id=cool_pins.pin_id and cool_pins.category_id=user_prefered_categories.category_id'
                              ' and user_prefered_categories.user_id=$user_id',
                              order='timestamp desc',
                              vars={'user_id': sess.user_id})
        cols = [[] for _ in range(3)]
        for i, cp in enumerate(cool_pins):
            cols[i % 3].append(cp)
            if not cp.name:
                cp.name = cp.description
        return template.atpl('register/aphase2', cols[0], cols[1], cols[2], phase=2)

    def phase3(self):
        '''
        Go to the profile
        '''
        sess = session.get_session()
        db = database.get_db()
        results = db.where(table='users', what='username', id=sess.user_id)
        username = results[0]['username']
        raise web.seeother(url="/{}".format(username), absolute=True)

    def GET(self, phase=None):
        '''
        Manages 3 phases of registration:

        1. Select categories
        2. select pins
        3. go to the profile
        '''
        auth.force_login(session.get_session())
        phase = int(phase or 1)
        try:
            return getattr(self, 'phase%d' % phase)()
        except AttributeError as e:
            raise web.notfound()


class ApiRegisterCategoryForUser:
    '''
    Adds and deletes prefered categories for the user

    For user via ajax.
    '''
    def PUT(self, category_id):
        '''
        Put a category in the prefered categories for this user
        '''
        sess = session.get_session()
        auth.force_login(sess)
        db = database.get_db()
        db.insert(tablename='user_prefered_categories', user_id=sess.user_id, category_id=category_id)
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})

    def DELETE(self, category_id):
        '''
        Deletes a category from the prefered categories for this user
        '''
        sess = session.get_session()
        auth.force_login(sess)
        db = database.get_db()
        db.delete(table='user_prefered_categories', where='user_id=$user_id and category_id=$category_id',
                  vars={'user_id': sess.user_id, 'category_id': category_id})
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})


class ApiRegisterCoolPinForUser(object):
    '''
    Adds and deletes cool items for the user

    For user via ajax.
    '''
    def PUT(self, pin_id):
        '''
        Put a cool item for this user
        '''
        sess = session.get_session()
        auth.force_login(sess)
        db = database.get_db()
        db.insert(tablename='user_prefered_pins', user_id=sess.user_id, pin_id=pin_id)
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})

    def DELETE(self, pin_id):
        '''
        Deletes a cool item from this user
        '''
        sess = session.get_session()
        auth.force_login(sess)
        db = database.get_db()
        db.delete(table='user_prefered_pins', where='user_id=$user_id and pin_id=$pin_id',
                  vars={'user_id': sess.user_id, 'pin_id': pin_id})
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})



def send_activation_email(email, hashed, user_id):
    web.sendmail('noreply@mypinnings.com', email, 'Please activate your MyPinnings account',
                 str(template.tpl('email', hashed, user_id)), headers={'Content-Type': 'text/html;charset=utf-8'})

app = web.application(urls, locals())
