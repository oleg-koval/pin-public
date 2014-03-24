'''
This module is for interfaces to speed user data loading, like Pin Loaders
'''
import logging
import urllib
import os
import os.path
import json
from gettext import gettext as _
from PIL import Image

import web

from mypinnings import cached_models
from mypinnings import template
from mypinnings import session
from mypinnings import auth
from mypinnings import database


logger = logging.getLogger('mypinnings.data_loaders')


class FileUploaderMixin(object):

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
        try:
            os.unlink(filename)
        except:
            pass


class PinLoaderPage(FileUploaderMixin):
    def get_form(self):
        sess = session.get_session()
        current_category = sess.get('category', None)
        categories = tuple((cat.id, cat.name) for cat in cached_models.all_categories)
        form = web.form.Form(web.form.Dropdown('category', categories, web.form.notnull, value=current_category),
                             web.form.Dropdown('category11', categories, value=current_category),
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
                             web.form.Textbox('link1', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link2', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link3', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link4', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link5', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link6', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link7', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link8', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link9', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('link10', placeholder="The original source for this image", **{'class': 'urllink', 'i': 1}),
                             web.form.Textbox('product_url1', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
                             web.form.Textbox('product_url2', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
                             web.form.Textbox('product_url3', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
                             web.form.Textbox('product_url4', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
                             web.form.Textbox('product_url5', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
                             web.form.Textbox('product_url6', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
                             web.form.Textbox('product_url7', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
                             web.form.Textbox('product_url8', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
                             web.form.Textbox('product_url9', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
                             web.form.Textbox('product_url10', placeholder="Where can you buy this item? www.rolex.com", **{'class': 'urlproduct_url', 'i': 1}),
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
                             web.form.Textbox('price1', placeholder='$888.00', **{'class': 'prodprice', 'i': 1}),
                             web.form.Textbox('price2', placeholder='$888.00', **{'class': 'prodprice', 'i': 2}),
                             web.form.Textbox('price3', placeholder='$888.00', **{'class': 'prodprice', 'i': 3}),
                             web.form.Textbox('price4', placeholder='$888.00', **{'class': 'prodprice', 'i': 4}),
                             web.form.Textbox('price5', placeholder='$888.00', **{'class': 'prodprice', 'i': 5}),
                             web.form.Textbox('price6', placeholder='$888.00', **{'class': 'prodprice', 'i': 6}),
                             web.form.Textbox('price7', placeholder='$888.00', **{'class': 'prodprice', 'i': 7}),
                             web.form.Textbox('price8', placeholder='$888.00', **{'class': 'prodprice', 'i': 8}),
                             web.form.Textbox('price9', placeholder='$888.00', **{'class': 'prodprice', 'i': 9}),
                             web.form.Textbox('price10', placeholder='$888.00', **{'class': 'prodprice', 'i': 10}),
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
                if not result.get('pin_id', False) and result.get('error', False):
                    result_info.append(result)
        sess.result_info = result_info
        return web.seeother('')

    def save_pin(self, form, i, category):
        result_info = {'index': i}
        title = form['title' + i]
        if title and title.value:
            description = form['description' + i]
            link = form['link' + i]
            product_url = form['product_url' + i]
            imageurl = form['imageurl' + i]
            image = web.input(**{'image' + i: {}}).get('image' + i, None)
            tags = form['tags' + i]
            price = form['price' + i]
            error = self.validate_errors(title, description, link, product_url, imageurl, image, tags, price)
            result_info['title'] = title.value
            result_info['description'] = description.value
            result_info['link'] = link.value
            result_info['product_url'] = product_url.value
            result_info['imageurl'] = imageurl.value
            result_info['image'] = image.filename
            result_info['tags'] = tags.value
            result_info['price'] = price.value
            pin_id = None
            if error:
                result_info['error'] = error
                return result_info
            try:
                pin_id = self.save_pin_in_db(category, title.value, description.value, link.value,
                                             tags.value, price.value, imageurl.value,
                                             product_url.value)
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

    def validate_errors(self, title, description, link, product_url, imageurl, image, tags, price):
        if not description.value:
            return _("No description")
        if not link.value:
            return _("No source link")
        if not product_url.value:
            return _("No product link")
        if not tags.value:
            return _("No tags")
        if not image.filename and not imageurl.value:
            return _("No image URL or no uploaded image file")
        return None

    def save_pin_in_db(self, category, title, description, link, tags, price, imageurl, product_url):
        try:
            db = database.get_db()
            sess = session.get_session()
            if not price:
                price = None
            pin_id = db.insert(tablename='pins', name=title, description=description,
                               user_id=sess.user_id, link=link, category=category,
                               views=1, price=price, image_url=imageurl, product_url=product_url)
            if tags:
                tags = remove_duplicate_hash_symbol_for(tags)
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


PIN_LIST_LIMIT = 20
PIN_LIST_FIRST_LIMIT = 50
class LoadersEditAPI(FileUploaderMixin):
    def GET(self, pin_id=None):
        if pin_id:
            return self.get_by_id(pin_id)
        else:
            return self.get_by_list()

    def get_by_id(self, id):
        sess = session.get_session()
        db = database.get_db()
        results = db.query('''select pins.*, tags.tags, categories.name as category_name
                            from pins join categories on pins.category=categories.id
                            left join tags on pins.id = tags.pin_id
                            where pins.id=$id and user_id=$user_id''',
                            vars={'id': id, 'user_id': sess.user_id})
        for row in results:
            web.header('Content-Type', 'application/json')
            row.price = str(row.price)
            return json.dumps(row)
        raise web.notfound()

    def get_by_list(self):
        sess = session.get_session()
        sess.offset = int(web.input(offset=None)['offset'] or sess.get('offset', 0))
        db = database.get_db()
        if sess.offset == 0:
            limit = PIN_LIST_FIRST_LIMIT
        else:
            limit = PIN_LIST_LIMIT
        results = db.query('''select pins.*, tags.tags, categories.name as category_name
                            from pins join categories on pins.category=categories.id
                            left join tags on pins.id = tags.pin_id
                            where user_id=$user_id
                            order by timestamp desc offset $offset limit $limit''',
                            vars={'user_id': sess.user_id, 'offset': sess.offset, 'limit': limit})
        sess.offset += len(results)
        rows = [row for row in results if os.path.exists('static/tmp/pinthumb{}.png'.format(row.id))]
        for r in rows:
            r.price = str(r.price)
        json_pins = json.dumps(rows)
        print(json_pins)
        web.header('Content-Type', 'application/json')
        return json_pins

    def DELETE(self, pin_id):
        try:
            sess = session.get_session()
            db = database.get_db()
            db.delete(table='pins', where='id=$id and user_id=$user_id', vars={'id': pin_id, 'user_id': sess.user_id})
            web.header('Content-Type', 'application/json')
            return json.dumps({'status': 'ok'})
        except:
            logger.info('Cannot delete a pin: {}'.format(pin_id), exc_info=True)
            return web.notfound()

    def get_form(self):
        sess = session.get_session()
        current_category = sess.get('category', None)
        categories = tuple((cat.id, cat.name) for cat in cached_models.all_categories)
        form = web.form.Form(web.form.Dropdown('category', categories, web.form.notnull, value=current_category),
                             web.form.Textbox('imageurl'),
                             web.form.Textbox('title', web.form.notnull),
                             web.form.Textarea('description', web.form.notnull),
                             web.form.Textbox('link', web.form.notnull),
                             web.form.Textbox('product_url', web.form.notnull),
                             web.form.Textbox('tags', web.form.notnull),
                             web.form.Textbox('price'))
        return form()

    def POST(self, pin_id):
        form = self.get_form()
        if form.validates():
            web.header('Content-Type', 'application/json')
            sess = session.get_session()
            db = database.get_db()
            price = form.d.price or None
            db.update(tables='pins', where='id=$id and user_id=$user_id', vars={'id': pin_id, 'user_id': sess.user_id},
                      name=form.d.title, description=form.d.description, link=form.d.link, category=form.d.category,
                      price=price, product_url=form.d.product_url)
            results = db.where(table='tags', pin_id=pin_id)
            tags = remove_duplicate_hash_symbol_for(form.d.tags)
            for _ in results:
                db.update(tables='tags', where='pin_id=$id', vars={'id': pin_id}, tags=tags)
                break
            else:
                db.insert(tablename='tags', pin_id=pin_id, tags=tags)
            if form.d.imageurl:
                try:
                    self.save_image_from_url(pin_id, form.d.imageurl)
                    db.update(tables='pins', where='id=$id and user_id=$user_id', vars={'id': pin_id, 'user_id': sess.user_id},
                              image_url=form.d.imageurl)
                except Exception as e:
                    logger.error('Could not save the image for pin: {} from URL: {}'.format(pin_id, form.d.imageurl), exc_info=True)
                    return json.dumps({'status': str(e)})
            return json.dumps({'status': 'ok'})
        else:
            return web.notfound()


class UpdatePin(FileUploaderMixin):
    def POST(self):
        result_info = []
        pin_id = int(web.input(id11=0)['id11'])
        name = web.input(title11=None)['title11']
        description = web.input(description11=None)['description11']
        image = web.input(image11={})['image11']
        tags = web.input(tags11=None)['tags11']
        link = web.input(link11=None)['link11']
        product_url = web.input(link11=None)['product_url11']
        price = web.input(link11=None)['price11'] or None
        category = web.input(category11=None)['category11']
        errors = {'error': 'Invalid data',
                  'index': 11,
                  'pin_id': pin_id,
                  'title': name,
                  'description': description,
                  'imageurl': '',
                  'image': image.filename,
                  'tags': tags,
                  'price': price,
                  'link': link,
                  'product_url': product_url}
        if pin_id > 0 and name and description and tags and link and product_url:
            sess = session.get_session()
            db = database.get_db()
            db.update(tables='pins', where='id=$id and user_id=$user_id', vars={'id': pin_id, 'user_id': sess.user_id},
                      name=name, description=description, link=link, category=category, price=price,
                      product_url=product_url)
            results = db.where(table='tags', pin_id=pin_id)
            tags = remove_duplicate_hash_symbol_for(tags)
            for _ in results:
                db.update(tables='tags', where='pin_id=pin_id', vars={'id': pin_id}, tags=tags)
                break
            else:
                db.insert(tablename='tags', pin_id=pin_id, tags=tags)
            try:
                new_filename = 'static/tmp/{}'.format(image.filename)
                with open(new_filename, 'w') as f:
                    f.write(image.file.read())
                self.save_image_from_file(pin_id, new_filename)
            except Exception as e:
                logger.error('Could not save the image for pin: {} from URL: {}'.format(pin_id, image.filename), exc_info=True)
                errors['error'] = str(e)
                result_info.append(errors)
        else:
            result_info.append(errors)
        sess.result_info = result_info
        return web.seeother(url='/admin/input/', absolute=True)


def remove_duplicate_hash_symbol_for(value):
    if value:
        separated = value.split(' ')
        fixed = []
        for v in separated:
            if '###' in v:
                new_v = v.replace('###', '#')
            elif '##' in v:
                new_v = v.replace('##', '#')
            else:
                new_v = v
            if new_v != '#':
                fixed.append(new_v)
        return ' '.join(fixed)
    else:
        return value