import web
import logging
from web.utils import storify
from mypinnings import pin_utils

from mypinnings.conf import settings
# from mypinnings import database
import redis as redis_server

db = None
redis = None
logger = logging.getLogger('mypinnings.pin_utils')
logger.addHandler(logging.NullHandler())



def connect_db():
    global db
    if db is not None:
        return db
    db = web.database(**settings.params)
    return db


def dbget(table, row_id):
    global db
    rows = db.select(table, where='id = $id', vars={'id': row_id})
    return rows[0] if rows else None


def get_db():
    global db
    return db


def redis_connect():
    global redis
    if redis is not None:
        return redis
    try:
        pool = redis_server.ConnectionPool(host=settings.redis['host'],
                                           port=settings.redis['port'],
                                           db=settings.redis['db'])
        redis = redis_server.StrictRedis(connection_pool=pool)
        redis.client_setname('mypinnings_redis')
    except redis_server.ConnectionError:
        logger.error("""Error in connection to redis server. Please check if
                     redis-server is running.""")
    return redis


def redis_set(key, value, domain='pin_'):
    domain_key = domain + str(key)
    try:
        redis.set(domain_key, value)
    except:
        logger.error('Error in addition of a value to redis')


def redis_has(key, domain='pin_'):
    domain_key = domain + str(key)
    try:
        if(redis_get(domain_key) is not None):
            return True
        else:
            return False
    except:
        logger.error('Error in triggering redis_has method')
    return False


def redis_get(key, domain='pin_'):
    domain_key = domain + str(key)
    try:
        return redis.get(domain_key)
    except:
        logger.error('Couldnt get a value from redis')


def redis_append(key, value):
    try:
        return redis.append(key, value)
    except:
        logger.error('Couldnt append %d value in %d', value, key)
        return False
    return True


def redis_zadd(key, index, value, domain='user_'):
    domain_key = domain + str(key)
    try:
        ''' Change index var index to value to set unique feature '''
        return redis.zadd(domain_key, value, value)
    except:
        logger.error('Coldnt zadd key %d in index %d with value %', key, index,
                     value)


def redis_zget(key, scope_start=0, scope_end=-1, domain='user_'):
    domain_key = domain + str(key)
    try:
        return redis.zrange(domain_key, scope_start, scope_end)
    except:
        logger.error('Couldnt zget key %')


def redis_remove(key, item, domain='user_'):
    domain_key = domain + str(key)
    try:
        return redis.zrem(domain_key, item[0])
    except:
        logger.error('Couldnt pop the element from redis')


def redis_zcount(key, scope_start=0, scope_end=-1, domain='user_'):
    domain_key = domain + str(key)
    try:
        ''' Also redis.zcount can be used if scope definition needed  '''
        # return redis.zcount(domain_key, scope_start, scope_end)
        elems = redis.zcard(domain_key)
        return elems
    except:
        logger.error('Couldnt count the sorted set elements')


def redis_get_user_pins(user_id, offset=0, limit=-1, return_count=False):
    pins_redis = redis_zget(user_id, offset, limit)
    pins_len = len(pins_redis)
    pins = list()
    for pin in pins_redis:
        pin_temp = redis_get(pin)
        eval_tmp = eval(pin_temp)
        store_tmp = pin_utils.dotdict(eval_tmp)
        pins.append(store_tmp)
    if return_count == True:
        pins.append(pins_len)
    return pins


def redis_get_connection():
    global redis
    return redis


def redis_setname(name):
    redis = redis_get_connection()
    try:
        redis.client_setname(name)
    except Exception, e:
        logger.error('Couldnt set redis client name', e)
        return False
    return True


def redis_create_pipe():
    try:
        return redis.pipeline()
    except:
        logger.error('Couldnt create pipline')


def get_user_quota():
    """
        @TODO user quota should be set somewhere in user admin panel
    """
    return 10

redis = redis_connect()
