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
from mypinnings.facebook import redirect_to_register
from mypinnings.register import valid_email


logger = logging.getLogger('mypinnings.google')

urls = ('/register/?', 'Register',
        '/register_return/?', 'RegisterReturn',
        '/username/?', 'SelectAUsernameAndPassword',
        '/login/?', 'Login',
        '/login_return/?', 'LoginReturn',
     )


class GoogleOauthStart(object):
    '''
    Starts the oauth dance with facebook
    '''
    def __init__(self, redirect_uri):
        '''
        Must provide the redirect_uri to return from google
        '''
        self.redirect_uri = redirect_uri

    def GET(self):
        '''
        Starts the authorization
        '''
        try:
            sess = session.get_session()
            oAuth_url = 'https://accounts.google.com/o/oauth2/auth?'
            sess['state'] = str(random.randrange(999999))
            sess['redirect_uri'] = self.redirect_uri
            parameters = {'response_type': 'code',
                          'client_id': settings.GOOGLE['client_id'],
                          'redirect_uri': self.redirect_uri,
                          'scope': 'profile email',
                          'state': sess['state'],
                          }
            url_redirect = oAuth_url + urllib.urlencode(parameters)
            return web.seeother(url=url_redirect, absolute=True)
        except Exception:
            logger.error('Cannot construct the URL to redirect to Facebook login', exc_info=True)
            return redirect_to_register(_('There is a misconfiguration in our server. We are not'
                                          ' able to login to Facebook now. Please try another method'))


class GoogleOauthReturnMixin(object):
    '''
    Mixin with utilities to manage the response from google oauth
    '''
    def grab_query_string_parameters(self):
        '''
        Get the parameter from query string returned by google
        '''
        self.state = web.input(state=None)['state']
        self.error = web.input(error=None)['error']
        self.code = web.input(code=None)['code']

    def chech_for_errors(self):
        '''
        Look for errors.

        Query string can contain an error parameter.
        The state can be different from what we sent in the oauth start
        Code parameter is mandatory.
        '''
        if not self.state or self.state != self.sess['state']:
            return redirect_to_register(_('Detected a possible request forge'))
        if self.error:
            return redirect_to_register(self.error)
        if not self.code:
            return redirect_to_register(_('Invalid google login'))
        return False

    def exchange_authorization_code(self):
        '''
        Exchange the code for an access token
        '''
        try:
            base_url = 'https://accounts.google.com/o/oauth2/token'
            parameters = {'client_id': settings.GOOGLE['client_id'],
                          'client_secret': settings.GOOGLE['client_secret'],
                          'redirect_uri': self.sess.redirect_uri,
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
        '''
        Get the user profile from Google
        '''
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
        Obtains the user_id from the database and return if exists, else returns false.

        Looks if the google nickname is in the DB. If the profile does not have a nickname,
        look if the email is in the DB.
        '''
        try:
            db = database.get_db()
            if 'nickname' in self.profile:
                query_result = db.select(tables='users', where="gplus=$username and login_source=$login_source",
                                           vars={'username': self.profile['nickname'],
                                                 'login_source': auth.LOGIN_SOURCE_GOOGLE})
            elif 'emails' in self.profile:
                email = self.profile['emails'][0]['value']
                query_result = db.select(tables='users', where="email=$email",
                                           vars={'email': email})
            else:
                return False
            for row in query_result:
                self.user_id = row['id']
                self.username = row['username']
                return self.user_id
            return False
        except:
            logger.error('Cannot obtain user from the DB. User id: %s', self.user_id, exc_info=True)
            return False


class Register(GoogleOauthStart):
    '''
    Starts the registration by performing the google oauth
    '''
    def __init__(self):
        '''
        Indicates the return url
        '''
        super(Register, self).__init__(web.ctx.home + '/register_return')


class RegisterReturn(GoogleOauthReturnMixin):
    '''
    Manages the return from google
    '''
    def GET(self):
        self.sess = session.get_session()
        self.grab_query_string_parameters()
        errors = self.chech_for_errors()
        if errors:
            return errors
        if not self.exchange_authorization_code():
            return redirect_to_register(_('Invalid google login'))
        if not self.obtain_user_profile():
            return redirect_to_register(_('Invalid google login'))
        if not self.get_user_from_db():
            self.sess['profile'] = self.profile
            web.seeother(url='/username', absolute=False)
        else:
            # user already registered, perform a login instead of registration
            web.seeother(url='/login/')


class SelectAUsernameAndPassword(auth.UniqueUsernameMixin):
    '''
    Ask for the user to select a username, email and password
    '''
    username_form = web.form.Form(web.form.Textbox('username', web.form.notnull, autocomplete='off',
                                                 id='username', placeholder=_('Select a username for your profile.'),
                                                 ),
                                web.form.Textbox('email', valid_email, web.form.notnull, autocomplete='off', id='email',
                                                 placeholder='Where we\'ll never spam you.'),
                                web.form.Password('password', web.form.notnull, id='password', autocomplete='off',
                                                  placeholder='Something you\'ll remember but others won\'t guess.'),
                                web.form.Button(_('Next')))

    def GET(self):
        '''
        Shows a form to introduce the data: username, email, password
        '''
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
        '''
        Creates the user in the DB if the data is valid
        '''
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
        '''
        Inserts the user data into the DB
        '''
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
        '''
        Grabs the profile image from google into this user
        '''
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
                ratio = 80.0 / float(width)
                width = 80
                height *= ratio
                img.thumbnail((width, height), Image.ANTIALIAS)
                picture_thumb_filename = 'static/pics/userthumb{0}.png'.format(photo_id)
                img.save(picture_thumb_filename)
                db.update(tables='users', where='id=$id', vars={'id': self.user_id}, pic=photo_id)
            except:
                # no problem, we can live without the profile picture
                logger.info('Could not obtain google profile picture', exc_info=True)


class Login(GoogleOauthStart):
    '''
    Starts the login process with google with oauth
    '''
    def __init__(self):
        '''
        Indicates the return URL
        '''
        super(Login, self).__init__(web.ctx.home + '/login_return')


class LoginReturn(GoogleOauthReturnMixin):
    '''
    Manages the return grom google login
    '''
    def GET(self):
        '''
        Logs the user in
        '''
        self.sess = session.get_session()
        self.grab_query_string_parameters()
        errors = self.chech_for_errors()
        if errors:
            return errors
        if not self.exchange_authorization_code():
            return redirect_to_register(_('Invalid google login'))
        if not self.obtain_user_profile():
            return redirect_to_register(_('Invalid google login'))
        if not self.get_user_from_db():
            # user not registered, go to registration
            web.seeother(url='/register/')
        else:
            auth.login_user(self.sess, self.user_id)
            web.seeother(url='/{}'.format(self.username), absolute=True)


app = web.application(urls, locals())
