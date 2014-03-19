import web

from mypinnings import session
from mypinnings import template


class PasswordRecoveryStart(object):
    UsenameForm = web.form.Form(web.form.Textbox('username', web.form.notnull, description="Enter your username or email address"),
                                web.form.Button('submit', description="Submit"))

    def GET(self):
        sess = session.get_session()
        if sess.get('user_id', False):
            return web.seeother(url='/', absolute=True)
        message = web.input(msg=None)['msg']
        form = self.UsenameForm()
        return template.ltpl('recover_password/start', form, message)