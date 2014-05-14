import json

import web

from mypinnings import template
from mypinnings import database
from mypinnings import conf
from mypinnings import pin_utils
from mypinnings.admin.auth import login_required


class CategorySelection(object):
    @login_required
    def GET(self):
        db = database.get_db()
        categories = db.where('categories', order='name')
        return template.admin.category_selection(categories)
    
    
class PendingItems(object):
    @login_required
    def GET(self):
        page = int(web.input().page)
        offset = page * conf.settings.PIN_COUNT
        db = database.get_db()
        pins_result = db.query('''
            select
                tags.tags, pins.*, users.pic as user_pic,
                users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join follows on follows.follow = users.id
                left join boards on pins.board_id = boards.id
            where pins.id not in (select pin_id from pins_categories)
            group by tags.tags, pins.id, users.id
            order by timestamp desc offset $offset limit $limit''',
            vars={'offset': offset, 'limit': conf.settings.PIN_COUNT})
        pins = []
        current_pin = None
        for row in pins_result:
            if not current_pin or current_pin['id'] != row.id:
                current_pin = dict(row)
                current_pin['price'] = str(current_pin['price'])
                pins.append(current_pin)
                current_pin['tags'] = []
                if row.tags:
                    current_pin['tags'].append(row.tags)
            else:
                if row.tags and row.tags not in current_pin['tags']:
                    current_pin['tags'].append(row.tags)
        print(json.dumps(pins))
        return json.dumps(pins)
    
    
class AddPinToCategories(object):
    form = web.form.Form(web.form.Textbox('categories', web.form.notnull),
                         web.form.Textbox('pin_id', web.form.notnull))
    @login_required
    def POST(self):
        print(web.data())
        form = self.form()
        if form.validates():
            categories = (int(x) for x in form.d.categories.split(','))
            pin_id = int(form.d.pin_id)
            db = database.get_db()
            pin_utils.update_pin_into_categories(db=db,
                                                 pin_id=pin_id,
                                                 category_id_list=categories)
            return json.dumps({'status': 'ok'})
        return json.dumps({'status': 'error'})