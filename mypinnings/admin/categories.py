import os
import os.path
import json
import logging
import urllib

import web
from PIL import Image

from mypinnings import cached_models
from mypinnings import template
from mypinnings import database
from mypinnings import session
from mypinnings.admin.auth import login_required


logger = logging.getLogger('mypinnings.admin.categories')


class ListCategories(object):
    '''
    Shows the category list to edit them and change its properties
    '''
    @login_required
    def GET(self):
        db = database.get_db()
        results = db.query('''select root.id, root.name, child.id as child_id, child.name as child_name, child.is_default_sub_category
                                    from categories root left join categories child on root.id=child.parent
                                    where root.parent is NULL
                                    order by root.name, child.name
                                    '''
                                  )
        category_list = []
        last_root_category = None
        for row in results:
            if not last_root_category or last_root_category['id'] != row.id:
                last_root_category = {'id': row.id, 'name': row.name, 'subcategories': list()}
                category_list.append(last_root_category)
            if row.child_id:
                last_root_category['subcategories'].append({'id': row.child_id,
                                                            'name': row.child_name,
                                                            'default': row.is_default_sub_category
                                                        })
        return template.admin.list_categories(category_list)


FIRST_PRODUCT_LIST_LIMIT = 32
ADDITIONAL_PRODUCT_LIST_LIMIT = 12


class EditCoolProductsForCategory(object):
    '''
    Allows edition of cool products for one category
    '''
    @login_required
    def GET(self, category_id):
        db = database.get_db()
        sess = session.get_session()
        sess.offset = 0
        pins = db.select(tables=['pins'], what="pins.*", order='timestamp desc',
                         where='pins.category=$category_id and pins.id not in (select pin_id from cool_pins where cool_pins.category_id=$category_id)',
                         vars={'category_id': category_id}, offset=sess.offset, limit=FIRST_PRODUCT_LIST_LIMIT)
        categories = db.where(table='categories', id=category_id)
        for c in categories:
            category = c
        json_pins = []
        for pin in pins:
            image_name = 'static/tmp/{}.png'.format(pin.id)
            thumb_image_name = 'static/tmp/pinthumb{}.png'.format(pin.id)
            if os.path.exists(thumb_image_name):
                pin.image_name = '/' + thumb_image_name
            elif os.path.exists(image_name):
                pin.image_name = '/' + image_name
            else:
                continue
            pin['price'] = str(pin['price'])
            json_pins.append(json.dumps(pin))
        sess.offset = FIRST_PRODUCT_LIST_LIMIT
        return template.admin.edit_cool_products_category(category, json_pins)


class EditMoreCoolProductsForCategory(object):
    '''
    Allows edition of cool products for one category
    '''
    @login_required
    def GET(self, category_id):
        db = database.get_db()
        sess = session.get_session()
        pins = db.select(tables=['pins'], what="pins.*", order='timestamp desc',
                         where='pins.category=$category_id and pins.id not in (select pin_id from cool_pins where cool_pins.category_id=$category_id)',
                         vars={'category_id': category_id}, offset=sess.offset, limit=ADDITIONAL_PRODUCT_LIST_LIMIT)
        json_pins = []
        for pin in pins:
            image_name = 'static/tmp/{}.png'.format(pin.id)
            thumb_image_name = 'static/tmp/pinthumb{}.png'.format(pin.id)
            if os.path.exists(thumb_image_name):
                pin.image_name = '/' + thumb_image_name
            elif os.path.exists(image_name):
                pin.image_name = '/' + image_name
            else:
                continue
            json_pins.append(pin)
        sess.offset += ADDITIONAL_PRODUCT_LIST_LIMIT
        web.header('Content-Type', 'application/json')
        print(len(json_pins))
        return json.dumps(json_pins)


class ListCoolProductsForCategory(object):
    @login_required
    def GET(self, category_id):
        db = database.get_db()
        offset = int(web.input(offset=0)['offset'])
        if offset < 0:
            offset = 0
        pins = db.select(tables=['pins', 'cool_pins'], what="pins.*", order='timestamp desc',
                         where='pins.category=$category_id and pins.id=cool_pins.pin_id',
                         vars={'category_id': category_id})
        pins_list = []
        for pin in pins:
            image_name = 'static/tmp/{}.png'.format(pin.id)
            thumb_image_name = 'static/tmp/pinthumb{}.png'.format(pin.id)
            if os.path.exists(thumb_image_name):
                pin.image_name = '/' + thumb_image_name
            elif os.path.exists(image_name):
                pin.image_name = '/' + image_name
            else:
                pin.image_name = ''
            pins_list.append(pin)
        return web.template.frender('t/admin/category_cool_items_list.html')(pins_list)


