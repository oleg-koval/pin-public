import web

from mypinnings import database
from mypinnings import auth
from mypinnings import session
from mypinnings import tpllib
from mypinnings import cached_models


admin = None


def tpl(*params):
    global template_obj
    return template_obj(*params)


def template_closure(directory):
    templates = web.template.render(directory,
        globals={'sess': session.get_session(), 'tpl': tpl, 'tpllib': tpllib})
    def render(name, *params):
        return getattr(templates, name)(*params)
    return render


def csrf_token():
    if not 'csrf_token' in session:
        from uuid import uuid4
        session.csrf_token = uuid4().hex
    return session.csrf_token

def ltpl(*params):
    sess = session.get_session()
    if auth.logged_in(sess):
        db = database.get_db()
        user = database.dbget('users', sess.user_id)
        acti_needed = user.activation
        notif_count = db.select('notifs', what='count(*)', where='user_id = $id', vars={'id': sess.user_id})
        all_albums = list(db.select('albums', where="user_id=%s" % (sess.user_id), order='id'))
        boards = db.where(table='boards', order='name', user_id=sess.user_id)
        return tpl('layout', tpl(*params), cached_models.all_categories, boards, all_albums, user, acti_needed, notif_count[0].count, csrf_token)
    return tpl('layout', tpl(*params), cached_models.all_categories)


def lmsg(msg):
    return tpl('layout', msg, {})


def atpl(*params, **kwargs):
    if 'phase' not in kwargs:
        raise Exception('phase needed in atpl')
    return tpl('register/asignup', tpl(*params), kwargs['phase'])

def initialize(directory):
    global template_obj
    global admin
    template_obj = template_closure(directory)
    admin = web.template.render(loc='t/admin', base='layout')