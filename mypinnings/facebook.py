'''
Handles registration and login using the facebook service
'''
import random
import urllib
import urlparse
import json
import logging
import os
import os.path
from gettext import gettext as _

import web
from PIL import Image

from mypinnings.conf import settings
from mypinnings import template
from mypinnings import session
from mypinnings import database
from mypinnings import auth


urls = ('/register/?', 'Register',
        '/register_return/?', 'RegisterReturn',
        '/username/?', 'Username',
        '/login/?', 'Login',
        '/login_return/?', 'LoginReturn',
        )

logger = logging.getLogger('mypinnings.facebook')


def redirect_to_register(msg='Error login with Facebook.'):
    url = '/register?msg={}'.format(msg)
    return web.seeother(url=url, absolute=True)


class FacebookOauthStart(object):
    '''
    Starts the oauth dance with facebook
    '''
    def __init__(self, return_url):
        self.return_url = return_url

    def GET(self):
        '''
        Redirects to facebook login page
        '''
        try:
            base_url = 'https://www.facebook.com/dialog/oauth?'
            state = str(random.randrange(99999999))
            sess = session.get_session()
            sess['state'] = state
            parameters = {'state': state,
                          'client_id': settings.FACEBOOK['application_id'],
                          'redirect_uri': self.return_url,
                          'scope': 'email,user_birthday,publish_actions,user_hometown',
                          }
            url_redirect = base_url + urllib.urlencode(parameters)
            return web.seeother(url=url_redirect, absolute=True)
        except Exception:
            logger.error('Cannot construct the URL to redirect to Facebook login', exc_info=True)
            return redirect_to_register(_('There is a misconfiguration in our server. We are not able to login to Facebook now. Please try another method'))


class FacebookOauthReturnMixin(object):
    '''
    Manages the second part of facebook oauth dance
    '''
    def __init__(self, return_url):
        self.return_url = return_url

    def _check_state_parameter(self):
        '''
        Check that the state we send to facebook is the same that facebook
        returns back.
        '''
        try:
            sess = session.get_session()
            state = sess['state']
            returned_state = web.input(state=None)['state']
            return state == returned_state
        except:
            logger.error('Session has no state value to check. Possible request forgery')
            return False

    def _exchange_code_for_access_token(self):
        '''
        Validates the code returned from facebook redirect. If correctly validated,
        returns True, otherwise False
        '''
        try:
            base_url = 'https://graph.facebook.com/oauth/access_token?'
            redirect_url = self.return_url
            parameters = {'client_id': settings.FACEBOOK['application_id'],
                          'client_secret': settings.FACEBOOK['application_secret'],
                          'redirect_uri': redirect_url,
                          'code': self.code,
                          }
            url_exchange = base_url + urllib.urlencode(parameters)
            exchange_data = urllib.urlopen(url=url_exchange).read()
            token_data = urlparse.parse_qs(qs=exchange_data)
            self.access_token = token_data['access_token'][-1]
            self.access_token_expires = token_data['expires'][-1]
            return True
        except:
            logger.error('Cannot exchange code for access token. Code: %s', self.code, exc_info=True)
            return False

    def _obtain_user_profile(self):
        '''
        Get the user profile from facebook, Returns True if the user is
        found in facebook, False otherwise
        '''
        try:
            base_url = 'https://graph.facebook.com/me?'
            parameters = {'access_token': self.access_token}
            url_profile = base_url + urllib.urlencode(parameters)
            self.profile = json.load(urllib.urlopen(url=url_profile))
            return True
        except:
            logger.error('Cannot obtain user profile. Access token: %s', self.access_token, exc_info=True)
            return False

    def _get_user_from_db(self):
        '''
        Obtains the user_id from the database and return if exists.
        Else returns false.
        '''
        try:
            db = database.get_db()
            query_result = db.select(tables='users', where="facebook=$username and login_source=$login_source",
                                       vars={'username': self.profile['username'],
                                             'login_source': auth.LOGIN_SOURCE_FACEBOOK})
            for row in query_result:
                self.user_id = row['id']
                self.username = row['username']
                return self.user_id
            return False
        except:
            logger.error('Cannot obtain user from the DB. User id: %s', self.user_id, exc_info=True)
            return False


class Register(FacebookOauthStart):
    '''
    Start the facebook login
    '''
    def __init__(self):
        super(Register, self).__init__(web.ctx.home + '/register_return')


