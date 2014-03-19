import json
from gettext import gettext as _

import web

from mypinnings import session
from mypinnings import template
from mypinnings import database


class PasswordRecoveryStart(object):
    UsenameForm = web.form.Form(web.form.Textbox('username', web.form.notnull, description=_("Enter your username or email address"), autocomplete='off'),
                                web.form.Button('submit', description=_("Submit")))

    def GET(self):
        sess = session.get_session()
        if sess.get('user_id', False):
            return web.seeother(url='/', absolute=True)
        message = web.input(msg=None)['msg']
        form = self.UsenameForm()
        return template.ltpl('recover_password/start', form, message)

    def POST(self):
        form = self.UsenameForm()
        if form.validates:
            username_or_email = form.d.username
            db = database.get_db()
            results = db.where(table='users', username=username_or_email)
            for row in results:
                user = row
                break
            else:
                results = db.where(table='users', email=username_or_email)
                for row in results:
                    user = row
                    break
                else:
                    return web.seeother('?msg={}'.format(_('It looks like you entered invalid information. Please try again.')), absolute=False)
            self.generate_a_temporary_password_change_hash()
            self.send_email_with_hash_and_link_to_the_user()
            return ''  # TODO
        else:
            return web.seeother('?msg={}'.format(_('Enter your username or email address')), absolute=False)

import time
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
