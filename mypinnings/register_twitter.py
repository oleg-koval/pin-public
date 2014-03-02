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
        '/return', 'Return')

logger = logging.getLogger('mypinnings.twitter')


class Register(object):

    def GET(self):
        sess = session.get_session()
        twitter = twython.Twython(app_key=settings.TWITTER['api_key'],
                                  app_secret=settings.TWITTER['api_secret'],
                                  )
        cb_url = web.ctx.home + '/return'
        try:
            auth = twitter.get_authentication_tokens(callback_url=cb_url)
            sess['oauth_token'] = auth['oauth_token']
            sess['oauth_token_secret'] = auth['oauth_token_secret']
        except:
            logger.error('Could not get auth tokens from twitter, review settings and twitter configuration', exc_info=True)
            return template.lmsg(_('Login to twitter not available.'))
        raise web.seeother(url=auth['auth_url'], absolute=True)


class Return(object):

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
            user_id = self._get_user_from_db()
            if not user_id:
                user_id = self._insert_user_to_db()
            auth.login_user(session.get_session(), user_id)
            raise web.seeother(url='/', absolute=True)
        else:
            logger.error('No oauth_verifyer %s', web.input())
            return template.lmsg(_("User not authenticated"))

    def _get_user_credentials(self):
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

    def _get_user_from_db(self):
        '''
        Obtains the user_id from the database and return if exists.
        Else returns false.
        '''
        db = database.get_db()
        query_result = db.select(tables='users', where="username=$username",
                                   vars={'username': self.credentials['screen_name'],
                                         'login_source': auth.LOGIN_SOURCE_TWITTER})
        for row in query_result:
            self.user_id = row['id']
            return self.user_id
        return False

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

app = web.application(mapping=urls, fvars=locals())
