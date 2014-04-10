import web

from mypinnings import database
from mypinnings import session
from mypinnings import template
from mypinnings import cached_models


PIN_COUNT = 20


class PageCategory:
    def GET(self, cid):
        cid = int(cid)
        db = database.get_db()
        sess = session.get_session()
        if cid == 0:
            category = {'name':'Random', 'id': 0}
        else:
            results = db.where('categories', id=cid)
            for r in results:
                category = r
                break
            else:
                return 'Category not found.'

        offset = int(web.input(offset=0).offset)
        ajax = int(web.input(ajax=0).ajax)

        if cid == 0:
            where = 'random() < 0.1'
        else:
            where = 'categories.id = $cid'

        query = '''
            select
                tags.tags, pins.*, categories.id as category, categories.name as cat_name, users.pic as user_pic,
                users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join follows on follows.follow = users.id
                join pins_categories on pins.id=pins_categories.pin_id
                join categories on pins_categories.category_id = categories.id
            where ''' + where + '''
            group by tags.tags, categories.id, pins.id, users.id
            order by timestamp desc offset %d limit %d''' % (offset * PIN_COUNT, PIN_COUNT)

        subcategories = db.where(table='categories', parent=cid, order='is_default_sub_category desc, name')
        existsrs = db.query('select exists(' + query + ') as exists', vars={'cid': cid})
        for r in existsrs:
            if not r.exists:
                subcatrs = db.where(table='categories', parent=cid, is_default_sub_category=True)
                for scrow in subcatrs:
                    cid = scrow.id
                    break
        pins = db.query(query, vars={'cid': cid})
        lists = db.select('boards',
        where='user_id=$user_id',
        vars={'user_id': sess.user_id})
        
        boards = db.where(table='boards', order='name', user_id=sess.user_id)

        print lists
        if ajax:
            return json_pins(pins, 'horzpin')
        return template.ltpl('category', pins, category, cached_models.all_categories, subcategories, boards)
