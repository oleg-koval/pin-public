'''
This module is for interfaces to speed user data loading, like Pin Loaders
'''
import logging
import urllib
import os
import os.path
import json
from gettext import gettext as _
import math
from PIL import Image

import web

from mypinnings import cached_models
from mypinnings import template
from mypinnings import session
from mypinnings import auth
from mypinnings import database


logger = logging.getLogger('mypinnings.data_loaders')


PRICE_RANGES = ((1, '$'), (2, '$$'), (3, '$$$'), (4, '$$$$'), (5, '$$$$+'))


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


class CategorySelectionMixin(object):
    def save_categories(self):
        values_to_insert = []
        for category_id in self.categories:
            values_to_insert.append({'pin_id': self.pin_id, 'category_id': category_id})
        self.db.multiple_insert(tablename='pins_categories', values=values_to_insert)
        
    
    def remove_categories(self):
        self.db.delete(table='pins_categories', where='pin_id=$pin_id',
                       vars={'pin_id': self.pin_id})
        
    def update_categories(self):
        self.remove_categories()
        self.save_categories()


class PinLoaderPage(FileUploaderMixin, CategorySelectionMixin):
    def get_form(self):
        form = web.form.Form(web.form.Hidden('categories'),
                             web.form.Hidden('category11'),
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
                             web.form.Radio('price_range1', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 1}),
                             web.form.Radio('price_range2', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 2}),
                             web.form.Radio('price_range3', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 3}),
                             web.form.Radio('price_range4', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 4}),
                             web.form.Radio('price_range5', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 5}),
                             web.form.Radio('price_range6', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 6}),
                             web.form.Radio('price_range7', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 7}),
                             web.form.Radio('price_range8', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 8}),
                             web.form.Radio('price_range9', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 9}),
                             web.form.Radio('price_range10', PRICE_RANGES, **{'class': 'prodprice_range', 'i': 10}),
                             web.form.Button('upload', id='btn-add')
                             )
        return form()

    def GET(self):
        sess = session.get_session()
        db = database.get_db()
        auth.force_login(sess)
        form = self.get_form()
        result_info = sess.get('result_info', [])
        results = db.where(table='pins', what='count(1) as pin_count', user_id=sess.user_id)
        for row in results:
            number_of_items_added = row.pin_count
        results = db.query('''
            select parent.id, parent.name, child.id as child_id, child.name as child_name
            from categories parent left join categories child on parent.id = child.parent
            where parent.parent is null
            order by parent.name, child.name
            ''')
        current_parent = None
        categories_as_list = []
        for row in results:
            if not current_parent or current_parent['id'] != row.id:
                current_parent = {'id': row.id, 'name': row.name, 'subcategories': []}
                categories_as_list.append(current_parent)
            if row.child_id:
                current_parent['subcategories'].append({'id': row.child_id, 'name': row.child_name})
        categories_columns = [[], [], [], []]
        categories_x_column = math.ceil(len(categories_as_list) / 4)
        count = 0
        index = 0
        for cat in categories_as_list:
            categories_columns[index].append(cat)
            count += 1
            if count >= categories_x_column and index < 3:
                count = 0
                index += 1
        return template.ltpl('pin_loader', form, result_info, categories_columns, number_of_items_added, sess.get('categories', []))

    def POST(self):
        sess = session.get_session()
        self.db = database.get_db()
        auth.force_login(sess)
        form = self.get_form()
        result_info = []
        if form.validates():
            categories_string = form.d.categories
            categories_separated = categories_string.split(',')
            sess.categories = tuple(int(c) for c in categories_separated)
            self.categories = sess.categories
            for i in range(10):
                result = self.save_pin(form, str(i + 1))
                if not result.get('pin_id', False) and result.get('error', False):
                    result_info.append(result)
        sess.result_info = result_info
        return web.seeother('')

    def save_pin(self, form, i):
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
            price_range = form['price_range' + i]
            error = self.validate_errors(title, description, link, product_url, imageurl, image, tags, price,
                                         price_range)
            result_info['title'] = title.value
            result_info['description'] = description.value
            result_info['link'] = link.value
            result_info['product_url'] = product_url.value
            result_info['imageurl'] = imageurl.value
            result_info['image'] = image.filename
            result_info['tags'] = tags.value
            result_info['price'] = price.value
            result_info['price_range'] = price_range.value
            self.pin_id = None
            if error:
                result_info['error'] = error
                return result_info
            try:
                self.pin_id = self.save_pin_in_db(title.value, description.value, link.value,
                                             tags.value, price.value, imageurl.value,
                                             product_url.value, price_range.value)
                self.save_categories()
                result_info['pin_id'] = self.pin_id
                self.save_image(self.pin_id, imageurl, image)
            except Exception as e:
                if self.pin_id:
                    self.delete_pin_from_db(self.pin_id)
                    if 'pin_id' in result_info:
                        del result_info['pin_id']
                result_info['error'] = str(e)
        else:
            result_info['error'] = ''
        return result_info

    def validate_errors(self, title, description, link, product_url, imageurl, image, tags, price,
                        price_range):
        if not link.value and not product_url.value:
            return _("You must provide at least one of source link or product link")
        if not tags.value:
            return _("No tags")
        if not price_range.value:
            return _("No price range")
        if not image.filename and not imageurl.value:
            return _("No image URL or no uploaded image file")
        return None

    def save_pin_in_db(self, title, description, link, tags, price, imageurl, product_url,
                       price_range):
        try:
            sess = session.get_session()
            if not price:
                price = None
            pin_id = self.db.insert(tablename='pins', name=title, description=description,
                               user_id=sess.user_id, link=link,
                               views=1, price=price, image_url=imageurl, product_url=product_url,
                               price_range=price_range)
            if tags:
                tags = remove_hash_symbol_from_tags(tags)
                self.db.insert(tablename='tags', pin_id=pin_id, tags=tags)
            self.db.insert(tablename='likes', pin_id=pin_id, user_id=sess.user_id)
            return pin_id
        except:
            logger.error('Cannot insert a pin in the DB with the pin loader ingerface',
                         exc_info=True)
            raise

    def delete_pin_from_db(self, pin_id):
        try:
            self.db.delete(table='likes', where='pin_id=$id', vars={'id': pin_id})
            self.db.delete(table='tags', where='pin_id=$id', vars={'id': pin_id})
            self.db.delete(table='pins_categories', where='pin_id=$id', vars={'id': pin_id})
            self.db.delete(table='pins', where='id=$id', vars={'id': pin_id})
        except:
            logger.error('Cannot delete pin when doing pin uploader interface', exc_info=True)


