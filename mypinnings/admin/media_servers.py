import web

from mypinnings import database
from mypinnings import template
from mypinnings.admin.auth import login_required


PAGE_LIMIT = 10


class ListMediaServers(object):
    SearchForm = web.form.Form(web.form.Textbox('search'),
                               web.form.Button('Search'),
                               web.form.Hidden('offset', value=0),
                               web.form.Hidden('limit', value=PAGE_LIMIT))

    @login_required(roles=['media_server'])
    def GET(self):
        db = database.get_db()
        server_results = db.where(table='media_servers', limit=PAGE_LIMIT, offset=0, order='id')
        form = self.SearchForm()
        form.d.offset = 0
        form.d.limit = PAGE_LIMIT
        return template.admin.admin_media_server_list(form, server_results)

    @login_required(roles=['media_server'])
    def POST(self):
        db = database.get_db()
        form = self.SearchForm()
        if form.validates():
            search = form.d.search.strip().lower()
            offset = int(form.d.offset)
            form.get('limit').value = PAGE_LIMIT
            search = '%{}%'.format(search)
            server_results = db.select(tables='media_servers', limit=PAGE_LIMIT, offset=offset, order='id',
                                      where='url like $search', vars={'search': search})
            return template.admin.admin_media_server_list(form, server_results)
        return self.GET()

class AddNewMediaServer(object):
    ServerForm = web.form.Form(web.form.Textbox('url', web.form.notnull, description="URL", size='60',
                                                 placeholder='http://mypinnings.com/static/media/{path}/{media}'),
                                web.form.Textbox('path', web.form.notnull, description='Fyle system path so save images', size='60',
                                                  placeholder='/var/www/pin/static/media/'),
                                web.form.Checkbox('active', value='ok', description='Is active for upload', checked=True),
                                web.form.Button('Save'))

    @login_required(roles=['media_server'])
    def GET(self):
        form = self.ServerForm()
        return template.admin.form(form, 'Add media server')

    @login_required(roles=['media_server'])
    def POST(self):
        form = self.ServerForm()
        if form.validates():
            db = database.get_db()
            db.insert(tablename='media_servers', active=form.d.active, url=form.d.url, path=form.d.path)
            return web.seeother(url='/media_servers/')
        else:
            return template.admin.form(form, 'Media Server - invalid data')