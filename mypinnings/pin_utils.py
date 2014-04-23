import random
import logging

from mypinnings import database
from mypinnings import media


logger = logging.getLogger('mypinnings.pin_utils')


DIGITS_AND_LETTERS = 'abcdefghijklmnopqrstuvwxwzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'


class PinError(Exception):
    pass


def create_pin(db, user_id, title, description, link, tags, price, product_url,
                   price_range, image_filename):
    try:
        _validate_pin_required_data(user_id, title, description, link, tags, price, product_url,
                   price_range, image_filename)
        images_dict = media.store_image_from_filename(db, image_filename, widths=(202, 212))
        if not price:
            price = None
        external_id = generate_external_id()
        pin_id = db.insert(tablename='pins',
                           name=title,
                           description=description,
                           user_id=user_id,
                           link=link,
                           views=1,
                           price=price,
                           image_url=images_dict[0],
                           image_202_url=images_dict[202],
                           image_212_url=images_dict[212],
                           product_url=product_url,
                           price_range=price_range,
                           external_id=external_id)
        if tags:
            tags = _remove_hash_symbol_from_tags(tags)
            db.insert(tablename='tags', pin_id=pin_id, tags=tags)
        pin = db.where(table='pins', id=pin_id)[0]
        return pin
    except:
        logger.error('Cannot insert a pin in the DB', exc_info=True)
        raise


def _validate_pin_required_data(user_id, title, description, link, tags, price, product_url,
                   price_range, image_filename):
    if not user_id:
        raise PinError('Must provide the user.id to create a pin')
    if not link and not product_url:
        raise PinError('Must provide a source link or a product link to create a pin.')
    if not tags:
        raise PinError('Must provide tags to create a pin')
    if not price_range:
        raise PinError('Must provide a price range ($, $$, $$$, $$$$, $$$$+) to create a pin')
    if not image_filename:
        raise PinError('Must provide the file of the image to create a pin')


def generate_external_id():
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


def _remove_hash_symbol_from_tags(value):
    if value:
        separated = value.split(' ')
        fixed = []
        for v in separated:
            new_v = v.replace('#', '')
            fixed.append(new_v)
        return ' '.join(fixed)
    else:
        return value