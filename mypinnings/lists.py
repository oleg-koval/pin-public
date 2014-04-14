import json

import web

from mypinnings import database, image_utils
from mypinnings import session
from mypinnings import auth
from mypinnings.conf import settings


class ListItemsJson:
    def get_items(self):
        db = database.get_db()
        self.query = '''
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
                join boards on pins.board_id = boards.id
            where boards.id = $board_id
            group by tags.tags, categories.id, pins.id, users.id
            order by timestamp desc offset $offset limit $limit'''
        results = db.query(self.query, vars={'board_id': self.board_id, 'offset': self.offset * settings.PIN_COUNT, 'limit': settings.PIN_COUNT})
        pin_list = []
        for pin in results:
            if not image_utils.create_thumbnail_212px_for_pin(pin):
                continue
            pin.price = str(pin.price)
            pin_list.append(pin)
        return pin_list
    
    def GET(self, board_id):
        self.board_id = int(board_id)
        self.offset = int(web.input(offset=0).offset)
        sess = session.get_session()
        auth.logged_in(sess)

        pins = self.get_items()
        json_pins = json.dumps(pins)
        return json_pins
