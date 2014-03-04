'''
Handles registration and login using the twitter service
'''
import random
import time
import logging
from gettext import gettext as _

import web
import twython

from mypinnings import settings
from mypinnings import session
from mypinnings import template
from mypinnings import database
from mypinnings import auth


urls = ('/register', 'Register',
        '/return', 'Return',
        '/email', 'Email',
        '/username', 'Username',)

logger = logging.getLogger('mypinnings.twitter')


class Register(object):
    '''
    Start the twitter login
    '''
    def GET(self):
        sess = session.get_session()
        twitter = twython.Twython(app_key=settings.TWITTER['api_key'],
                                  app_secret=settings.TWITTER['api_secret'],
                                  )
        cb_url = web.ctx.home + '/return'
        try:
            authtw = twitter.get_authentication_tokens(callback_url=cb_url)
            sess['oauth_token'] = authtw['oauth_token']
            sess['oauth_token_secret'] = authtw['oauth_token_secret']
        except:
            logger.error('Could not get auth tokens from twitter, review settings and twitter configuration', exc_info=True)
            return template.lmsg(_('Login to twitter not available.'))
        raise web.seeother(url=authtw['auth_url'], absolute=True)


class Return(auth.UniqueUsernameMixin):
    '''
    Manages the callback from the twitter login
    '''
    def GET(self):
        sess = session.get_session()
        twitter = twython.Twython(app_key=settings.TWITTER['api_key'],
                                  app_secret=settings.TWITTER['api_secret'],
                                  oauth_token=sess['oauth_token'],
                                  oauth_token_secret=sess['oauth_token_secret'])
        oauth_verifier = web.input(oauth_verifier=None)['oauth_verifier']
        try:
            final_step = twitter.get_authorized_tokens(oauth_verifier)
        except:
            logger.error('Twitter authoriation failed', exc_info=True)
            return template.lmsg(_('Twitter authentication failed'))
        if oauth_verifier:
            self.oauth_token = sess['oauth_token'] = final_step['oauth_token']
            self.oauth_toke_secret = sess['oauth_token_secret'] = final_step['oauth_token_secret']
            if not self._get_user_credentials():
                return template.lmsg(_('Invalid twitter login'))
            user_id, email = self._get_user_data_from_db()
            if not user_id:
                self._save_profile_in_session()
                if self.username_already_exists(self.credentials['screen_name']):
                    sess['tw_username'] = self.suggest_a_username(self.credentials['screen_name'])
                    raise web.seeother(url='/username', absolute=False)
                raise web.seeother(url='/email', absolute=False)
            if email:
                auth.login_user(session.get_session(), user_id)
                # username is set in _get_user_data_from_db()
                raise web.seeother(url='/{}'.format(self.username), absolute=True)
            else:
                self._save_profile_in_session()
                raise web.seeother(url='/email', absolute=False)
        else:
            logger.error('No oauth_verifyer %s', web.input())
            return template.lmsg(_("User not authenticated"))

    def _get_user_credentials(self):
        '''
        Get the user profile from twitter, Returns True if the user is
        found in twitter, False otherwise
        '''
        try:
            twitter = twython.Twython(app_key=settings.TWITTER['api_key'],
                                  app_secret=settings.TWITTER['api_secret'],
                                  oauth_token=self.oauth_token,
                                  oauth_token_secret=self.oauth_toke_secret)
            self.credentials = twitter.verify_credentials()
            return True
        except:
            logger.error('User not logged, could not get credentials', exc_info=True)
            return False

    def _get_user_data_from_db(self):
        '''
        Obtains the user_id from the database and return if exists.
        Else returns false.
        '''
        db = database.get_db()
        query_result = db.select(tables='users', where="twitter=$username and login_source=$login_source",
                                   vars={'username': self.credentials['screen_name'],
                                         'login_source': auth.LOGIN_SOURCE_TWITTER})
        for row in query_result:
            self.user_id = row['id']
            self.email = row['email']
            self.username = row['username']
            return self.user_id, self.email
        return False, False

    def _insert_user_to_db(self):
        '''
        Inserts the user into the database using the data that we can extract
        from the twitter credentials.
        '''
        values = {'name': self.credentials['name'],
                  'username': self.credentials['screen_name'],
                  'twitter': self.credentials['screen_name'],
                  'login_source': auth.LOGIN_SOURCE_TWITTER,
                  }
        db = database.get_db()
        user_id = db.insert(tablename='users', **values)
        return user_id

    def _save_profile_in_session(self):
        sess = session.get_session()
        if hasattr(self, 'user_id') and self.user_id:
            sess['tw_user_id'] = self.user_id
        else:
            sess['tw_user_id'] = None
        sess['tw_name'] = self.credentials['name']
        sess['tw_username'] = self.credentials['screen_name']
        sess['tw_twitter'] = self.credentials['screen_name']


