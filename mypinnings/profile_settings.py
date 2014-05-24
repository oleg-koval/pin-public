import web
from web import form

from mypinnings import session
from mypinnings.template import tpl, ltpl, lmsg
from mypinnings.auth import force_login
from mypinnings.conf import settings
from mypinnings.database import connect_db, dbget
from mypinnings.pin_utils import dotdict
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


class PageEditProfile(object):
    """
    Responsible for profile editing.
    """
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

        logintoken = convert_to_logintoken(sess.user_id)
        profile_url = "/api/profile/userinfo/get"
        profile_owner_context = {
            "csid_from_client": "",
            "logintoken": logintoken
        }
        user = api_request(profile_url, data=profile_owner_context).get("data")
        user = dotdict(user)
        msg = web.input(msg=None)['msg']
        return ltpl('editprofile', user, settings.COUNTRIES, name, msg)

    def POST(self, name=None):
        """
        Responsible for handing profile editing calls
        """
        sess = session.get_session()
        force_login(sess)
        logintoken = convert_to_logintoken(sess.user_id)

        form = self._form()
        if not form.validates():
            return 'you need to fill in everything'

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
    """
    Edit username & email
    """
    _form = form.Form(
        form.Textbox('email'),
        form.Textbox('username'))

    def _is_available(self, uid, value, field="email"):
        """
        This function checks if given email/username is not yet occupied

        uid: user id is used to exclude current user from check
        """
        vars={'id': uid, 'value': value}
        query = db.select('users', vars=vars,
                          where='id<>$id and %s=$value' % (field))

        if len(query.list()) > 0:
            return False
        return True


    def POST(self, name=None):
        """
        Handler for changing email or username
        """
        sess = session.get_session()
        force_login(sess)
        logintoken = convert_to_logintoken(sess.user_id)

        form = self._form()
        if not form.validates():
            return form.note

        email_available = self._is_available(uid=sess.user_id,
                                             field="email",
                                             value=form.d.email)
        if not email_available:
            msg = "Please try another email, this one is already occupied"
            return web.seeother('?msg=%s' % msg)

        username_available = self._is_available(uid=sess.user_id,
                                             field="username",
                                             value=form.d.username)
        if not username_available:
            msg = "Please try another username, this one is already occupied"
            return web.seeother('?msg=%s' % msg)

        if logintoken:
            data = {
                "username":form.d.username,
                "email":form.d.email,
                "csid_from_client": 'None',
                "logintoken": logintoken
            }

            data = api_request("api/profile/userinfo/update", "POST", data)
            if data['status'] == 200:
                raise web.seeother('')
            else:
                msg = data['error_code']
                raise web.seeother('?msg=%s' % msg)


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
    """
    Class responsible for updating social media accounts
    """
    _form = form.Form(
        form.Textbox('facebook'),
        form.Textbox('linkedin'),
        form.Textbox('twitter'),
        form.Textbox('gplus'),
    )

    def POST(self, name=None):
        """
        Updates social media accounts.
        """
        sess = session.get_session()
        force_login(sess)
        logintoken = convert_to_logintoken(sess.user_id)

        form = self._form()
        if not form.validates():
            return 'bad input'

        if logintoken:
            data = {
                "logintoken": logintoken,
                "csid_from_client": "",
                "facebook": form.d.facebook,
                "linkedin": form.d.linkedin,
                "twitter": form.d.twitter,
                "gplus": form.d.gplus
                }
        data = api_request("api/profile/userinfo/update", data=data)
        if data['status'] == 200:
            raise web.seeother('/social-media')
        else:
            mgs = data['error_code']
            raise web.seeother('/profile?msg=%s' % msg)

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
