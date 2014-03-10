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
        return template.admin.user_list(form, users_results)

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