import random
import urllib
import json
import logging
import os
from gettext import gettext as _

import web
from PIL import Image

from mypinnings.conf import settings
from mypinnings import session
from mypinnings import template
from mypinnings import auth
from mypinnings import database


logger = logging.getLogger('mypinnings.google')

urls = ('/register/?', 'Register',
        '/register_return/?', 'RegisterReturn',
        '/username/?', 'SelectAUsernameAndPassword',
     )


class Register(object):
    def GET(self):
        sess = session.get_session()
        oAuth_url = 'https://accounts.google.com/o/oauth2/auth?'
        redirect_uri = web.ctx.home + '/register_return'
        sess['state'] = str(random.randrange(999999))
        parameters = {'response_type': 'code',
                      'client_id': settings.GOOGLE['client_id'],
                      'redirect_uri': redirect_uri,
                      'scope': 'profile email',
                      'state': sess['state'],
                      }
        url_redirect = oAuth_url + urllib.urlencode(parameters)
        raise web.seeother(url=url_redirect, absolute=True)

class RegisterReturn(object):
    def GET(self):
        self.sess = session.get_session()
        self.grab_query_string_parameters()
        errors = self.chech_for_errors()
        if errors:
            return errors
        if not self.exchange_authorization_code():
            return template.lmsg(_('Invalid google login'))
        if not self.obtain_user_profile():
            return template.lmsg(_('Invalid google login'))
        if not self.get_user_from_db():
            self.sess['profile'] = self.profile
            web.seeother(url='/username', absolute=False)
        else:
            # user already registered, perform a login instead of registration
            web.seeother(url='/login/')

    def grab_query_string_parameters(self):
        self.state = web.input(state=None)['state']
        self.error = web.input(error=None)['error']
        self.code = web.input(code=None)['code']

    def chech_for_errors(self):
        if not self.state or self.state != self.sess['state']:
            return template.lmsg(_('Detected a possible request forge'))
        if self.error:
            return template.lmsg(self.error)
        if not self.code:
            return template.lmsg(_('Invalid google login'))
        return False

    def exchange_authorization_code(self):
        try:
            base_url = 'https://accounts.google.com/o/oauth2/token'
            redirect_url = web.ctx.home + '/register_return'
            parameters = {'client_id': settings.GOOGLE['client_id'],
                          'client_secret': settings.GOOGLE['client_secret'],
                          'redirect_uri': redirect_url,
                          'code': self.code,
                          'grant_type': 'authorization_code',
                          }
            url_data = urllib.urlencode(parameters)
            url_exchange = base_url
            exchange_data = urllib.urlopen(url=url_exchange, data=url_data).read()
            token_data = json.loads(exchange_data)
            self.access_token = token_data['access_token']
            self.access_token_expires = token_data['expires_in']
            self.token_type = token_data['token_type']
            return True
        except:
            logger.error('Cannot exchange code for access token. Code: %s', self.code, exc_info=True)
            return False

    def obtain_user_profile(self):
        try:
            profile_url = 'https://www.googleapis.com/plus/v1/people/me?'
            parameters = {'access_token': self.access_token}
            url_profile = profile_url + urllib.urlencode(parameters)
            self.profile = json.load(urllib.urlopen(url=url_profile))
            # TODO delete this
            from pprint import pprint
            pprint(self.profile)
            return True
        except:
            logger.error('Cannot cannot obtain user profile. Access token: %s', self.access_token, exc_info=True)
            return False

    def get_user_from_db(self):
        '''
        Obtains the user_id from the database and return if exists.
        Else returns false.
        '''
        db = database.get_db()
        if 'nickname' in self.profile:
            query_result = db.select(tables='users', where="gplus=$username and login_source=$login_source",
                                       vars={'username': self.profile['nickname'],
                                             'login_source': auth.LOGIN_SOURCE_GOOGLE})
        elif 'emails' in self.profile:
            email = self.profile['emails'][0]['value']
            query_result = db.select(tables='users', where="email=$email and login_source=$login_source",
                                       vars={'email': email,
                                             'login_source': auth.LOGIN_SOURCE_GOOGLE})
        else:
            return False
        for row in query_result:
            self.user_id = row['id']
            self.username = row['username']
            return self.user_id
        return False


