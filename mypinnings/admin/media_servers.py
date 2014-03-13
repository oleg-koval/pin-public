import json

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


ServerForm = web.form.Form(web.form.Textbox('url', web.form.notnull, description="URL", size='60',
                                             placeholder='http://mypinnings.com/static/media/{path}/{media}'),
                            web.form.Textbox('path', web.form.notnull, description='Fyle system path so save images', size='60',
                                              placeholder='/var/www/pin/static/media/'),
                            web.form.Checkbox('active', value='ok', description='Is active for upload'),
                            web.form.Button('Save'))


class AddNewMediaServer(object):
    @login_required(roles=['media_server'])
    def GET(self):
        form = ServerForm()
        form['active'].checked = True
        return template.admin.form(form, 'Add media server')

    @login_required(roles=['media_server'])
    def POST(self):
        form = ServerForm()
        if form.validates():
            db = database.get_db()
            db.insert(tablename='media_servers', active=form.d.active, url=form.d.url, path=form.d.path)
            return web.seeother(url='/media_servers/')
        else:
            return template.admin.form(form, 'Media Server - invalid data')


class EditMediaServer(object):
    @login_required(roles=['media_server'])
    def GET(self, id):
        form = ServerForm()
        db = database.get_db()
        results = db.where(table='media_servers', id=id)
        for row in results:
            form['url'].value = row.url
            form['path'].value = row.path
            form['active'].checked = row.active
            break
        else:
            return "No such media server"
        return template.admin.form(form, 'Add media server')

    @login_required(roles=['media_server'])
    def POST(self, id):
        form = ServerForm()
        if form.validates():
            db = database.get_db()
            db.update(tables='media_servers', where='id=$id', vars={'id': id},
                      active=form.d.active, url=form.d.url, path=form.d.path)
            return web.seeother(url='/media_servers/')
        else:
            return template.admin.form(form, 'Media Server - invalid data')

    @login_required(roles=['media_server'])
    def DELETE(self, id):
        db = database.get_db()
        db.delete(table='media_servers', where='id=$id', vars={'id': id})
        return json.dumps({'status': 'ok'})