class Email(object):
    '''
    Ask for the user email; Twitter API does not provides email
    '''
    _email_form = web.form.Form(web.form.Textbox('email', web.form.notnull, autocomplete='off',
                                                 id='email', placeholder=_('Where we\'ll never spam you.'),
                                                 ),
                                web.form.Button(_('Next')))

    def GET(self):
        form = self._email_form()
        return template.ltpl('register/twitter/email', form)

    def POST(self):
        form = self._email_form()
        if form.validates():
            user_email = form['email'].value
            sess = session.get_session()
            user_id = sess['tw_user_id']
            db = database.get_db()
            if user_id:
                db.update(tables='users', where='id=$user_id', vars={'user_id': user_id}, email=user_email)
            else:
                values = {'name': sess['tw_name'],
                          'username': sess['tw_username'],
                          'twitter':sess['tw_twitter'],
                          'login_source': auth.LOGIN_SOURCE_TWITTER,
                          'email': user_email,
                          }
                user_id = db.insert(tablename='users', **values)
            auth.login_user(session.get_session(), user_id)
            web.seeother(url='/{}'.format(sess.tw_username), absolute=True)
        else:
            return template.ltpl('register/twitter/email', form, msg=_('Please provide an email'))


class Username(auth.UniqueUsernameMixin):
    '''
    Ask for the user to select a username and email; Twitter API does not provides email
    '''
    _email_form = web.form.Form(web.form.Textbox('username', web.form.notnull, autocomplete='off',
                                                 id='username', placeholder=_('Select a username for your profile.'),
                                                 ),
                                web.form.Textbox('email', web.form.notnull, autocomplete='off',
                                                 id='email', placeholder=_('Where we\'ll never spam you.'),
                                                 ),
                                web.form.Button(_('Next')))

    def GET(self):
        sess = session.get_session()
        form = self._email_form()
        form['username'].set_value(sess.tw_username)
        return template.ltpl('register/twitter/username', form)

    def POST(self):
        form = self._email_form()
        if form.validates():
            self.email = form['email'].value
            self.username = form['username'].value
            if self.username_already_exists(self.username):
                return template.ltpl('register/twitter/username', form, msg=_('Username already exists'))
            self._insert_user_to_db()
            auth.login_user(session.get_session(), self.user_id)
            web.seeother(url='/{}'.format(self.username), absolute=True)
        else:
            return template.ltpl('register/twitter/username', form, msg=_('Please provide an username and email'))

    def _insert_user_to_db(self):
        sess = session.get_session()
        values = {'name': sess['tw_name'],
                  'username': self.username,
                  'twitter': sess['tw_twitter'],
                  'login_source': auth.LOGIN_SOURCE_TWITTER,
                  'email': self.email,
                  }
        db = database.get_db()
        self.user_id = db.insert(tablename='users', **values)
        return self.user_id


app = web.application(mapping=urls, fvars=locals())