class SelectAUsernameAndPassword(auth.UniqueUsernameMixin):
    '''
    Ask for the user to select a username
    '''
    username_form = web.form.Form(web.form.Textbox('username', web.form.notnull, autocomplete='off',
                                                 id='username', placeholder=_('Select a username for your profile.'),
                                                 ),
                                web.form.Textbox('email', autocomplete='off', id='email', placeholder='Where we\'ll never spam you.'),
                                web.form.Password('password', id='password', autocomplete='off',
                                                  placeholder='Something you\'ll remember but others won\'t guess.'),
                                web.form.Button(_('Next')))

    def GET(self):
        sess = session.get_session()
        if 'nickname' in sess.profile and self.username_already_exists(sess.profile['nickname']):
            username = self.suggest_a_username(sess.profile['nickname'])
        elif 'nickname' in sess.profile:
            username = sess.profile['nickname']
        else:
            username = ''
        form = self.username_form()
        form['username'].set_value(username)
        if 'emails' in sess.profile and len(sess.profile['emails']) > 0:
            email_data = sess.profile['emails'][0]
            if 'value' in email_data:
                form['email'].set_value(email_data['value'])
        return template.ltpl('register/username', form)

    def POST(self):
        self.form = self.username_form()
        if self.form.validates():
            if self.username_already_exists(self.form['username'].value):
                return template.ltpl('register/username', self.form, _('Username already exists'))
            if self.email_already_exists(self.form['email'].value):
                return template.ltpl('register/username', self.form, _('Email already exists'))
            self._insert_user_to_db()
            auth.login_user(session.get_session(), self.user_id)
            web.seeother(url='/register/after-signup', absolute=True)
        else:
            return template.ltpl('register/username', self.form, _('Please provide all information'))

    def _insert_user_to_db(self):
        sess = session.get_session()
        # basic profile data
        values = {'username': self.form['username'].value,
                  'facebook': sess.profile['nickname'] if 'nickname' in sess.profile else '',
                  'login_source': auth.LOGIN_SOURCE_GOOGLE,
                  }
        # extended profile data, may not be always available
        try:
            if 'displayName' in sess.profile:
                values['name'] = sess.profile['displayName']
            elif 'name' in sess.profile:
                name_data = sess.profile['name']
                values['name'] = '{} {}'.format(name_data['givenName'], name_data['familyName'])
        except:
            logger.info('could not get name', exc_info=True)
        try:
            if 'placesLived' in sess.profile:
                # get the primary place lived
                for place_lived in sess.profile['placesLived']:
                    if place_lived['primary']:
                        values['hometown'] = place_lived['value']
                        values['city'] = place_lived['value']
                        break
        except:
            logger.info('could not get hometown', exc_info=True)
        try:
            if 'urls' in sess.profile:
                last_url_data = sess.profile['urls'][-1]
                values['website'] = last_url_data['value']
        except:
            logger.info('could not get website', exc_info=True)
        try:
            if 'birthday' in sess.profile:
                values['birthday'] = sess.profile['birthday']
        except:
            logger.info('could not get birthday', exc_info=True)
        # TODO delete
        from pprint import pprint
        pprint(values)
        self.user_id = auth.create_user(self.form['email'].value, self.form['password'].value, **values)
        self.grab_and_insert_profile_picture()
        return self.user_id

    def grab_and_insert_profile_picture(self):
        sess = session.get_session()
        if 'image' in sess.profile and 'url' in sess.profile['image']:
            db = database.get_db()
            album_id = db.insert(tablename='albums', name=_('Profile Pictures'), user_id=self.user_id)
            photo_id = db.insert(tablename='photos', album_id=album_id)
            picture_url = sess.profile['image']['url']
            picture_filename = 'static/pics/{0}.png'.format(photo_id)
            try:
                filename, headers = urllib.urlretrieve(url=picture_url)
                if filename.endswith('.png'):
                    os.renames(old=filename, new=picture_filename)
                else:
                    img = Image.open(filename)
                    img.save(picture_filename)
                    os.unlink(filename)
                img = Image.open(picture_filename)
                width, height = img.size
                ratio = 80 / width
                width = 80
                height *= ratio
                img.thumbnail((width, height), Image.ANTIALIAS)
                picture_thumb_filename = 'static/pics/userthumb{0}.png'.format(photo_id)
                img.save(picture_thumb_filename)
                db.update(tables='users', where='id=$id', vars={'id': self.user_id}, pic=photo_id)
            except:
                # no problem, we can live without the profile picture
                logger.info('Could not obtain google profile picture', exc_info=True)


app = web.application(urls, locals())
