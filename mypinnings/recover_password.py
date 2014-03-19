import json
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
