'''
This module is for interfaces to speed user data loading, like Pin Loaders
'''
import logging
import urllib
import json
from gettext import gettext as _
import math

import web

from mypinnings import template
from mypinnings import session
from mypinnings import auth
from mypinnings import database
from mypinnings import pin_utils


logger = logging.getLogger('mypinnings.data_loaders')


PRICE_RANGES = ((1, '$'), (2, '$$'), (3, '$$$'), (4, '$$$$'), (5, '$$$$+'))


class PinLoaderPage(object):
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
                             web.form.Textbox('tags1', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 1}),
                             web.form.Textbox('tags2', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 2}),
                             web.form.Textbox('tags3', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 3}),
                             web.form.Textbox('tags4', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 4}),
                             web.form.Textbox('tags5', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 5}),
                             web.form.Textbox('tags6', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 6}),
                             web.form.Textbox('tags7', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 7}),
                             web.form.Textbox('tags8', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 8}),
                             web.form.Textbox('tags9', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 9}),
                             web.form.Textbox('tags10', placeholder='#this is awesome #product', **{'class': 'tagwords', 'i': 10}),
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
                    json_repr = json.dumps(result)
                    result['json'] = json_repr
                    result_info.append(result)
        sess.result_info = result_info
        return web.seeother('')

    def save_pin(self, form, i):
        result_info = {'index': i, 'json': ''}
        title = form['title' + i]
        if title and title.value:
            description = form['description' + i]
            link = form['link' + i]
            product_url = form['product_url' + i]
            imageurl = form['imageurl' + i]
            tags = form['tags' + i]
            price = form['price' + i]
            price_range = form['price_range' + i]
            error = self.validate_errors(title, description, link, product_url, imageurl, tags, price,
                                         price_range)
            result_info['title'] = title.value
            result_info['description'] = description.value
            result_info['link'] = link.value
            result_info['product_url'] = product_url.value
            result_info['imageurl'] = imageurl.value
            result_info['tags'] = tags.value
            result_info['price'] = price.value
            result_info['price_range'] = price_range.value
            self.pin_id = None
            if error:
                result_info['error'] = error
                return result_info
            try:
                transaction = self.db.transaction()
                filename = self.save_image(self.pin_id, imageurl)
                self.pin_id = self.save_pin_in_db(title.value, description.value, link.value,
                                             tags.value, price.value, imageurl.value,
                                             product_url.value, price_range.value, filename)
                pin_utils.add_pin_to_categories(self.db, self.pin_id, self.categories)
                result_info['pin_id'] = self.pin_id
                transaction.commit()
            except Exception as e:
                transaction.rollback()
                if 'pin_id' in result_info:
                    del result_info['pin_id']
                result_info['error'] = str(e)
        else:
            result_info['error'] = ''
        return result_info

    def validate_errors(self, title, description, link, product_url, imageurl, tags, price,
                        price_range):
        if not link.value and not product_url.value:
            return _("You must provide at least one of source link or product link")
        if not tags.value:
            return _("No tags")
        if not price_range.value:
            return _("No price range")
        if not imageurl.value:
            return _("No image URL")
        return None

    def save_pin_in_db(self, title, description, link, tags, price, imageurl, product_url,
                       price_range, image_filename):
        try:
            sess = session.get_session()
            pin = pin_utils.create_pin(self.db, sess.user_id, title, description, link, tags, price,
                                 product_url, price_range, image_filename)
            self.db.insert(tablename='likes', pin_id=pin.id, user_id=sess.user_id)
            return pin.id
        except:
            logger.error('Cannot insert a pin in the DB with the pin loader ingerface',
                         exc_info=True)
            raise

    
    def save_image(self, pin_id, imageurl):
        filename, _ = urllib.urlretrieve(imageurl.value)
        return filename


PIN_LIST_LIMIT = 20
PIN_LIST_FIRST_LIMIT = 50
class LoadersEditAPI(object):
    def GET(self, pin_id=None):
        if pin_id:
            return self.get_by_id(pin_id)
        else:
            return self.get_by_list()

    def get_by_id(self, id):
        sess = session.get_session()
        db = database.get_db()
        results = db.query('''select pins.*
                            from pins
                            where pins.id=$id and user_id=$user_id''',
                            vars={'id': id, 'user_id': sess.user_id})
        for row in results:
            web.header('Content-Type', 'application/json')
            row.price = str(row.price)
            row.price_range_repr = '$' * row.price_range if row.price_range < 5 else '$$$$+'
            results = db.select(tables=['categories', 'pins_categories'],
                                        where='categories.id = pins_categories.category_id and pins_categories.pin_id=$id',
                                        vars={'id': id})
            row['categories'] = [{'id': catrow.id, 'name': catrow.name} for catrow in results]
            results = db.where(table='tags', pin_id=id)
            tags = [r.tags for r in results]
            row['tags'] = tags
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
                            group by pins.id, categories.id, tags.tags
                            order by timestamp desc, pins.id, categories.name
                            offset $offset limit $limit''',
                            vars={'user_id': sess.user_id, 'offset': sess.offset, 'limit': limit})
        sess.offset += len(results)
        pin_list = []
        current_pin = None
        for r in results:
            if not current_pin or current_pin['id'] != r.id:
                current_pin = dict(r)
                current_pin['price'] = str(r.price)
                current_pin['price_range_repr'] = '$' * r.price_range if r.price_range < 5 else '$$$$+'
                current_pin['categories'] = []
                categories = []
                current_pin['tags'] = []
                pin_list.append(current_pin)
            if r.category_id not in categories:
                category = {'id': r.category_id, 'name': r.category_name}
                current_pin['categories'].append(category)
                categories.append(r.category_id)
            if r.tags and r.tags not in current_pin['tags']:
                current_pin['tags'].append(r.tags)
        json_pins = json.dumps(pin_list)
        web.header('Content-Type', 'application/json')
        return json_pins

    def DELETE(self, pin_id):
        try:
            sess = session.get_session()
            db = database.get_db()
            pin_utils.delete_pin_from_db(db, pin_id, sess.user_id)
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
            db = database.get_db()
            price = form.d.price or None
            pin_utils.update_base_pin_information(db,
                                                  pin_id,
                                                  sess.user_id,
                                                  form.d.title,
                                                  form.d.description,
                                                  form.d.link,
                                                  form.d.tags,
                                                  price,
                                                  form.d.product_url,
                                                  form.d.price_range)
            categories = [int(c) for c in form.d.categories.split(',')]
            pin_utils.update_pin_into_categories(db, pin_id, categories)
            if form.d.imageurl:
                try:
                    image_filename, _ = urllib.urlretrieve(form.d.imageurl)
                    pin_utils.update_pin_images(db, pin_id, sess.user_id, image_filename)
                except Exception as e:
                    logger.error('Could not save the image for pin: {} from URL: {}'.format(pin_id, form.d.imageurl), exc_info=True)
                    return json.dumps({'status': str(e)})
            return json.dumps({'status': 'ok'})
        else:
            return web.notfound()
