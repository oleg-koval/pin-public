import logging

import web

from mypinnings import pin_utils
from mypinnings import session
from mypinnings import database
from mypinnings.api import api_request, convert_to_id, convert_to_logintoken


logger = logging.getLogger('mypinnings.pin')


urls = ('/(\d+)/?', 'Pin',
        )


class Pin(object):
    form = web.form.Form(web.form.Textbox('title', web.form.notnull),
                         web.form.Textbox('description'),
                         web.form.Textbox('price'),
                         web.form.Textbox('tags'),
                         web.form.Textbox('price_range', web.form.notnull),
                         web.form.Textbox('link'),
                         web.form.Textbox('product_url'),
                         web.form.Textbox('board_id'),
                         web.form.Textbox('board_name'),
                         )
    
    def POST(self, pin_id):
        input_values = web.input(category_check=[])
        form_data = self.form(input_values)
        if form_data.validates():
            if not form_data.d.link and not form_data.d.product_url:
                return "Invalid url for the product"
            if not form_data.d.board_id and not form_data.d.board_name:
                return "Invalid board"
            # db = database.get_db()
            # transaction = db.transaction()
            # try:
            if form_data.d.board_id:
                board = form_data.d.board_id
            else:
                board = db.insert('boards', name=form_data.d.board_name)
            sess = session.get_session()

            logintoken = convert_to_logintoken(sess.user_id)

            data = {
                'image_id': pin_id,
                'image_title': form_data.d.title,
                'image_desc': form_data.d.description,
                'link': form_data.d.link,
                'price': form_data.d.price or None,
                'product_url': form_data.d.product_url,
                'price_range': form_data.d.price_range,
                'board_id': board,
                'hash_tag_add_list': form_data.d.tags.split(),
                "csid_from_client": '',
                "logintoken": logintoken
            }

            data = api_request("api/image/mp", "POST", data)
            if data['status'] == 200:
                return web.seeother(
                    url='/p/{}'.format(data['data']['external_id']),
                    absolute=True
                )
                # pin = pin_utils.update_base_pin_information(db=db,
                #                                             pin_id=pin_id,
                #                                             user_id=sess.user_id,
                #                                             title=form_data.d.title,
                #                                             description=form_data.d.description,
                #                                             link=form_data.d.link,
                #                                             tags=form_data.d.tags,
                #                                             price=form_data.d.price or None,
                #                                             product_url=form_data.d.product_url,
                #                                             price_range=form_data.d.price_range,
                #                                             board_id=board)
                # transaction.commit()
                # return web.seeother(url='/p/{}'.format(pin.external_id), absolute=True)
            # except Exception as e:
            #     logger.error('Error updating pin', exc_info=True)
            #     transaction.rollback()
        return "Invalid data"


app = web.application(urls, locals())
