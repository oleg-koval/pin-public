import web

from mypinnings import database
from mypinnings import template
from mypinnings.admin.auth import AdminUser, AdminPermission, login_required


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
                                web.form.Checkbox('manager', value='ok'),
                                web.form.Button('Add'))

    def GET(self):
        form = self.NewUserForm()
        return template.admin.form(form, 'Add admin user')

    def POST(self):
        form = self.NewUserForm()
        if form.validates():
            user = AdminUser(username=form.d.username, password=form.d.password,
                             super=form.d.super, manager=form.d.manager)
            user.save()
            return web.seeother(url='/admin_users/')
        else:
            return template.admin.form(form, 'Add admin user - invalid data')


class PermissionsList(object):
    def GET(self):
        db = database.get_db()
        permissions_list = db.where(table='admin_permissions', order='name')
        return template.admin.admin_perms_list(permissions_list)


class AddNewPermission(object):
    NewPermissionForm = web.form.Form(web.form.Textbox('name'),
                                      web.form.Button('Add'))

    def GET(self):
        form = self.NewPermissionForm()
        return template.admin.form(form, 'Add new permission type')

    def POST(self):
        form = self.NewPermissionForm()
        if form.validates():
            permission = AdminPermission(name=form.d.name)
            permission.save()
            return web.seeother(url='/admin_perms/', absolute=False)
        else:
            return template.admin.form(form, 'Add new permission type, permission not added')