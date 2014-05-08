import web
from web import form

from mypinnings import session
from mypinnings.template import tpl, ltpl, lmsg
from mypinnings.auth import force_login
from mypinnings.conf import settings
from mypinnings.database import connect_db, dbget
db = connect_db()

from mypinnings.api import api_request, convert_to_id, convert_to_logintoken

urls = ('', 'PageEditProfile',
        '/(email)', 'PageChangeEmail',
        '/(profile)', 'PageEditProfile',
        '/(password)', 'PageChangePw',
        '/(social-media)', 'PageChangeSM',
        '/(privacy)', 'PageChangePrivacy',
        '/(email-settings)', 'PageEditProfile',

        # '/changeemail', 'PageChangeEmail',
        # '/changepw', 'PageChangePw',
        # '/changesm', 'PageChangeSM',
        # '/changeprivacy', 'PageChangePrivacy',
        )


class PageEditProfile:
    _form = form.Form(
        form.Textbox('name'),
        form.Dropdown('country', []),
        form.Textbox('hometown'),
        form.Textbox('city'),
        form.Textbox('zip'),
        form.Textbox('username'),
        form.Textbox('website'),
        form.Textarea('about'),
    )

    def GET(self, name=None):
        sess = session.get_session()
        force_login(sess)
        user = dbget('users', sess.user_id)
        photos = db.select('photos', where='album_id = $id', vars={'id': sess.user_id})
        msg = web.input(msg=None)['msg']
        return ltpl('editprofile', user, settings.COUNTRIES, name, photos, msg)

    def POST(self, name=None):
        sess = session.get_session()
        user = dbget('users', sess.user_id)
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'you need to fill in everything'

        logintoken = convert_to_logintoken(sess.user_id)

        if logintoken:
            data = {
                "name":form.d.name,
                "about":form.d.about,
                "website":form.d.website,
                "country":form.d.country,
                "hometown":form.d.hometown,
                "city":form.d.city,
                "csid_from_client": 'None',
                "logintoken": logintoken
            }

            data = api_request("api/profile/userinfo/update", "POST", data)
            if data['status'] == 200:
                raise web.seeother('/profile')
            else:
                msg = data['error_code']
                raise web.seeother('/profile?msg=%s' % msg)

        get_input = web.input(_method='get')
        if 'user_profile' in get_input:
            raise web.seeother('/%s?editprofile=1' % user.username)

class PageChangeEmail(PageEditProfile):
    _form = form.Form(
        form.Textbox('email'),
        form.Textbox('username'))

    # @csrf_protected # Verify this is not CSRF, or fail
    def POST(self, name=None):
        sess = session.get_session()
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'you need to fill in everything'
        if db.select('users', where='email = $email', vars={'email' : form.d.email}):
            return 'Pick another email address'
        if db.select('users', where='username = $username', vars={'username':form.d.username}):
            return 'Pick another username'
        db.update('users', where='id = $id', vars={'id': sess.user_id}, email=form.d.email, username=form.d.username)
        raise web.seeother('/email')

class PageChangePw(PageEditProfile):
    _form = form.Form(
        form.Textbox('old'),
        form.Textbox('pwd1'),
        form.Textbox('pwd2')
    )

    def POST(self, name=None):
        sess = session.get_session()
        force_login(sess)

        form = self._form()
        if not form.validates():
            raise web.seeother('/password?msg=bad input')

        logintoken = convert_to_logintoken(sess.user_id)

        if logintoken:
            data = {
                "old_password": form.d.old,
                "new_password": form.d.pwd1,
                "new_password2": form.d.pwd2,
                "logintoken": logintoken
            }

            data = api_request("api/profile/pwd", "POST", data)
            if data['status'] == 200:
                raise web.seeother('/password')
            else:
                msg = data['error_code']
                raise web.seeother('/password?msg=%s' % msg)


class PageChangeSM(PageEditProfile):
    _form = form.Form(
        form.Textbox('facebook'),
        form.Textbox('linkedin'),
        form.Textbox('twitter'),
        form.Textbox('gplus'),
    )

    def POST(self, name=None):
        sess = session.get_session()
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'bad input'

        user = dbget('users', sess.user_id)
        if not user:
            return 'error getting user'

        db.update('users', where='id = $id', vars={'id': sess.user_id}, **form.d)
        raise web.seeother('/social-media')

class PageChangePrivacy(PageEditProfile):
    _form = form.Form(
        form.Checkbox('private'),
    )

    def POST(self, name=None):
        sess = session.get_session()
        force_login(sess)

        form = self._form()
        form.validates()

        # db.update('users', where='id = $id', vars={'id': sess.user_id}, **form.d)
        logintoken = convert_to_logintoken(sess.user_id)

        if logintoken:
            data = {
                "private": form.d.private,
                "logintoken": logintoken,
                "csid_from_client": "None"
            }

            data = api_request("api/profile/userinfo/set_privacy", "POST", data)
            if data['status'] == 200:
                raise web.seeother('/privacy')
            else:
                msg = data['error_code']
                raise web.seeother('/privacy?msg=%s' % msg)

app = web.application(urls, locals())

