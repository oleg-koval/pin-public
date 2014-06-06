import random
import logging

# from mypinnings import database
from mypinnings import media


logger = logging.getLogger('mypinnings.pin_utils')


DIGITS_AND_LETTERS = 'abcdefghijklmnopqrstuvwxwzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'


class PinError(Exception):
    pass


def create_pin(db, user_id, title, description, link, tags, price, product_url,
                   price_range, image_filename=None, board_id=None, repin=None):
    try:
#        if image_filename:
#            images_dict = media.store_image_from_filename(db, image_filename, widths=(202, 212))
#        else:
#            empty = {'url': None, 'width': None, 'height': None}
#            images_dict = {0: empty, 202: empty, 212: empty}
        if not price:
            price = None
        empty = {'url': None, 'width': None, 'height': None}
        images_dict = {0: empty, 202: empty, 212: empty}
        external_id = _generate_external_id()
        pin_id = db.insert(tablename='pins',
                           name=title,
                           description=description,
                           user_id=user_id,
                           link=link,
                           views=1,
                           price=price,
                           image_url=images_dict[0]['url'],
                           image_width=images_dict[0]['width'],
                           image_height=images_dict[0]['height'],
                           image_202_url=images_dict[202]['url'],
                           image_202_height=images_dict[202]['height'],
                           image_212_url=images_dict[212]['url'],
                           image_212_height=images_dict[212]['height'],
                           product_url=product_url,
                           price_range=price_range,
                           external_id=external_id,
                           board_id=board_id,
                           repin=repin)

        if tags:
            tags = remove_hash_symbol_from_tags(tags)
            db.insert(tablename='tags', pin_id=pin_id, tags=tags)

        # Now the redis insert

        # select all friends and people who follows user_id
        query1 = '''
            SELECT follows.follow FROM follows WHERE follows.follower = $id
            UNION
            SELECT friends.id1 FROM friends WHERE friends.id2 = $id'''

        try:
            update_users = list(db.query(query1, {'id': user_id}))
            for update_user in update_users:
                # There might be better way to pass the details of pin
                params = {  'id': pin_id,
                            'name': title,
                            'description': description,
                            'user_id': user_id,
                            'link': link,
                            'views': 1,
                            'price': price,
                            'image_url': images_dict[0]['url'],
                            'image_width': images_dict[0]['width'],
                            'image_height': images_dict[0]['height'],
                            'image_202_url': images_dict[202]['url'],
                            'image_202_height': images_dict[202]['height'],
                            'image_212_url': images_dict[212]['url'],
                            'image_212_height': images_dict[212]['height'],
                            'product_url': product_url,
                            'price_range': price_range,
                            'external_id': external_id,
                            'board_id': board_id,
                            'repin': 0}

                create_feed(update_user['follow'], pin_id=pin_id,
                                      params=storify(params))
        except:
            print 'error while adding to redis or query failed'
        return pin
    except:
        logger.error('Cannot insert a pin in the DB', exc_info=True)
        raise

def create_feed(user_id, pin_id, params):
    """ Creates cached pin and deletes oldest pin if the limit exceedes the user quota """
    try:
        create_feed.counter += 1
        if(redis_has(pin_id) != True):
            # Start transaction
            pipe = redis_create_pipe()
            if(redis_zcount(user_id) > get_user_quota()):
                item = redis_zget(user_id, 0, 0)
                redis_remove(user_id, item)
            redis_set(pin_id, params)
            redis_zadd(user_id, create_feed.counter, pin_id)
            # End transaction
            pipe.execute()
        else:
            redis_zadd(user_id, create_feed.counter, pin_id)
    except:
        logger.error('Cannot insert feed info in the redis while adding pin',
                     exc_info=True)
create_feed.counter = 0

def update_base_pin_information(db, pin_id, user_id, title, description, link, tags, price, product_url,
                   price_range, board_id=None):
    db.update(tables='pins',
               where='id=$id and user_id=$user_id',
               vars={'id': pin_id, 'user_id': user_id},
               name=title,
               description=description,
               link=link,
               price=price,
               product_url=product_url,
               price_range=price_range,
               board_id=board_id,
               )
    db.delete(table='tags', where='pin_id=$pin_id', vars={'pin_id': pin_id})
    tags = parse_tags(tags)
    values_to_insert = [{'pin_id':pin_id, 'tags':tag} for tag in tags]
    db.multiple_insert(tablename='tags', values=values_to_insert)
    pin = db.where('pins', id=pin_id)[0]
    # Update redis
    refresh_individual_user(user_id, pin_id)
    return pin


