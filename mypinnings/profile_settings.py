import web
from web import form

import mypinnings.session
from mypinnings.template import tpl, ltpl, lmsg
from mypinnings.auth import force_login
from mypinnings.conf import settings
from mypinnings.database import connect_db, dbget
db = connect_db()

urls = ('/', 'PageEditProfile',
        '/(email)', 'PageEditProfile',
        '/(profile)', 'PageEditProfile',
        '/(password)', 'PageEditProfile',
        '/(social-media)', 'PageEditProfile',
        '/(privacy)', 'PageEditProfile',
        '/(email-settings)', 'PageEditProfile',
        )

sess = mypinnings.session.sess

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
        force_login(sess)
        user = dbget('users', sess.user_id)
        photos = db.select('photos', where='album_id = $id', vars={'id': sess.user_id})
        msg = web.input(msg=None)['msg']
        return ltpl('editprofile', user, settings.COUNTRIES, name, photos, msg)

    def POST(self, name=None):
        user = dbget('users', sess.user_id)
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'you need to fill in everything'

        db.update('users', where='id = $id',
            name=form.d.name, about=form.d.about, username=form.d.username,
            zip=(form.d.zip or None), website=form.d.website, country=form.d.country,
            hometown=form.d.hometown, city=form.d.city,
            vars={'id': sess.user_id})
        get_input = web.input(_method='get')
        if 'user_profile' in get_input:
            raise web.seeother('/%s?editprofile=1' % user.username)
        raise web.seeother('/settings/profile')

app = web.application(urls, locals())