PIN_LIST_LIMIT = 20
PIN_LIST_FIRST_LIMIT = 50
class LoadersEditAPI(FileUploaderMixin, CategorySelectionMixin):
    def GET(self, pin_id=None):
        if pin_id:
            return self.get_by_id(pin_id)
        else:
            return self.get_by_list()

    def get_by_id(self, id):
        sess = session.get_session()
        db = database.get_db()
        results = db.query('''select pins.*, tags.tags
                            from pins left join tags on pins.id = tags.pin_id
                            where pins.id=$id and user_id=$user_id''',
                            vars={'id': id, 'user_id': sess.user_id})
        for row in results:
            web.header('Content-Type', 'application/json')
            row.price = str(row.price)
            row.tags = add_hash_symbol_to_tags(row.tags)
            row.price_range_repr = '$' * row.price_range if row.price_range < 5 else '$$$$+'
            results = db.select(tables=['categories', 'pins_categories'],
                                        where='categories.id = pins_categories.category_id and pins_categories.pin_id=$id',
                                        vars={'id': id})
            row['categories'] = [{'id': catrow.id, 'name': catrow.name} for catrow in results]
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
        results = db.query('''select pins.*, tags.tags, categories.id as category_id, categories.name as category_name
                            from pins join pins_categories pc on pins.id = pc.pin_id
                            join categories on pc.category_id=categories.id
                            left join tags on pins.id = tags.pin_id
                            where user_id=$user_id
                            order by timestamp desc, categories.name
                            offset $offset limit $limit''',
                            vars={'user_id': sess.user_id, 'offset': sess.offset, 'limit': limit})
        sess.offset += len(results)
        pin_list = []
        current_pin = None
        for r in results:
            if os.path.exists('static/tmp/pinthumb{}.png'.format(r.id)):
                if not current_pin or current_pin['id'] != r.id:
                    current_pin = dict(r)
                    current_pin['price'] = str(r.price)
                    current_pin['tags'] = add_hash_symbol_to_tags(r.tags)
                    current_pin['price_range_repr'] = '$' * r.price_range if r.price_range < 5 else '$$$$+'
                    current_pin['categories'] = []
                    pin_list.append(current_pin)
                category = {'id': r.category_id, 'name': r.category_name}
                current_pin['categories'].append(category)
        json_pins = json.dumps(pin_list)
        print(json_pins)
        web.header('Content-Type', 'application/json')
        return json_pins

    def DELETE(self, pin_id):
        try:
            sess = session.get_session()
            self.db = database.get_db()
            self.pin_id = pin_id
            self.remove_categories()
            self.db.delete(table='pins', where='id=$id and user_id=$user_id', vars={'id': pin_id, 'user_id': sess.user_id})
            web.header('Content-Type', 'application/json')
            return json.dumps({'status': 'ok'})
        except:
            logger.info('Cannot delete a pin: {}'.format(pin_id), exc_info=True)
            return web.notfound()

    def get_form(self):
        form = web.form.Form(web.form.Hidden('categories', web.form.notnull),
                             web.form.Textbox('imageurl'),
                             web.form.Textbox('title', web.form.notnull),
                             web.form.Textarea('description'),
                             web.form.Textbox('link'),
                             web.form.Textbox('product_url'),
                             web.form.Textbox('tags', web.form.notnull),
                             web.form.Textbox('price'),
                             web.form.Radio('price_range', PRICE_RANGES, web.form.notnull),
                             validators =[web.form.Validator("Provide source Link", lambda f: f.link or f.product_url)
                                          ])
        return form()

    def POST(self, pin_id):
        form = self.get_form()
        if form.validates():
            web.header('Content-Type', 'application/json')
            sess = session.get_session()
            self.db = database.get_db()
            price = form.d.price or None
            self.db.update(tables='pins', where='id=$id and user_id=$user_id', vars={'id': pin_id, 'user_id': sess.user_id},
                      name=form.d.title, description=form.d.description, link=form.d.link,
                      price=price, product_url=form.d.product_url, price_range=form.d.price_range)
            self.categories = [int(c) for c in form.d.categories.split(',')]
            self.pin_id = pin_id
            self.update_categories()
            results = self.db.where(table='tags', pin_id=pin_id)
            tags = remove_hash_symbol_from_tags(form.d.tags)
            for _ in results:
                self.db.update(tables='tags', where='pin_id=$id', vars={'id': pin_id}, tags=tags)
                break
            else:
                self.db.insert(tablename='tags', pin_id=pin_id, tags=tags)
            if form.d.imageurl:
                try:
                    self.save_image_from_url(pin_id, form.d.imageurl)
                    self.db.update(tables='pins', where='id=$id and user_id=$user_id', vars={'id': pin_id, 'user_id': sess.user_id},
                              image_url=form.d.imageurl)
                except Exception as e:
                    logger.error('Could not save the image for pin: {} from URL: {}'.format(pin_id, form.d.imageurl), exc_info=True)
                    return json.dumps({'status': str(e)})
            return json.dumps({'status': 'ok'})
        else:
            return web.notfound()