class RegisterReturn(FacebookOauthReturnMixin, auth.UniqueUsernameMixin):
    '''
    Manages the return from the facebook login
    '''
    def __init__(self):
        super(RegisterReturn, self).__init__(web.ctx.home + '/register_return')

    def GET(self):
        '''
        Manages the return from the facebook login. On success returns to the root
        of the server url. Else prints a message
        '''
        sess = session.get_session()
        error = web.input(error=None)['error']
        if error:
            error = web.input(error_description='')['error_description']
            full_error = _('There was a problem with login with Facebook. You can try again or user another login method: {}').format(error)
            return redirect_to_register(full_error)
        else:
            self.code = web.input(code=None)['code']
            if self.code:
                if not self._check_state_parameter():
                    return redirect_to_register(_('Detected a possible request forge'))
                if not self._exchange_code_for_access_token():
                    return redirect_to_register(_('Invalid facebook login'))
                if not self._obtain_user_profile():
                    return redirect_to_register(_('Invalid facebook login'))
                user_id = self._get_user_from_db()
                if not user_id:
                    sess['fb_profile'] = self.profile
                    web.seeother(url='/username', absolute=False)
                else:
                    # user already registered, perform a login instead of registration
                    web.seeother(url='/login/')
            else:
                error = _('Failure in the OAuth protocol with Facebook. You can try again or user another login method')
                return redirect_to_register(error)


class Username(auth.UniqueUsernameMixin):
    '''
    Ask for the user to select a username
    '''
    username_form = web.form.Form(web.form.Textbox('username', web.form.notnull, autocomplete='off',
                                                 id='username', placeholder=_('Select a username for your profile.'),
                                                 ),
                                web.form.Textbox('email', web.form.notnull, autocomplete='off', id='email',
                                                 placeholder='Where we\'ll never spam you.'),
                                web.form.Password('password', web.form.notnull, id='password', autocomplete='off',
                                                  placeholder='Something you\'ll remember but others won\'t guess.'),
                                web.form.Button(_('Next')))

    def GET(self):
        sess = session.get_session()
        if self.username_already_exists(sess.fb_profile['username']):
            username = self.suggest_a_username(sess.fb_profile['username'])
        else:
            username = sess.fb_profile['username']
        form = self.username_form()
        form['username'].set_value(username)
        form['email'].set_value(sess.fb_profile['email'])
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
        values = {'name': sess.fb_profile['name'],
                  'username': self.form['username'].value,
                  'facebook': sess.fb_profile['username'],
                  'login_source': auth.LOGIN_SOURCE_FACEBOOK,
                  }
        # extended profile data, may not be always available
        try:
            hometown = sess.fb_profile.get('hometown', None)
            if hometown:
                hometown_name = hometown.get('name', None)
                if hometown_name:
                    values['hometown'] = hometown_name
        except:
            logger.info('could not get hometown', exc_info=True)
        try:
            location = sess.fb_profile.get('location', None)
            if location:
                location_name = location['name']
                if location_name:
                    city_and_country = location_name.split(',')
                    values['city'] = city_and_country[0].strip()
                    if len(city_and_country) > 1:
                        values['country'] = city_and_country[1].strip()
        except:
            logger.info('could not get city and country', exc_info=True)
        try:
            website = sess.fb_profile.get('website', None)
            if website:
                values['website'] = website
        except:
            logger.info('could not get website', exc_info=True)
        try:
            birthday = sess.fb_profile.get('birthday', None)
            if birthday:
                values['birthday'] = birthday
        except:
            logger.info('could not get birthday', exc_info=True)
        self.user_id = auth.create_user(self.form['email'].value, self.form['password'].value, **values)
        self.grab_and_insert_profile_picture()
        return self.user_id

    def grab_and_insert_profile_picture(self):
        sess = session.get_session()
        db = database.get_db()
        album_id = db.insert(tablename='albums', name=_('Profile Pictures'), user_id=self.user_id)
        photo_id = db.insert(tablename='photos', album_id=album_id)
        picture_url = 'https://graph.facebook.com/{0}/picture'.format(sess.fb_profile['username'])
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
            logger.info('Could not obtain faceboog profile picture', exc_info=True)


class Login(FacebookOauthStart):
    '''
    Starts a login action
    '''
    def __init__(self):
        super(Login, self).__init__(web.ctx.home + '/login_return')


class LoginReturn(FacebookOauthReturnMixin):
    def __init__(self):
        super(LoginReturn, self).__init__(web.ctx.home + '/login_return')

    def GET(self):
        error = web.input(error=None)['error']
        if error:
            error = web.input(error_description='')['error_description']
            full_error = _('There was a problem with login with Facebook. You can try again or user another login method: {}').format(error)
            return redirect_to_register(full_error)
        else:
            self.code = web.input(code=None)['code']
            if self.code:
                if not self._check_state_parameter():
                    return redirect_to_register(_('Detected a possible request forge'))
                if not self._exchange_code_for_access_token():
                    return redirect_to_register(_('Invalid facebook login'))
                if not self._obtain_user_profile():
                    return redirect_to_register(_('Invalid facebook login'))
                user_id = self._get_user_from_db()
                if not user_id:
                    # user not registered, let's register
                    web.seeother(url='/register/')
                else:
                    sess = session.get_session()
                    auth.login_user(sess, user_id)
                    web.seeother(url='/{}'.format(self.username), absolute=True)
            else:
                error = _('Failure in the OAuth protocol with Facebook. You can try again or user another login method')
                return redirect_to_register(error)


# register the app for using in the main urls
app = web.application(urls, locals())
