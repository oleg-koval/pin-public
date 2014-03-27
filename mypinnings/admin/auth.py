import web

from mypinnings import session


def login():
    sess = session.get_session()
    if 'ok' not in sess or not sess['ok']:
        raise web.seeother('/login')

def login_required(f):
    '''
    Decorator to force login
    '''
    def not_logged_in(self, *args, **kwargs):
        sess = session.get_session()
        if 'ok' not in sess or not sess['ok']:
            raise web.seeother('/login')
        else:
            return f(self, *args, **kwargs)
    return not_logged_in