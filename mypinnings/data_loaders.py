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
        sess = session.get_session()
        current_category = sess.get('category', None)
        categories = tuple((cat.id, cat.name) for cat in cached_models.all_categories)
        form = web.form.Form(web.form.Dropdown('category', categories, web.form.notnull, value=current_category),
                             web.form.Textbox('imageurl1', **{'class': 'imagelink', 'i': 1}),
                             web.form.Textbox('imageurl2', **{'class': 'imagelink', 'i': 2}),
                             web.form.Textbox('imageurl3', **{'class': 'imagelink', 'i': 3}),
                             web.form.Textbox('imageurl4', **{'class': 'imagelink', 'i': 4}),
                             web.form.Textbox('imageurl5', **{'class': 'imagelink', 'i': 5}),
                             web.form.Textbox('imageurl6', **{'class': 'imagelink', 'i': 6}),
                             web.form.Textbox('imageurl7', **{'class': 'imagelink', 'i': 7}),
                             web.form.Textbox('imageurl8', **{'class': 'imagelink', 'i': 8}),
                             web.form.Textbox('imageurl9', **{'class': 'imagelink', 'i': 9}),
                             web.form.Textbox('imageurl10', **{'class': 'imagelink', 'i': 10}),
                             web.form.File('image1', **{'class': 'imagefile', 'i': 1}),
                             web.form.File('image2', **{'class': 'imagefile', 'i': 2}),
                             web.form.File('image3', **{'class': 'imagefile', 'i': 3}),
                             web.form.File('image4', **{'class': 'imagefile', 'i': 4}),
                             web.form.File('image5', **{'class': 'imagefile', 'i': 5}),
                             web.form.File('image6', **{'class': 'imagefile', 'i': 6}),
                             web.form.File('image7', **{'class': 'imagefile', 'i': 7}),
                             web.form.File('image8', **{'class': 'imagefile', 'i': 8}),
                             web.form.File('image9', **{'class': 'imagefile', 'i': 9}),
                             web.form.File('image10', **{'class': 'imagefile', 'i': 10}),
                             web.form.Textbox('title1', **{'class': 'titleentry', 'i': 1}),
                             web.form.Textbox('title2', **{'class': 'titleentry', 'i': 2}),
                             web.form.Textbox('title3', **{'class': 'titleentry', 'i': 3}),
                             web.form.Textbox('title4', **{'class': 'titleentry', 'i': 4}),
                             web.form.Textbox('title5', **{'class': 'titleentry', 'i': 5}),
                             web.form.Textbox('title6', **{'class': 'titleentry', 'i': 6}),
                             web.form.Textbox('title7', **{'class': 'titleentry', 'i': 7}),
                             web.form.Textbox('title8', **{'class': 'titleentry', 'i': 8}),
                             web.form.Textbox('title9', **{'class': 'titleentry', 'i': 9}),
                             web.form.Textbox('title10', **{'class': 'titleentry', 'i': 10}),
                             web.form.Textarea('description1', **{'class': 'descrentry', 'i': 1}),
                             web.form.Textarea('description2', **{'class': 'descrentry', 'i': 2}),
                             web.form.Textarea('description3', **{'class': 'descrentry', 'i': 3}),
                             web.form.Textarea('description4', **{'class': 'descrentry', 'i': 4}),
                             web.form.Textarea('description5', **{'class': 'descrentry', 'i': 5}),
                             web.form.Textarea('description6', **{'class': 'descrentry', 'i': 6}),
                             web.form.Textarea('description7', **{'class': 'descrentry', 'i': 7}),
                             web.form.Textarea('description8', **{'class': 'descrentry', 'i': 8}),
                             web.form.Textarea('description9', **{'class': 'descrentry', 'i': 9}),
                             web.form.Textarea('description10', **{'class': 'descrentry', 'i': 10}),
                             web.form.Textbox('link1', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link2', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link3', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link4', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link5', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link6', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link7', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link8', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link9', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link10', **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('tags1', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 1}),
                             web.form.Textbox('tags2', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 2}),
                             web.form.Textbox('tags3', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 3}),
                             web.form.Textbox('tags4', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 4}),
                             web.form.Textbox('tags5', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 5}),
                             web.form.Textbox('tags6', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 6}),
                             web.form.Textbox('tags7', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 7}),
                             web.form.Textbox('tags8', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 8}),
                             web.form.Textbox('tags9', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 9}),
                             web.form.Textbox('tags10', placeholder='#this #is #awesome', **{'class': 'tagwords', 'i': 10}),
                             web.form.Button('add', id='btn-add')
                             )
        return form()

    def GET(self):
        sess = session.get_session()
        auth.force_login(sess)
        form = self.get_form()
        result_info = sess.get('result_info', [])
        return template.ltpl('pin_loader', form, result_info)

    def POST(self):
        sess = session.get_session()
        auth.force_login(sess)
        form = self.get_form()
        result_info = []
        if form.validates():
            sess.category = int(form.d.category)
            for i in range(10):
                result = self.save_pin(form, str(i + 1), sess.category)
                result_info.append(result)
        sess.result_info = result_info
        return web.seeother('')

    def save_pin(self, form, i, category):
        result_info = {'index': i}
        title = form['title' + i]
        if title and title.value:
            description = form['description' + i]
            link = form['link' + i]
            imageurl = form['imageurl' + i]
            image = web.input(**{'image' + i: {}}).get('image' + i, None)
            tags = form['tags' + i]
            error = self.validate_errors(title, description, link, imageurl, image, tags)
            result_info['title'] = title.value
            result_info['description'] = description.value
            result_info['link'] = link.value
            result_info['imageurl'] = imageurl.value
            result_info['image'] = image.filename
            result_info['tags'] = tags.value
            pin_id = None
            if error:
                result_info['error'] = error
                return result_info
            try:
                pin_id = self.save_pin_in_db(category, title.value, description.value, link.value, tags.value)
                result_info['pin_id'] = pin_id
                self.save_image(pin_id, imageurl, image)
            except Exception as e:
                if pin_id:
                    self.delete_pin_from_db(pin_id)
                    del result_info['pin_id']
                result_info['error'] = str(e)
        else:
            result_info['error'] = ''
        return result_info

    def validate_errors(self, title, description, link, imageurl, image, tags):
        if not description.value:
            return _("No description")
        if not link.value:
            return _("No link")
        if not tags.value:
            return _("No tags")
        if not image.filename and not imageurl.value:
            return _("No image URL or no uploaded image file")
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
