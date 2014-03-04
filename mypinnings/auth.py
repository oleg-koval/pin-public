import random
import string

import web

from mypinnings import database


LOGIN_SOURCE_MYPINNINGS = 'MP'
LOGIN_SOURCE_FACEBOOK = 'FB'
LOGIN_SOURCE_TWITTER = 'TW'

def generate_salt(length=10):
    random.seed()
    pool = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(pool) for i in range(length))


def logged_in(sess):
    if 'logged_in' in sess:
        if sess.logged_in:
            return sess.user_id
    return False

def force_login(sess, page='/login', check_logged_in=False):
    user_id = logged_in(sess)
    if not user_id:
        user_id = cookie_logged_in()

    if user_id:
        login_user(sess, user_id)

    redirect = (bool(user_id) == check_logged_in)

    if user_id:
        update_cookie_login(user_id)
    if redirect:
        raise web.seeother(page)


def email_exists(email):
    result = database.get_db().select('users',
        what='1',
        where='email=$email',
        vars={'email': email},
        limit=1)
    return bool(result)


def username_exists(username):
    result = database.get_db().select('users',
        what='1',
        where='username=$username',
        vars={'username': username},
        limit=1)
    return bool(result)


def create_user(email, password, **params):
    pw_hash = hash(password)
    pw_salt = generate_salt()
    pw_hash = hash(pw_hash + pw_salt)

    return database.get_db().insert('users', email=email, pw_hash=pw_hash, pw_salt=pw_salt, **params)


def authenticate_user_email(email, password):
    users = database.get_db().select('users', where='email = $email', vars={'email': email},
    what='id, pw_hash, pw_salt')
    if not users:
        return False

    user = users[0]
    if hash(hash(password) + user['pw_salt']) == user['pw_hash']:
        return user['id']
    return False


def authenticate_user_username(username, password):
    users = database.get_db().select('users', where='username = $username', vars={'username': username}, what='id, pw_hash, pw_salt')
    if not users:
        return False

    user = users[0]
    if hash(hash(password) + user['pw_salt']) == user['pw_hash']:
        return user['id']
    return False


def cookie_logged_in():
    try:
        cookies = web.cookies()
        result = database.get_db().select('users',
            where='id = $user_id and seriesid = $seriesid and logintoken=$logintoken',
            vars=dict((x, getattr(cookies, x)) for x in ['user_id', 'seriesid', 'logintoken']))
        if len(list(result)) == 1:
            return cookies.user_id
    except:
        return False


def update_cookie_login(user_id, new_series_id=False):
    params = {
        'user_id': user_id,
        'logintoken': generate_salt()}
    if new_series_id:
        params['seriesid'] = generate_salt()

    for k, v in params.iteritems():
        web.setcookie(k, v, 9999999)  # a really long time

    del params['user_id']
    database.get_db().update('users',
        where='id = $user_id',
        vars={'user_id': user_id},
        **params)

def login_user(sess, user_id):
    if logged_in(sess):
        return False

    user_id = int(user_id)
    sess.logged_in = True
    sess.user_id = user_id
    update_cookie_login(user_id, new_series_id=True)
    return True

def logout_user(sess):
    sess.kill()
    for x in ['user_id', 'seriesid', 'logintoken']:
        web.setcookie(x, '', expires=-1)


class UniqueUsernameMixin(object):

    def username_already_exists(self, username):
        '''
        Test if the username already exists in the DB
        '''
        db = database.get_db()
        query_result = db.select(tables='users', where="username=$username",
                                   vars={'username': username})
        for _ in query_result:
            return True
        return False

    def suggest_a_username(self, username):
        suggested_username = "{}{}".format(username, random.randrange(999))
        while self.username_already_exists(suggested_username):
            suggested_username = "{}{}".format(username, random.randrange(999))
        return suggested_username