class UpdatePin(FileUploaderMixin, CategorySelectionMixin):
    def POST(self):
        sess = session.get_session()
        result_info = []
        self.pin_id = int(web.input(id11=0)['id11'])
        name = web.input(title11=None)['title11']
        description = web.input(description11=None)['description11']
        image = web.input(image11={})['image11']
        tags = web.input(tags11=None)['tags11']
        link = web.input(link11=None)['link11']
        product_url = web.input(product_url11=None)['product_url11']
        price = web.input(price11=None)['price11'] or None
        price_range = web.input(price_range11=None)['price_range11']
        categories = web.input(category11=None)['categories11']
        errors = {'error': 'Invalid data',
                  'index': 11,
                  'pin_id': self.pin_id,
                  'title': name,
                  'description': description,
                  'imageurl': '',
                  'image': image.filename,
                  'tags': tags,
                  'price': price,
                  'link': link,
                  'product_url': product_url}
        if self.pin_id > 0 and name  and tags and (link or product_url) and price_range:
            self.db = database.get_db()
            self.db.update(tables='pins', where='id=$id and user_id=$user_id', vars={'id': self.pin_id, 'user_id': sess.user_id},
                      name=name, description=description, link=link, price=price,
                      product_url=product_url, price_range=price_range)
            self.categories = [int(c) for c in categories.split(',')]
            self.update_categories()
            results = self.db.where(table='tags', pin_id=self.pin_id)
            tags = remove_hash_symbol_from_tags(tags)
            for _ in results:
                self.db.update(tables='tags', where='pin_id=pin_id', vars={'id': self.pin_id}, tags=tags)
                break
            else:
                self.db.insert(tablename='tags', pin_id=self.pin_id, tags=tags)
            try:
                new_filename = 'static/tmp/{}'.format(image.filename)
                with open(new_filename, 'w') as f:
                    f.write(image.file.read())
                self.save_image_from_file(self.pin_id, new_filename)
            except Exception as e:
                logger.error('Could not save the image for pin: {} from URL: {}'.format(self.pin_id, image.filename), exc_info=True)
                errors['error'] = str(e)
                result_info.append(errors)
        else:
            result_info.append(errors)
        sess.result_info = result_info
        return web.seeother(url='/admin/input/#added', absolute=True)


def remove_hash_symbol_from_tags(value):
    if value:
        separated = value.split(' ')
        fixed = []
        for v in separated:
            new_v = v.replace('#', '')
            fixed.append(new_v)
        return ' '.join(fixed)
    else:
        return value
    
    
def add_hash_symbol_to_tags(value):
    if value:
        separated = value.split(' ')
        fixed = []
        for v in separated:
            if v.startswith('#'):
                fixed.append(v)
            else:
                new_v = '#{}'.format(v)
                fixed.append(new_v)
        return ' '.join(fixed)
    else:
        return value