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


class CannotCreateUser(Exception):
    pass


class AdminPermission():
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

    @staticmethod
    def load(id):
        db = database.get_db()
        results = db.where(table='admin_permissions', id=id)
        for row in results:
            permission = AdminPermission(**row)
            return permission
        else:
            raise NoSuchPermissionException

    def save(self):
        db = database.get_db()
        if self.id:
            db.update(tables='admin_permissions', where='id=$id', vars={'id': self.id}, name=self.name)
        else:
            self.id = db.insert(tablename='admin_permissions', name=self.name)

    def delete(self):
        if self.id:
            db = database.get_db()
            db.delete(table='admin_users_permissions', where='user_id=$id', vars={'id': self.id})
            db.delete(table='admin_permissions', where='id=$id', vars={'id': self.id})


class AdminUser(object):
    '''
    User model for the administration interface
    '''
    def __init__(self, id=None, username=None, pwsalt=None, pwhash=None, super=False, manager=False, password=None, storage=None):
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
            self.password = password

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

    def save(self):
        db = database.get_db()
        if self.id:
            db.update(tables='admin_users', where='id=$id', vars={'id': self.id},
                      super=self.super, manager=self.manager)
        elif self.password:
            self.pwsalt = generate_salt()
            self.pwhash = salt_and_hash(self.password, self.pwsalt)
            userid = db.insert(tablename='admin_users', username=self.username, pwsalt=self.pwsalt, pwhash=self.pwhash,
                      super=self.super, manager=self.manager)
            self.id = userid
        else:
            raise CannotCreateUser('Cannot create user, missing data')


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
