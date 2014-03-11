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
        self.roles = set(roles)

    def __call__(self, f):
        def check_login_and_permissions(*args, **kwargs):
            sess = session.get_session()
            user = sess.get('user', None)
            if not user:
                return web.seeother('/login')
            if sess.user.super:
                return f(*args, **kwargs)
            if self.only_super and not sess.user.super:
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


class AdminRol():
    def __init__(self, id=None, name=None, storage=None):
        if storage:
            self.id = storage.id
            self.name = storage.name
        else:
            self.id = id
            self.name = name

    @staticmethod
    def load_all():
        db = database.get_db()
        results = db.where(table='admin_roles', order='name')
        permissions = []
        for row in results:
            permission = AdminRol(**row)
            permissions.append(permission)
        return permissions

    @staticmethod
    def load(id):
        db = database.get_db()
        results = db.where(table='admin_roles', id=id)
        for row in results:
            permission = AdminRol(**row)
            return permission
        else:
            raise NoSuchPermissionException

    def save(self):
        db = database.get_db()
        if self.id:
            db.update(tables='admin_roles', where='id=$id', vars={'id': self.id}, name=self.name)
        else:
            self.id = db.insert(tablename='admin_roles', name=self.name)

    def delete(self):
        if self.id:
            db = database.get_db()
            db.delete(table='admin_users_roles', where='rol_id=$id', vars={'id': self.id})
            db.delete(table='admin_roles', where='id=$id', vars={'id': self.id})

    def __eq__(self, other):
        if isinstance(other, AdminRol):
            return self.id == other.id
        return False

    def __hash__(self):
        return self.id


class AdminUser(object):
    '''
    User model for the administration interface
    '''
    def __init__(self, id=None, username=None, pwsalt=None, pwhash=None, super=False,
                 manager=False, password=None, storage=None, roles=[]):
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
        self.roles = set(roles)

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
            user._load_roles()
            return user
        else:
            raise NoSuchAdminUserException('No such user')

    def _load_roles(self):
        db = database.get_db()
        results = db.select(tables=['admin_users_roles', 'admin_roles'], what='admin_roles.*',
                            where='admin_users_roles.user_id=$id and admin_users_roles.rol_id=admin_roles.id',
                            vars={'id': self.id})
        for row in results:
            rol = AdminRol(**row)
            self.roles.add(rol)

    @staticmethod
    def get_with_password(username=None, password=None):
        db = database.get_db()
        results = db.where(table='admin_users', username=username)
        for row in results:
            user = AdminUser(storage=row)
            if user.has_valid_password(password):
                user._load_roles()
                return user
            else:
                NoSuchAdminUserException('Invalid password')
        else:
            raise NoSuchAdminUserException('No such user')

    def save(self):
        db = database.get_db()
        if self.id:
            db.update(tables='admin_users', where='id=$id', vars={'id': self.id},
                      super=self.super, manager=self.manager, username=self.username)
            db.delete(table='admin_users_roles', where='user_id=$id', vars={'id': self.id})
        elif self.password:
            self.pwsalt = generate_salt()
            self.pwhash = salt_and_hash(self.password, self.pwsalt)
            userid = db.insert(tablename='admin_users', username=self.username, pwsalt=self.pwsalt, pwhash=self.pwhash,
                      super=self.super, manager=self.manager)
            self.id = userid
        else:
            raise CannotCreateUser('Cannot create user, missing data')
        for rol in self.roles:
            db.insert(tablename='admin_users_roles', user_id=self.id, rol_id=rol.id)

    def delete(self):
        if self.id:
            db = database.get_db()
            db.delete(table='admin_users_roles', where='user_id=$id', vars={'id': self.id})
            db.delete(table='admin_users', where='id=$id', vars={'id': self.id})


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
