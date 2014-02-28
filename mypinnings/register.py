import random

import web

from mypinnings import auth
from mypinnings import template
from mypinnings import session
from mypinnings import database

urls = ('', 'PageRegister',
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
        raise web.seeother('/register?msg=%s' % s)

    def GET(self):
        auth.force_login(session.get_session(), '/dashboard', True)
        form = self._form()
        message = web.input(msg=None).msg
        if message:
            return template.ltpl('reg', form, message)
        return template.tpl('reg', form)

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



def send_activation_email(email, hashed, user_id):
    web.sendmail('noreply@mypinnings.com', email, 'Please activate your MyPinnings account',
                 str(template.tpl('email', hashed, user_id)), headers={'Content-Type': 'text/html;charset=utf-8'})

app = web.application(urls, locals())