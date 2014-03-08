'''
Handles registration and login using the facebook service
'''
import random
import urllib
import urlparse
import json
import logging
from gettext import gettext as _

import web

from mypinnings.conf import settings
from mypinnings import template
from mypinnings import session
from mypinnings import database
from mypinnings import auth


urls = ('/register', 'Register',
        '/return', 'Return',
        '/username', 'Username',
        )

logger = logging.getLogger('mypinnings.facebook')

class Register:
    '''
    Start the facebook login
    '''
    def GET(self):
        '''
        Redirects to facebook login page
        '''
        base_url = 'https://www.facebook.com/dialog/oauth?'
        state = str(random.randrange(99999999))
        sess = session.get_session()
        sess['state'] = state
        redirect_url = web.ctx.home + '/return'
        parameters = {'state': state,
                      'client_id': settings.FACEBOOK['application_id'],
                      'redirect_uri': redirect_url,
                      'scope': 'email',
                      }
        url_redirect = base_url + urllib.urlencode(parameters)
        raise web.seeother(url=url_redirect, absolute=True)

class Return(auth.UniqueUsernameMixin):
    '''
    Manages the return from the facebook login
    '''
    def GET(self):
        '''
        Manages the return from the facebook login. On success returns to the root
        of the server url. Else prints a message
        '''
        sess = session.get_session()
        error = web.input(error=None)['error']
        if error:
            errors = web.input()
            template.ltpl('facebook/no-login', **errors)
        else:
            self.code = web.input(code=None)['code']
            if self.code:
                if not self._check_state_parameter():
                    return template.lmsg(_('Detected a possible request forge'))
                if not self._exchange_code_for_access_token():
                    return template.lmsg(_('Invalid facebook login'))
                if not self._obtain_user_profile():
                    return template.lmsg(_('Invalid facebook login'))
                user_id = self._get_user_from_db()
                if not user_id:
                    sess['fb_profile'] = self.profile
                    web.seeother(url='/username', absolute=False)
                else:
                    # user already registered, perform a login instead of registration
                    web.seeother(url="/login/facebook", absolute=True)
            else:
                return template.lmsg(_('Failure in the OAuth protocol with facebook. Try again'))

    def _check_state_parameter(self):
        '''
        Check that the state we send to facebook is the same that facebook
        returns back.
        '''
        sess = session.get_session()
        state = sess['state']
        returned_state = web.input(state=None)['state']
        return state == returned_state

    def _exchange_code_for_access_token(self):
        '''
        Validates the code returned from facebook redirect. If correctly validated,
        returns True, otherwise False
        '''
        try:
            base_url = 'https://graph.facebook.com/oauth/access_token?'
            redirect_url = web.ctx.home + '/return'
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
            logger.error('Cannot cannot obtain user profile. Access token: %s', self.access_token, exc_info=True)
            return False

    def _get_user_from_db(self):
        '''
        Obtains the user_id from the database and return if exists.
        Else returns false.
        '''
        db = database.get_db()
        query_result = db.select(tables='users', where="facebook=$username and login_source=$login_source",
                                   vars={'username': self.profile['username'],
                                         'login_source': auth.LOGIN_SOURCE_FACEBOOK})
        for row in query_result:
            self.user_id = row['id']
            self.username = row['username']
            return self.user_id
        return False


class Username(auth.UniqueUsernameMixin):
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
        if self.username_already_exists(sess.fb_profile['username']):
            username = self.suggest_a_username(sess.fb_profile['username'])
        else:
            username = sess.fb_profile['username']
        form = self.username_form()
        form['username'].set_value(username)
        form['email'].set_value(sess.fb_profile['email'])
        return template.ltpl('register/facebook/username', form)

    def POST(self):
        self.form = self.username_form()
        if self.form.validates():
            if self.username_already_exists(self.form['username'].value):
                return template.ltpl('register/facebook/username', self.form, _('Username already exists'))
            if self.email_already_exists(self.form['email'].value):
                return template.ltpl('register/facebook/username', self.form, _('Email already exists'))
            self._insert_user_to_db()
            auth.login_user(session.get_session(), self.user_id)
            web.seeother(url='/register/after-signup', absolute=True)
        else:
            return template.ltpl('register/facebook/username', self.form, _('Please provide all information'))

    def _insert_user_to_db(self):
        sess = session.get_session()
        values = {'name': sess.fb_profile['name'],
                  'username': self.form['username'].value,
                  'facebook': sess.fb_profile['username'],
                  'login_source': auth.LOGIN_SOURCE_FACEBOOK,
                  }
        self.user_id = auth.create_user(self.form['email'].value, self.form['password'].value, **values)
        return self.user_id


# register the app for using in the main urls
app = web.application(urls, locals())