def update_pin_images(db, pin_id, user_id, image_filename):
    images_dict = media.store_image_from_filename(db, image_filename, widths=(202, 212))
    db.update(tables='pins',
              where='id=$id and user_id=$user_id',
              vars={'id': pin_id, 'user_id': user_id},
              image_url=images_dict[0]['url'],
              image_width=images_dict[0]['width'],
              image_height=images_dict[0]['height'],
              image_202_url=images_dict[202]['url'],
              image_202_height=images_dict[202]['height'],
              image_212_url=images_dict[212]['url'],
              image_212_height=images_dict[212]['height'],
              )
    # Update redis
    refresh_individual_user(user_id, pin_id)


def update_pin_image_urls(db, pin_id, user_id, image_url, image_width, image_height,
                          image_202_url, image_202_height, image_212_url, image_212_height):
    db.update(tables='pins',
              where='id=$id and user_id=$user_id',
              vars={'id': pin_id, 'user_id': user_id},
              image_url=image_url,
              image_width=image_width,
              image_height=image_height,
              image_202_url=image_202_url,
              image_202_height=image_202_height,
              image_212_url=image_212_url,
              image_212_height=image_212_height,
              )
    # Update redis
    refresh_individual_user(user_id, pin_id)


def delete_pin_from_db(db, pin_id, user_id):
    results = db.where(table='pins', id=pin_id, user_id=user_id)
    for _ in results:
        break
    else:
        # this ping does not belog to the user?
        raise PinError('Item does not exists for you.')
    db.delete(table='likes', where='pin_id=$id', vars={'id': pin_id})
    db.delete(table='tags', where='pin_id=$id', vars={'id': pin_id})
    db.delete(table='pins_categories', where='pin_id=$id', vars={'id': pin_id})
    db.delete(table='comments', where='pin_id=$id', vars={'id': pin_id})
    db.delete(table='cool_pins', where='pin_id=$id', vars={'id': pin_id})
    db.delete(table='ratings', where='pin_id=$id', vars={'id': pin_id})
    db.update(tables='pins', where='repin=$id', vars={'id': pin_id}, repin=None)
    db.delete(table='pins', where='id=$id', vars={'id': pin_id})
    # Update redis
    refresh_individual_user(user_id, pin_id)



def add_pin_to_categories(db, pin_id, category_id_list):
    if category_id_list:
        values_to_insert = []
        for category_id in category_id_list:
            values_to_insert.append({'pin_id': pin_id, 'category_id': category_id})
        db.multiple_insert(tablename='pins_categories', values=values_to_insert)
    # Update redis
    refresh_individual_user(user_id, pin_id)


def remove_pin_from__all_categories(db, pin_id):
    db.delete(table='pins_categories', where='pin_id=$pin_id',
                   vars={'pin_id': pin_id})
    # Update redis
    refresh_individual_user(user_id, pin_id)


def update_pin_into_categories(db, pin_id, category_id_list):
    remove_pin_from__all_categories(db, pin_id)
    add_pin_to_categories(db, pin_id, category_id_list)
    # Update redis
    refresh_individual_user(user_id, pin_id)


def parse_tags(value):
    parsed = []
    if value:
        separated = value.split('#')
        for v in separated:
            new_v = v.replace('#', '')
            new_v = new_v.strip()
            if new_v:
                parsed.append(new_v)
    return parsed


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


def _generate_external_id():
    id = _new_external_id()
    while _already_exists(id):
        id = _new_external_id()
    return id


def _new_external_id():
    digits_and_letters = random.sample(DIGITS_AND_LETTERS, 9)
    return ''.join(digits_and_letters)


def _already_exists(id):
    db = database.get_db()
    results = db.where('pins', external_id=id)
    for _ in results:
        return True
    return False


def delete_all_pins_for_user(db, user_id):
    db.delete(table='likes', where='pin_id in (select id from pins where user_id=$id)', vars={'id': user_id})
    db.delete(table='tags', where='pin_id in (select id from pins where user_id=$id)', vars={'id': user_id})
    db.delete(table='pins_categories', where='pin_id in (select id from pins where user_id=$id)', vars={'id': user_id})
    db.delete(table='comments', where='pin_id in (select id from pins where user_id=$id)', vars={'id': user_id})
    db.delete(table='cool_pins', where='pin_id in (select id from pins where user_id=$id)', vars={'id': user_id})
    db.delete(table='ratings', where='pin_id in (select id from pins where user_id=$id)', vars={'id': user_id})
    db.update(tables='pins', where='repin in (select id from pins where user_id=$id)', vars={'id': user_id}, repin=None)
    db.delete(table='pins', where='id in (select id from pins where user_id=$id)', vars={'id': user_id})
    # Update redis
    refresh_individual_user(user_id)


class dotdict(dict):
    '''
    Special dict used for templates compatability
    '''
    def __getattr__(self, name):
        return self[name]
