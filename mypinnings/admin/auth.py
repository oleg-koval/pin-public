'''
Authentication for the admin interface

You can be interested in the @login_required() decorator.
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
    '''
    Decorator to protect access in the admin interface.

    Use this decorator on HTTP request verb methods: GET, POST, DELETE, etc.

    To protect a request requiring only user login:
    @login_required()
    def GET(self):
        pass

    Notice the call to @login_required() has parentesis: this is mandatory

    For a request to be accessible only for the super-users:
    @login_required(only_super=True)

    For a request to be accessible only for the managers:
    @login_required(only_managers=True)

    For a request to be accessible only for users with role pin_loaders:
    @login_required(roles=['pin_loaders'])

    For a request to be accessible only for users with role categories and pins:
    @login_required(roles=['categories', 'pins'])
    must have both roles to access this resource

    Users that are 'super' users have access to all requests.
    '''
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
            if not sess.user.has_all_rol_names(self.roles):
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
    '''
    A role in the administrative site
    '''
    def __init__(self, id=None, name=None, storage=None):
        '''
        Can be initialized by id and name, or by a web.py Storage object (db)
        '''
        if storage:
            self.id = storage.id
            self.name = storage.name
        else:
            self.id = id
            self.name = name

    @staticmethod
    def load_all():
        '''
        Loads all roles
        '''
        db = database.get_db()
        results = db.where(table='admin_roles', order='name')
        permissions = []
        for row in results:
            permission = AdminRol(**row)
            permissions.append(permission)
        return permissions

    @staticmethod
    def load(id):
        '''
        Loads one rol by id
        '''
        db = database.get_db()
        results = db.where(table='admin_roles', id=id)
        for row in results:
            permission = AdminRol(**row)
            return permission
        else:
            raise NoSuchPermissionException

    def save(self):
        '''
        Inserts or updates into the DB
        '''
        db = database.get_db()
        if self.id:
            db.update(tables='admin_roles', where='id=$id', vars={'id': self.id}, name=self.name)
        else:
            self.id = db.insert(tablename='admin_roles', name=self.name)

    def delete(self):
        '''
        Deletes the role from the DB.

        Also removes the role to every user that previously have it
        '''
        if self.id:
            db = database.get_db()
            db.delete(table='admin_users_roles', where='rol_id=$id', vars={'id': self.id})
            db.delete(table='admin_roles', where='id=$id', vars={'id': self.id})

    def __eq__(self, other):
        if isinstance(other, AdminRol):
            return self.id == other.id
        return self.name.equals(other)

    def __hash__(self):
        return self.id


class AdminUser(object):
    '''
    User model for the administration interface
    '''
    def __init__(self, id=None, username=None, pwsalt=None, pwhash=None, super=False,
                 manager=False, password=None, storage=None, site_user_id=None,
                 site_user_email=None, roles=[]):
        '''
        Can be created by indicating the fields or by a web.py Storage object (db)
        '''
        if storage:
            self.id = storage.id
            self.username = storage.username
            self.pwsalt = storage.pwsalt
            self.pwhash = storage.pwhash
            self.super = storage.super
            self.site_user_id = storage.site_user_id
            self.manager = storage.manager
        else:
            self.id = id
            self.username = username
            self.pwsalt = pwsalt
            self.pwhash = pwhash
            self.super = super
            self.manager = manager
            self.password = password
            self.site_user_id = site_user_id
            self.site_user_email = site_user_email
        self.roles = set(roles)

    def has_valid_password(self, password):
        '''
        Test if the user password is valid.

        Useful for login in
        '''
        if not self.pwsalt or not self.pwhash:
            return False
        salted_and_hashed = salt_and_hash(password, self.pwsalt)
        return salted_and_hashed == self.pwhash

    @staticmethod
    def load(id):
        '''
        Loads a user from DB given its id
        '''
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
        '''
        Loads the roles for this user from the DB
        '''
        db = database.get_db()
        results = db.select(tables=['admin_users_roles', 'admin_roles'], what='admin_roles.*',
                            where='admin_users_roles.user_id=$id and admin_users_roles.rol_id=admin_roles.id',
                            vars={'id': self.id})
        for row in results:
            rol = AdminRol(**row)
            self.roles.add(rol)

    @staticmethod
    def get_with_password(username=None, password=None):
        '''
        Get the user from the DB given username and password
        '''
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
        '''
        Inserts or updates the user in the DB.

        Also saves the roles the user have associated
        '''
        db = database.get_db()
        if self.site_user_email:
            # find the site user with this email, this is the users table
            results = db.where(table='users', what='id', email=self.site_user_email)
            for row in results:
                self.site_user_id = row.id
                break
            else:
                raise CannotCreateUser('Cannot create user, that email is not registered for a site user')
        if self.id:
            db.update(tables='admin_users', where='id=$id', vars={'id': self.id},
                      super=self.super, manager=self.manager, username=self.username, site_user_id=self.site_user_id)
            db.delete(table='admin_users_roles', where='user_id=$id', vars={'id': self.id})
        elif self.password:
            self.pwsalt = generate_salt()
            self.pwhash = salt_and_hash(self.password, self.pwsalt)
            userid = db.insert(tablename='admin_users', username=self.username, pwsalt=self.pwsalt, pwhash=self.pwhash,
                      super=self.super, manager=self.manager, site_user_id=self.site_user_id)
            self.id = userid
        else:
            raise CannotCreateUser('Cannot create user, missing data')
        for rol in self.roles:
            db.insert(tablename='admin_users_roles', user_id=self.id, rol_id=rol.id)

    def delete(self):
        '''
        Deletes the user and removes the roles from the user
        '''
        if self.id:
            db = database.get_db()
            db.delete(table='admin_users_roles', where='user_id=$id', vars={'id': self.id})
            db.delete(table='admin_users', where='id=$id', vars={'id': self.id})

    def has_all_rol_names(self, rol_names):
        '''
        Test if the user has all the roles in rol_names

        - rol_names list of string with the names of the roles to test: ['pin_loaders', 'category']

        Returns True if the user has _all_ the roles in the rol_names list, or if the
            rol_names list is empty or None. False otherwise.

        Useful to test that the user has access to some resource
        '''
        for name in rol_names:
            for rol in self.roles:
                if rol.name == name:
                    break
            else:
                return False
        return True

    def change_password(self, password):
        '''
        Changes the password for the user in the DB
        '''
        self.pwsalt = generate_salt()
        self.pwhash = salt_and_hash(password, self.pwsalt)
        db = database.get_db()
        db.update(tables='admin_users', where='id=$id', vars={'id': self.id},
                  pwsalt=self.pwsalt, pwhash=self.pwhash)


class PageLogin:
    '''
    Login to the site

    Saves the logged in user in the session as:

    >>> sess.user:
    <Object: AdminUser>
    '''
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
    '''
    Logouts the user by killing the session
    '''
    def GET(self):
        sess = session.get_session()
        sess.kill()
        raise web.seeother('/login')