class ApiCategoryListPins(object):
    '''
    API to list and serach the pins in a category
    '''
    @login_required
    def GET(self, category_id):
        '''
        Searches or returns all pins in this category_id.

        The results are paginated using offset and limit
        '''
        db = database.get_db()
        search_terms = web.input(search_terms=None)['search_terms']
        try:
            search_limit = int(web.input(limit='10')['limit'])
        except ValueError:
            search_limit = 10
        else:
            if search_limit > 50: search_limit = 50
            if search_limit < 5: search_limit = 5
        try:
            search_offset = int(web.input(offset='0')['offset'])
        except ValueError:
            search_offset = 0
        else:
            if search_offset < 0: search_offset = 0
        if search_terms:
            search_terms = "%{}%".format(search_terms.lower())
            pins = db.select(tables=['pins'], order='name',
                             where='category=$category_id and (lower(name) like $search or lower(description) like $search)'
                                ' and id not in (select pin_id from cool_pins where category=$category_id)',
                             vars={'category_id': category_id, 'search': search_terms},
                             limit=search_limit, offset=search_offset)
        else:
            pins = db.select(tables='pins', order='name',
                             where='category=$category_id'
                                ' and id not in (select pin_id from cool_pins where category=$category_id)',
                             vars={'category_id': category_id, 'search': search_terms},
                             limit=search_limit, offset=search_offset)
        list_of_pins = []
        for p in pins:
            list_of_pins.append(dict(p))
        web.header('Content-Type', 'application/json')
        return json.dumps({'limit': search_limit, 'offset': search_offset, 'list_of_pins': list_of_pins,
                           'search_terms': search_terms})


class ApiCategoryPins(object):
    '''
    '''
    @login_required
    def GET(self, pin_id):
        db = database.get_db()
        query_results = db.where(table='pins', id=pin_id)
        pin = None
        for p in query_results:
            pin = dict(p)
            pin['price'] = str(pin['price'])
            image_name = 'static/tmp/{}.png'.format(pin_id)
            thumb_image_name = 'static/tmp/pinthumb{}.png'.format(pin_id)
            if os.path.exists(thumb_image_name):
                pin['image_name'] = '/' + thumb_image_name
            elif os.path.exists(image_name):
                pin['image_name'] = '/' + image_name
            else:
                pin['image_name'] = ''
        if pin:
            web.header('Content-Type', 'application/json')
            return json.dumps(pin)


class ApiCategoryCoolPins(object):
    '''
    API to manage cool pins in a category
    '''
    @login_required
    def PUT(self, category_id, pin_id):
        '''
        Puts the pin in the category's cool pins
        '''
        db = database.get_db()
        try:
            db.insert(tablename='cool_pins', category_id=category_id, pin_id=pin_id)
            image_name = os.path.join('static', 'tmp', str(pin_id)) + '.png'
            image = Image.open(image_name)
            if image.size[0] <= image.size[1]:
                ratio = 72.0 / float(image.size[0])
                height = int(ratio * image.size[1])
                image = image.resize((72, height), Image.ANTIALIAS)
                margin = (height - 72) / 2
                crop_box = (0, margin, 72, 72 + margin)
            else:
                ratio = 72.0 / float(image.size[1])
                width = int(ratio * image.size[0])
                image = image.resize((width, 72), Image.ANTIALIAS)
                margin = (width - 72) / 2
                crop_box = (margin, 0, 72 + margin, 72)
            image = image.crop(crop_box)
            new_name = os.path.join('static', 'tmp', str(pin_id)) + '_cool.png'
            image.save(new_name)
        except:
            db.delete(table='cool_pins', where='category_id=$category_id and pin_id=$pin_id',
                      vars={'category_id': category_id, 'pin_id': pin_id})
            logger.error('Could not add pin ({}) to cool pins for category ({})'.format(pin_id, category_id), exc_info=True)
            raise web.NotFound('Could not add pin to cool pins')
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})

    @login_required
    def DELETE(self, category_id, pin_id):
        '''
        Deletes the pin from the category's cool pins
        '''
        db = database.get_db()
        try:
            db.delete(table='cool_pins', where='category_id=$category_id and pin_id=$pin_id',
                      vars={'category_id': category_id, 'pin_id': pin_id})
            image_name = os.path.join('static', 'tmp', str(pin_id)) + '_cool.png'
            os.unlink(image_name)
        except OSError:
            # could not delete the image, nothing happens
            pass
        except:
            logger.error('Could not delete pin ({}) from cool pins for category ({})'.format(pin_id, category_id), exc_info=True)
            raise web.NotFound('Could not delete pin from cool pins')
        web.header('Content-Type', 'application/json')
        return json.dumps({'status': 'ok'})


