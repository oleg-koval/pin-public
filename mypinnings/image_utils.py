import os.path
import logging

from PIL import Image


logger = logging.getLogger('mypinnings.image_utils')


def create_thumbnail_212px_for_pin_id(pin_id):
    image_thumb_filename = 'static/tmp/pinthumb_212_{}.png'.format(pin_id)
    if not os.path.exists(image_thumb_filename):
        try:
            original_image_filename = 'static/tmp/{}.png'.format(pin_id)
            original_image = Image.open(original_image_filename)
            width, height = original_image.size
            ratio = 212 / float(width)
            width = 212
            height *= ratio
            original_image.thumbnail((width, height), Image.ANTIALIAS)
            original_image.save(image_thumb_filename)
        except:
            logger.error('could not generate thumbnail for: {}'.format(original_image_filename), exc_info=True)
            return False
    return True
        
        
def create_thumbnail_212px_for_pin(pin):
    return create_thumbnail_212px_for_pin_id(pin.id)