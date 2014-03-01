import web

from mypinnings import database
from mypinnings import auth
from mypinnings import session
from mypinnings import tpllib
from mypinnings import cached_models


def tpl(*params):
    global template_obj
    return template_obj(*params)


def template_closure(directory):
    templates = web.template.render(directory,
        globals={'sess': session.get_session(), 'tpl': tpl, 'tpllib': tpllib})
    def render(name, *params):
        print('19 render', templates, name, params)
        return getattr(templates, name)(*params)
    return render



def ltpl(*params):
    sess = session.get_session()
    if auth.logged_in(sess):
        db = database.get_db()
        user = db.dbget('users', sess.user_id)
        acti_needed = user.activation
        notif_count = db.select('notifs', what='count(*)', where='user_id = $id', vars={'id': sess.user_id})
        all_albums = list(db.select('albums', where="user_id=%s" % (sess.user_id), order='id'))
        return tpl('layout', tpl(*params), cached_models.all_categories, all_albums, user, acti_needed, notif_count[0].count)
    return tpl('layout', tpl(*params), cached_models.all_categories)


def lmsg(msg):
    return tpl('layout', msg)

def initialize(directory):
    global template_obj
    template_obj = template_closure(directory)