class AddCategory(object):
    @login_required
    def GET(self):
        return template.admin.category_add()
    
    @login_required
    def POST(self):
        web_input = web.input(name=None, number_of_sub_categories=None)
        name = web_input['name']
        number_of_sub_categories = web_input['number_of_sub_categories']
        if not name or not number_of_sub_categories:
            return template.admin.category_add('No category added. Review your data')
        db = database.get_db()
        t = db.transaction()
        try:
            category_id = db.insert(tablename='categories', seqname='categories_id_seq', name=name, is_default_sub_category=False, parent=None)
            number_of_sub_categories = int(number_of_sub_categories)
            default_sub_category = web_input.get('default-sub-category', None)
            default_sub_category_mark_not_found = True
            last_sub_category_id = None
            for i in range(number_of_sub_categories):
                name = web_input.get('name{}'.format(i), None)
                if name:
                    is_default = False
                    if default_sub_category and int(default_sub_category) == i:
                        is_default = True
                        default_sub_category_mark_not_found = False
                    last_sub_category_id = db.insert(tablename='categories', seqname='categories_id_seq', name=name,
                              is_default_sub_category=is_default, parent=category_id)
            if default_sub_category_mark_not_found and last_sub_category_id:
                db.update(tables='categories', where='id=$id', vars={'id': last_sub_category_id}, is_default_sub_category=True)
            t.commit()
            return web.seeother(url='/admin/categories', absolute=True)
        except Exception as e:
            t.rollback()
            logger.info('Cannot create category', exc_info=True)
            return template.admin.category_add(str(e))


class EditCategory(object):
    @login_required
    def GET(self, category_id):
        db = database.get_db()
        results = db.where(table='categories', id=category_id)
        for row in results:
            category = dict(row)
            break
        else:
            raise web.notfound("Category not found")
        if not category['parent']:
            results = db.where(table='categories', parent=category_id)
            category['subcategories'] = results
        else:
            category['subcategories'] = None
        message = web.input(message=None)['message']
        return template.admin.category_edit(category, message)
    
    @login_required
    def POST(self, category_id):
        self.category_id = category_id
        self.web_input = web.input(name=None, number_of_sub_categories=None)
        name = self.web_input['name']
        self.number_of_sub_categories = self.web_input['number_of_sub_categories']
        if name:
            self.db = database.get_db()
            transaction = self.db.transaction()
            try:
                self.db.update(tables='categories', where='id=$id', vars={'id': category_id}, name=name)
                if self.number_of_sub_categories:
                    self.save_sub_categories()
                transaction.commit()
                web.seeother(url='/admin/categories', absolute=True)
            except Exception as e:
                transaction.rollback()
                logger.error('Cannot update category {}'.format(category_id), exc_info=True)
                try:
                    error = urllib.urlencode(('message', str(e)))
                except:
                    error = 'message=Cannot update category'
                web.seeother(url='?{}'.format(error), absolute=False)
        else:
            web.seeother(url='', absolute=False)
            
    def save_sub_categories(self):
        number_of_sub_categories = int(self.number_of_sub_categories)
        default_sub_category = int(self.web_input.get('default-sub-category', 0))
        default_sub_category_mark_not_found = True
        last_sub_category_id = None
        self.ids_found = []
        for i in range(number_of_sub_categories):
            subid = self.web_input.get('subid{}'.format(i), None)
            name = self.web_input.get('name{}'.format(i), None)
            if default_sub_category_mark_not_found and default_sub_category == i:
                is_default = True
                default_sub_category_mark_not_found = False
            else:
                is_default = False
            if subid:
                self.db.update(tables='categories', where=('id=$id and parent=$parent'),
                          vars={'id': subid, 'parent': self.category_id},
                          name=name, is_default_sub_category=is_default)
                last_sub_category_id = subid
                self.ids_found.append(int(subid))
            elif name:
                last_sub_category_id = self.db.insert(tablename='categories', seqname='categories_id_seq', name=name,
                      is_default_sub_category=is_default, parent=self.category_id)
                self.ids_found.append(last_sub_category_id)
        if default_sub_category_mark_not_found and last_sub_category_id:
            self.db.update(tables='categories', where='id=$id', vars={'id': last_sub_category_id}, is_default_sub_category=True)
        self.delete_subcategories_not_found()
        
    def delete_subcategories_not_found(self):
        ids_to_delete = []
        results = self.db.where(table='categories', parent=self.category_id)
        for row in results:
            if row.id not in self.ids_found:
                ids_to_delete.append(str(row.id))
        if ids_to_delete:
            # move all of the sub-category items to the parent category
            ids_to_delete_list = ','.join(ids_to_delete)
            self.db.update('pins', where='id in ({})'.format(ids_to_delete_list), category=self.category_id)
            # remove the sub-categories
            self.db.delete('categories', where='id in ({})'.format(ids_to_delete_list))