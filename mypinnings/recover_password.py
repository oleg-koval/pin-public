import json
import datetime
from gettext import gettext as _

import web

from mypinnings import session
from mypinnings import template
from mypinnings import database
from mypinnings import auth


class PasswordRecoveryStart(object):
    UsernameForm = web.form.Form(web.form.Textbox('username', web.form.notnull, description=_("Enter your username or email address"), autocomplete='off'),
                                web.form.Button('submit', description=_("Submit")))

    def GET(self):
        sess = session.get_session()
        if sess.get('user_id', False):
            return web.seeother(url='/', absolute=True)
        message = web.input(msg=None)['msg']
        form = self.UsernameForm()
        return template.ltpl('recover_password/start', form, message)

    def POST(self):
        form = self.UsernameForm()
        if form.validates():
            username_or_email = form.d.username
            self.db = database.get_db()
            results_username = self.db.where(table='users', username=username_or_email)
            for row in results_username:
                self.user = row
                break
            else:
                results_email = self.db.where(table='users', email=username_or_email)
                for row in results_email:
                    self.user = row
                    break
                else:
                    return web.seeother('?msg={}'.format(_('It looks like you entered invalid information. Please try again.')), absolute=False)
            self.generate_a_temporary_password_change_token()
            self.send_email_to_user()
            return web.seeother('/recover_password_sent/')
        else:
            return web.seeother('?msg={}'.format(_('Enter your username or email address')), absolute=False)

    def generate_a_temporary_password_change_token(self):
        self.token = auth.generate_salt(20)
        self.token_id = self.db.insert(tablename='password_change_tokens', seqname='password_change_tokens_id_seq', user_id=self.user.id, token=self.token)

    def send_email_to_user(self):
        html_message = str(web.template.frender('t/recover_password/email.html')(self.user, self.token_id, self.token))
        web.sendmail('noreply@mypinnings.com', self.user.email, 'Reset your MyPinnings password',
                 html_message, headers={'Content-Type': 'text/html;charset=utf-8'})


class EmailSentPage(object):
    def GET(self):
        return template.ltpl('recover_password/sent')


class UsernameOrEmailValidator(object):
    def GET(self):
        result = {'status': 'nothing'}
        username_or_email = web.input(username=None)['username']
        if username_or_email:
            db = database.get_db()
            results = db.where(table='users', username=username_or_email)
            for row in results:
                result['status'] = 'ok'
                break
            else:
                results = db.where(table='users', email=username_or_email)
                for row in results:
                    result['status'] = 'ok'
                    break
                else:
                    result['status'] = 'notfound'
        result = json.dumps(result)
        web.header('Content-Type', 'application/json')
        return result


class PasswordReset(object):
    PwdResetForm = web.form.Form(web.form.Password('pwd1', web.form.notnull, description=_('New password')),
                                 web.form.Password('pwd2', web.form.notnull, description=_('Verify your password')),
                                 web.form.Button('send', description=_('Send')),
                                 validators=[web.form.Validator("Passwords don't match", lambda i: i.pwd1 == i.pwd2),
                                             web.form.Validator('Passwords must have at least 6 characters', lambda i: len(i.pwd1) >= 6)])

    def GET(self, user_id, token_id, token):
        user_id = int(user_id)
        token_id = int(token_id)
        db = database.get_db()
        results = db.where(table='password_change_tokens', id=token_id)
        for row in results:
            if (user_id == row.user_id and token == row.token
                    and not row.used
                    and datetime.datetime.now() < (row.created_on + datetime.timedelta(hours=row.valid_hours))):
                form = self.PwdResetForm()
                sess = session.get_session()
                sess['pwdrecov_user_id'] = user_id
                sess['pwdrecov_token_id'] = token_id
                sess['pwdrecov_token'] = token
                return template.ltpl('recover_password/change_pwd_form', form)
        message = _('Sorry! We cannot verify that this user requested a password reset. Please try to reset your passord again.')
        web.seeother(url='/recover_password?msg={}'.format(message), absolute=True)

    def POST(self, user_id, token_id, token):
        user_id = int(user_id)
        token_id = int(token_id)
        form = self.PwdResetForm()
        if form.validates():
            sess = session.get_session()
            if sess['pwdrecov_token_id'] != token_id or sess['pwdrecov_user_id'] != user_id or sess['pwdrecov_token'] != token:
                message = _('Sorry! We cannot verify that this user requested a password reset. Please try to reset your passord again.')
                return web.seeother(url='/recover_password?msg={}'.format(message), absolute=True)
            password = form.d.pwd1
            auth.chage_user_password(user_id, password)
            db = database.get_db()
            db.update(tables='password_change_tokens', where='id=$id', vars={'id': token_id}, used=True, used_on=datetime.datetime.now())
            auth.login_user(sess, user_id)
            return web.seeother('/recover_password_complete/')
        else:
            return template.ltpl('recover_password/change_pwd_form', form)


class RecoverPasswordComplete(object):
    def GET(self):
        db = database.get_db()
        sess = session.get_session()
        results = db.where('users', what='username', id=sess.user_id)
        for row in results:
            username = row.username
        return template.ltpl('recover_password/complete', username)