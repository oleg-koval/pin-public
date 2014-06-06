from sys import path, exit
import web
from web import *
import logging
import redis as redis_server

sys.path.append("/home/smg628/sandbox/pin/")
from mypinnings.database import *


db = None
redis = None
logger = logging.getLogger('mypinnings.pin_utils')
logger.addHandler(logging.NullHandler())

db = connect_db()
redis_connect()


def get_users():
    return db.query('SELECT * FROM users')


def create_feed(user_id, pin_id, params):
    """ Creates cached pin and deletes oldest pin if the limit exceedes the
    user quota """
    try:
        create_feed.counter += 1
        if redis_has(pin_id) is not True:
            # Start transaction
            pipe = redis_create_pipe()
            if(redis_zcount(user_id) > get_user_quota()):
                item = redis_zget(user_id, 0, 0) # the last element
                redis_remove(user_id, item)
            try:
                redis_set(pin_id, params)
                print 'redis_set'
            except Exception, e:
                print e
            redis_zadd(user_id, create_feed.counter, pin_id)
            print '------------------------- ADDED TO CACHED PIN WITH ID: --------------------------'
            print pin_id
            # End transaction
            pipe.execute()
        else:
            redis_zadd(user_id, create_feed.counter, pin_id)
    except Exception, e:
        print e
        logger.error('Cannot insert feed info in the redis while adding pin',
                     exc_info=True)
create_feed.counter = 0


def generate_feed(user_id, user_username, user_name, user_pic, category, cat_name, id, name, description, link, views, price, image_url,
                  image_width, image_height, image_202_url, image_202_height,
                  image_212_url, image_212_height, product_url, price_range,
                  external_id, board_id, tags,  timestamp, repin_count=0, like_count=0):
    try:
        # There might be better way to pass the details of pin
        params = {'id': id,
                  'name': name,
                  'description': description,
                  'user_id': user_id,
                  'user_name': user_name,
                  'user_username': user_username,
                  'user_pic': user_pic,
                  'category': category,
                  'cat_name': cat_name,
                  'link': link,
                  'views': str(views),
                  'price': str(price),
                  'image_url': image_url,
                  'image_width': image_width,
                  'image_height': image_height,
                  'image_202_url': image_202_url,
                  'image_202_height': image_202_height,
                  'image_212_url': image_212_url,
                  'image_212_height': image_212_height,
                  'product_url': product_url,
                  'price_range': price_range,
                  'external_id': external_id,
                  'board_id': board_id,
                  'tags': tags,
                  'timestamp': timestamp,
                  'repin_count': 0,
                  'like_count': like_count,
                  'repin': 0}

        create_feed(user_id, pin_id=id,
                                params=params)
    except Exception, e:
        print e
        print 'error while query'


def get_user_people(user_id):

    query1 = '''
        SELECT follows.follower FROM follows WHERE follows.follow = {id}
        UNION
        SELECT friends.id1 FROM friends WHERE friends.id2 =
        {id}'''.format(id=user_id)

    query2 = '''
        SELECT pins.*, categories.id as category, categories.name as cat_name FROM pins
        LEFT JOIN categories on categories.id in
            (SELECT category_id FROM pins_categories WHERE pin_id = pins.id limit 1)
        WHERE user_id = {id}
        '''.format(id=user_id)

    theuser_query = '''
            SELECT * FROM users WHERE id = {id}
            '''.format(id=user_id)

    theuser = list(db.query(theuser_query))
    theuser = theuser[0]
    update_users = list(db.query(query1))
    user_pins = list(db.query(query2))

    if len(user_pins) <= 0 or len(update_users) <= 0 or theuser is None:
        print '---------------- USER HAS NO DATA TO CACHE --------------------'
        return False


    for update_user in update_users:
        for user_pin in user_pins:
            dictpin = dict(pin_id=user_pin.id)
            tags_obj = db.select('tags', dictpin, where=("pin_id = $pin_id"))
            tags = []
            like_dict = {'pin_id': user_pin.id}
            likes_obj = db.select('likes', like_dict, where=("pin_id=$pin_id"))
            # likes_c = db.query("SELECT COUNT(*) FROM likes")
            # likes = list(likes_obj)
            # likes = int(likes[0].count)
            likes = len(likes_obj)

            repin_count = 0

            for tag in tags_obj:
                tags.append(tag.tags)

            if tags:
                tags = tags
            else:
                tags = ''

            user_query = '''
                SELECT * FROM users WHERE id = {id}
                '''.format(id=update_user.follower)
            user = list(db.query(user_query))
            user = user[0]

            generate_feed(update_user.follower, theuser.username, theuser.name,
                          theuser.pic, user_pin.cat_name, user_pin.category, user_pin.id, user_pin.name, 
                          user_pin.description, user_pin.link, user_pin.views, user_pin.price,
                          user_pin.image_url, user_pin.image_width,
                          user_pin.image_height, user_pin.image_202_url,
                          user_pin.image_202_height, user_pin.image_212_url,
                          user_pin.image_212_height, user_pin.product_url,
                          user_pin.price_range, user_pin.external_id,
                          user_pin.board_id, tags, user_pin.timestamp, repin_count,
                          likes)


def refresh_individual_user(user_id):
    get_user_people(user_id)


if __name__ == '__main__':
    # import mypinnings
    print 'script is working'

    users = get_users()

    for user in users:
        get_user_people(user.id)

    print 'end of script'
