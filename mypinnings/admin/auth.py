'''
Authentication for the admin interface
'''
import web

from mypinnings import database
from mypinnings import session
from mypinnings import template
from mypinnings.auth import generate_salt


def salt_and_hash(password, salt):
    hashed = str(hash(password + salt))
    return hashed

class login_required(object):
    def __init__(self, only_super=False, only_managers=False, roles=[]):
        self.only_super = only_super
        self.only_managers = only_managers
        self.roles = frozenset(roles)

    def __call__(self, f):
        def check_login_and_permissions(*args, **kwargs):
            sess = session.get_session()
            user = sess.get('user', None)
            if not user:
                return web.seeother('/login')
            if sess.user.super:
                return f(*args, **kwargs)
            if self.only_admins and not sess.user.super:
                return "You don't have permission to see this page"
            if self.only_managers and not sess.user.manager:
                return "You don't have permission to see this page"
            if not self.roles.issubset(sess.user.roles):
                return "You don't have permission to see this page"
            return f(*args, **kwargs)
        return check_login_and_permissions


class NoSuchAdminUserException(Exception):
    pass


class NoSuchPermissionException(Exception):
    pass


class AdminPermission():
    def __init__(self, perm_id=None, name=None):
        self.perm_id = perm_id
        self.name = name

    @staticmethod
    def load_all():
        db = database.get_db()
        results = db.select(tables='users')
        permission_list = []
        for row in results:
            permission = AdminPermission(**row)
            permission_list.append(permission)
        return permission

    @staticmethod
    def load(id_or_name):
        try:
            permission = AdminPermission._load_by_id(id_or_name)
        except NoSuchPermissionException:
            permission = AdminPermission._load_by_name(id_or_name)
        return permission

    @staticmethod
    def _load_by_id(perm_id):
        pass

    @staticmethod
    def _load_by_name(name):
        pass


class AdminUser(object):
    '''
    User model for the administration interface
    '''
    def __init__(self, id=None, username=None, pwsalt=None, pwhash=None, super=False, manager=False, storage=None):
        if storage:
            self.id = storage.id
            self.username = storage.username
            self.pwsalt = storage.pwsalt
            self.pwhash = storage.pwhash
            self.super = storage.super
            self.manager = storage.manager
        else:
            self.id = id
            self.username = username
            self.pwsalt = pwsalt
            self.pwhash = pwhash
            self.super = super
            self.manager = manager

    def has_valid_password(self, password):
        if not self.pwsalt or not self.pwhash:
            return False
        salted_and_hashed = salt_and_hash(password, self.pwsalt)
        return salted_and_hashed == self.pwhash

    @staticmethod
    def load(id):
        db = database.get_db()
        results = db.where(table='admin_users', id=id)
        if len(results) > 0:
            row = results[0]
            user = AdminUser(**row)
            return user
        else:
            raise NoSuchAdminUserException('No such user')

    @staticmethod
    def get_with_password(username=None, password=None):
        db = database.get_db()
        results = db.where(table='admin_users', username=username)
        for row in results:
            user = AdminUser(storage=row)
            if user.has_valid_password(password):
                return user
            else:
                NoSuchAdminUserException('Invalid password')
        else:
            raise NoSuchAdminUserException('No such user')


class PageLogin:
    _form = web.form.Form(
        web.form.Textbox('username'),
        web.form.Password('password'),
        web.form.Button('login')
    )

    def GET(self):
        sess = session.get_session()
        sess.user = False
        return web.template.frender('t/admin/form.html')(self._form, 'Login')
        return template.admin.form(self._form, 'Login')

    def POST(self):
        form = self._form()
        if not form.validates():
            return 'Invalid user'

        try:
            user = AdminUser.get_with_password(form.d.username, form.d.password)
        except NoSuchAdminUserException:
            return 'password incorrect'

        sess = session.get_session()
        sess.user = user
        raise web.seeother('/')


class PageLogout:
    def GET(self):
        sess = session.get_session()
        sess.kill()
        raise web.seeother('/login')
