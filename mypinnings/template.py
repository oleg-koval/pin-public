import web

from mypinnings import database
from mypinnings import auth
from mypinnings import session
from mypinnings import tpllib
from mypinnings import cached_models
from mypinnings.api import api_request, convert_to_id, convert_to_logintoken
from mypinnings import pin_utils


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
        logintoken = convert_to_logintoken(sess.user_id)
        # Getting profile of a given user
        profile_url = "/api/profile/userinfo/info"
        profile_owner_context = {
            "csid_from_client": "1",
            "id": sess.user_id,
            "logintoken": logintoken}
        user = api_request(profile_url, data=profile_owner_context)\
            .get("data", [])

        if len(user) == 0:
            return u"Profile was not found"
        user = pin_utils.dotdict(user)

        db = database.get_db()

        acti_needed = user.activation
        notif_count = db.select('notifs', what='count(*)', where='user_id = $id', vars={'id': sess.user_id})
        # all_albums = list(db.select('albums', where="user_id=%s" % (sess.user_id), order='id'))
        all_albums = []
        boards = list(db.where(table='boards', order='name', user_id=sess.user_id))
        categories_to_select = list(cached_models.get_categories_with_children(db))
        return tpl('layout', tpl(*params), cached_models.get_categories(), boards, all_albums, user, acti_needed, notif_count[0].count, csrf_token,categories_to_select )
    return tpl('layout', tpl(*params), cached_models.get_categories())


def lmsg(msg, user=None):
    return tpl('layout', msg, cached_models.get_categories(), [], None, user)


def atpl(*params, **kwargs):
    if 'phase' not in kwargs:
        raise Exception('phase needed in atpl')
    return tpl('register/asignup', tpl(*params), kwargs['phase'])

def initialize(directory):
    global template_obj
    global admin
    template_obj = template_closure(directory)
    admin = web.template.render(loc='t/admin', base='layout')
