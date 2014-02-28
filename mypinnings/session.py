import web


sess = None

def debuggable_session(app):
    if web.config.get('_sess') is None:
        sess = web.session.Session(app, web.session.DiskStore('sessions'))
        web.config._sess = sess
        return sess
    return web.config._sess

def initialize(app):
    global sess
    sess = debuggable_session(app)

def get_session():
    global sess
    return sess
