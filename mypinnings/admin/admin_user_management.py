import json

import web

from mypinnings import database
from mypinnings import template
from mypinnings.admin.auth import AdminUser, AdminRol, login_required


PAGE_LIMIT = 10


class UsersList(object):
    SearchForm = web.form.Form(web.form.Textbox('search'),
                               web.form.Button('Search'),
                               web.form.Hidden('offset', value=0),
                               web.form.Hidden('limit', value=PAGE_LIMIT))

    @login_required(only_super=True)
    def GET(self):
        db = database.get_db()
        users_results = db.where(table='admin_users', limit=PAGE_LIMIT, offset=0, order='username')
        form = self.SearchForm()
        form.d.offset = 0
        form.d.limit = PAGE_LIMIT
        return template.admin.admin_user_list(form, users_results)

    @login_required(only_super=True)
    def POST(self):
        db = database.get_db()
        form = self.SearchForm()
        if form.validates():
            search = form.d.search.strip().lower()
            offset = int(form.d.offset)
            form.get('limit').value = PAGE_LIMIT
            search = '%{}%'.format(search)
            users_results = db.select(tables='admin_users', limit=PAGE_LIMIT, offset=offset, order='username',
                                      where='username like $search', vars={'search': search})
            return template.admin.user_list(form, users_results)
        return self.GET()


class AddNewUser(object):
    NewUserForm = web.form.Form(web.form.Textbox('username'),
                                web.form.Password('password'),
                                web.form.Checkbox('super', value='ok'),
                                web.form.Checkbox('manager', value='ok'))

    @login_required(only_super=True)
    def GET(self):
        form = self.NewUserForm()
        perms_list = AdminRol.load_all()
        return template.admin.admin_user_insert(form, 'Add admin user', 'Add', perms_list)

    @login_required(only_super=True)
    def POST(self):
        form = self.NewUserForm()
        if form.validates():
            perms_list = AdminRol.load_all()
            perms_list_to_add = []
            for perm in perms_list:
                try:
                    val = web.input()[str(perm.id)]
                    if val == 'ok':
                        perms_list_to_add.append(AdminUser(id=perm.id))
                except KeyError:
                    pass
            user = AdminUser(username=form.d.username, password=form.d.password,
                             super=form.d.super, manager=form.d.manager, roles=perms_list_to_add)
            user.save()
            return web.seeother(url='/admin_users/')
        else:
            return template.admin.form(form, 'Add admin user - invalid data')


class EditUser(object):
    UserForm = web.form.Form(web.form.Textbox('username'),
                                web.form.Checkbox('super', value='ok'),
                                web.form.Checkbox('manager', value='ok'))

    @login_required(only_super=True)
    def GET(self, id):
        user = AdminUser.load(id)
        form = self.UserForm()
        form['username'].value = user.username
        form['super'].checked = user.super
        form['manager'].checked = user.manager
        perms_list = AdminRol.load_all()
        return template.admin.admin_user_edit(form, 'Edit admin user', 'Edit', perms_list, user)

    @login_required(only_super=True)
    def POST(self, id):
        form = self.UserForm()
        if form.validates():
            perms_list = AdminRol.load_all()
            perms_list_to_add = []
            for perm in perms_list:
                try:
                    val = web.input()[str(perm.id)]
                    if val == 'ok':
                        perms_list_to_add.append(AdminUser(id=perm.id))
                except KeyError:
                    pass
            user = AdminUser(id=id, username=form.d.username, super=form.d.super,
                             manager=form.d.manager, roles=perms_list_to_add)
            user.save()
            return web.seeother(url='/admin_users/')
        else:
            return template.admin.form(form, 'Add admin user - invalid data')

    @login_required(only_super=True)
    def DELETE(self, id):
        user = AdminUser(id=id)
        user.delete()
        return json.dumps({'status': 'ok'})


class RolesList(object):
    @login_required(only_super=True)
    def GET(self):
        db = database.get_db()
        roles_list = db.where(table='admin_roles', order='name')
        return template.admin.admin_roles_list(roles_list)


class AddNewRol(object):
    NewRolForm = web.form.Form(web.form.Textbox('name'),
                                      web.form.Button('Add'))

    @login_required(only_super=True)
    def GET(self):
        form = self.NewRolForm()
        return template.admin.form(form, 'Add new permission type')

    @login_required(only_super=True)
    def POST(self):
        form = self.NewRolForm()
        if form.validates():
            rol = AdminRol(name=form.d.name)
            rol.save()
            return web.seeother(url='/admin_roles/', absolute=False)
        else:
            return template.admin.form(form, 'Add new rol type, rol not added')


class EditRol(object):
    NewRolForm = web.form.Form(web.form.Textbox('name'),
                                      web.form.Button('Edit'))

    @login_required(only_super=True)
    def GET(self, id):
        rol = AdminRol.load(id)
        form = self.NewRolForm()
        form['name'].value = rol.name
        return template.admin.form(form, 'Edit rol type')

    @login_required(only_super=True)
    def POST(self, id):
        form = self.NewRolForm()
        if form.validates():
            rol = AdminRol(name=form.d.name, id=id)
            rol.save()
            return web.seeother(url='/admin_roles/', absolute=False)
        else:
            return template.admin.form(form, 'Edit rol type, rol not modified')

    @login_required(only_super=True)
    def DELETE(self, id):
        rol = AdminRol(id=id)
        rol.delete()
        return json.dumps({'status': 'ok'})
