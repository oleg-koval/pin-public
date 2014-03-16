'''
This module is for interfaces to speed user data loading, like Pin Loaders
'''
import logging
import urllib
import os
import os.path
from gettext import gettext as _
from PIL import Image

import web

from mypinnings import cached_models
from mypinnings import template
from mypinnings import session
from mypinnings import auth
from mypinnings import database


logger = logging.getLogger('mypinnings.data_loaders')


class PinLoaderPage(object):
    def get_form(self):
        categories = tuple((cat.id, cat.name) for cat in cached_models.all_categories)
        form = web.form.Form(web.form.Dropdown('category', categories, web.form.notnull),
                             web.form.Textbox('imageurl1'),
                             web.form.Textbox('imageurl2'),
                             web.form.Textbox('imageurl3'),
                             web.form.Textbox('imageurl4'),
                             web.form.Textbox('imageurl5'),
                             web.form.Textbox('imageurl6'),
                             web.form.Textbox('imageurl7'),
                             web.form.Textbox('imageurl8'),
                             web.form.Textbox('imageurl9'),
                             web.form.Textbox('imageurl10'),
                             web.form.File('image1'),
                             web.form.File('image2'),
                             web.form.File('image3'),
                             web.form.File('image4'),
                             web.form.File('image5'),
                             web.form.File('image6'),
                             web.form.File('image7'),
                             web.form.File('image8'),
                             web.form.File('image9'),
                             web.form.File('image10'),
                             web.form.Textbox('title1'),
                             web.form.Textbox('title2'),
                             web.form.Textbox('title3'),
                             web.form.Textbox('title4'),
                             web.form.Textbox('title5'),
                             web.form.Textbox('title6'),
                             web.form.Textbox('title7'),
                             web.form.Textbox('title8'),
                             web.form.Textbox('title9'),
                             web.form.Textbox('title10'),
                             web.form.Textarea('description1'),
                             web.form.Textarea('description2'),
                             web.form.Textarea('description3'),
                             web.form.Textarea('description4'),
                             web.form.Textarea('description5'),
                             web.form.Textarea('description6'),
                             web.form.Textarea('description7'),
                             web.form.Textarea('description8'),
                             web.form.Textarea('description9'),
                             web.form.Textarea('description10'),
                             web.form.Textbox('link1'),
                             web.form.Textbox('link2'),
                             web.form.Textbox('link3'),
                             web.form.Textbox('link4'),
                             web.form.Textbox('link5'),
                             web.form.Textbox('link6'),
                             web.form.Textbox('link7'),
                             web.form.Textbox('link8'),
                             web.form.Textbox('link9'),
                             web.form.Textbox('link10'),
                             web.form.Textbox('tags1', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags2', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags3', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags4', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags5', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags6', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags7', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags8', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags9', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags10', placeholder='#this #is #awesome'),
                             web.form.Button('add', id='btn-add')
                             )
        return form()

    def GET(self):
        auth.force_login(session.get_session())
        form = self.get_form()
        errors = web.input(errors=None)['errors']
        return template.ltpl('pin_loader', form, errors)

    def POST(self):
        sess = session.get_session()
        auth.force_login(sess)
        form = self.get_form()
        errors = []
        if form.validates():
            category = form.d.category
            for i in range(10):
                error = self.save_pin(form, str(i + 1), category)
                if error:
                    errors.append(error)
            if errors:
                str_errors = ' - '.join(errors)
                return web.seeother('?errors={}'.format(urllib.quote_plus(str_errors)))
            else:
                return web.seeother('')
        else:
            return template.ltpl('pin_loader', form)

    def save_pin(self, form, i, category):
        title = form['title' + i]
        if title and title.value:
            description = form['description' + i]
            link = form['link' + i]
            imageurl = form['imageurl' + i]
            image = web.input(**{'image' + i: {}}).get('image' + i, None)
            tags = form['tags' + i]
            error = self.validate_errors(title, description, link, imageurl, image, tags)
            pin_id = None
            if error:
                return error
            try:
                pin_id = self.save_pin_in_db(category, title.value, description.value, link.value, tags.value)
                self.save_image(pin_id, imageurl, image)
            except Exception as e:
                if pin_id:
                    self.delete_pin_from_db(pin_id)
                return str(e)
        return None

    def validate_errors(self, title, description, link, imageurl, image, tags):
        if not description or not description.value:
            return _("No description for pin with title: {}").format(title.value)
        if not link or not link.value:
            return _("No link for pin with title: {}").format(title.value)
        if not image and not imageurl and not imageurl.value:
            return _("No image URL for pin with title: {}").format(title.value)
        return None

    def save_pin_in_db(self, category, title, description, link, tags):
        try:
            db = database.get_db()
            sess = session.get_session()
            pin_id = db.insert(tablename='pins', name=title, description=description,
                               user_id=sess.user_id, link=link, category=category,
                               views=1)
            if tags:
                db.insert(tablename='tags', pin_id=pin_id, tags=tags)
            db.insert(tablename='likes', pin_id=pin_id, user_id=sess.user_id)
            return pin_id
        except:
            logger.error('Cannot insert a pin in the DB with the pin loader ingerface',
                         exc_info=True)
            raise

    def delete_pin_from_db(self, pin_id):
        try:
            db = database.get_db()
            db.delete(table='likes', where='pin_id=$id', vars={'id': pin_id})
            db.delete(table='tags', where='pin_id=$id', vars={'id': pin_id})
            db.delete(table='pins', where='id=$id', vars={'id': pin_id})
        except:
            logger.error('Cannot delete pin when doing pin uploader interface', exc_info=True)

    def save_image(self, pin_id, imageurl, image):
        if imageurl and imageurl.value:
            self.save_image_from_url(pin_id, imageurl.value)
        else:
            new_filename = 'static/tmp/{}'.format(image.filename)
            with open(new_filename, 'w') as f:
                f.write(image.file.read())
            self.save_image_from_file(pin_id, new_filename)

    def save_image_from_url(self, pin_id, url):
        filename, _ = urllib.urlretrieve(url)
        self.save_image_from_file(pin_id, filename)

    def save_image_from_file(self, pin_id, filename):
        new_filename = 'static/tmp/{}.png'.format(pin_id)
        if filename.endswith('.png'):
            os.rename(filename, new_filename)
        else:
            img = Image.open(filename)
            img.save(new_filename)
        img = Image.open(new_filename)
        width, height = img.size
        ratio = 202.0 / float(width)
        width = 202
        height *= ratio
        img.thumbnail((width, int(height)), Image.ANTIALIAS)
        img.save('static/tmp/pinthumb{}.png'.format(pin_id))
        os.unlink(filename)
