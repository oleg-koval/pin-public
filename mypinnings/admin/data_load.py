import web

from mypinnings import database
from mypinnings import template
from mypinnings import media
from mypinnings import session
from mypinnings.admin.auth import login_required
from mypinnings import cached_models

class LoadPins(object):
    def get_form(self, categories):
        cat_list = []
        for cat in categories:
            cat_list.append((cat.id, cat.name))
        DataForm = web.form.Form(web.form.Textbox('name', web.form.notnull, description='Name', size="60",),
                             web.form.Textarea('description', web.form.notnull, description='Description', cols="60", rows="20"),
                             web.form.Textbox('link', web.form.notnull, description='Complete URL link', placeholder='http://example.com/path/link',
                                              size="80"),
                             web.form.Dropdown('category', cat_list, web.form.notnull, description='Category'),
                             web.form.Textbox('tags', web.form.notnull, description='Tags', placeholder='#follow #this #convention', size="60"),
                             web.form.Textbox('image_url', description='Image from the web', size="80", placeholder='http://'),
                             web.form.File('image', description='...or upload the image'),
                             web.form.Button('Add Pin'))
        return DataForm()

    @login_required(roles=['pin_loader'])
    def GET(self):
        form = self.get_form(cached_models.all_categories)
        return template.admin.form(form, 'Load Pin')

    @login_required(roles=['pin_loader'])
    def POST(self):
        form = self.get_form(cached_models.all_categories)
        if form.validates():
            sess = session.get_session()
            image_file = web.input(image={}).image
            if image_file:
                image_metadata = media.store_image_from_filename(file=image_file.filename, widths=[220, 40])
            elif form.d.image_url:
                image_metadata = media.store_image_from_url(url=form.d.image_url, widths=[220, 40])
            else:
                return "You must provide an image via upload or URL"
            db = database.get_db()
            pin_id = db.insert(tablename='pins', name=form.d.name, description=form.d.description,
                               user_id=sess.user.site_user_id, link=form.d.link, category=form.d.category)
            db.insert('tags', pin_id=pin_id, tags=form.d.tags)
            db.insert('pins_photos', pin_id=pin_id, photo_id=image_metadata.id)
            return web.seeother(url='', absolute=False)
        else:
            return template.admin.form(form, 'Load Pin')
