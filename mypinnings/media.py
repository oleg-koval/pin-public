import time
import random
import string
import os
import os.path
import urllib

from PIL import Image

from mypinnings import database
from mypinnings.conf import settings


class MediaFileMetadata(object):
    def __init__(self, filename):
        self.id = None
        self.filename = filename
        self.sizes = []

    def insert_into_db(self):
        db = database.get_db()
        string_of_sizes = ','.join('{}x{}'.format(*pair) for pair in self.sizes)
        self.id = db.insert(tablename='photos', filename=self.filename, sizes=string_of_sizes)


class MediaServer(object):
    servers = {}
    active_servers = []
    cache_timestamp = 0

    def __init__(self, id, url, path, active):
        self.id = id
        self.url = url
        self.path = path
        self.active = active


def load_servers():
    reload_servers()


def reload_servers():
    new_timestamp = time.time()
    if new_timestamp > MediaServer.cache_timestamp + settings.SERVER_LIST_CACHE_EXPIRATION:
        MediaServer.servers = {}
        MediaServer.active_servers = []
        db = database.get_db()
        results = db.where(table='media_servers', order='id')
        for row in results:
            server = MediaServer(**row)
            MediaServer.servers[server.id] = server
            if server.active:
                MediaServer.active_servers.append(server)


def store_image_from_url(url, widths=[]):
    downloaded_filename, headers = urllib.urlretrieve(url)
    return store_image_from_filename(downloaded_filename, widths)


def store_image_from_filename(original_filename, widths=[]):
    reload_servers()
    base_path, base_filename = _get_base_file_path_and_name()
    original_image = Image.open(original_filename)
    image_filename = base_filename + '.png'
    original_image.save(os.path.join(base_path, image_filename))
    os.unlink(original_filename)
    media_file = MediaFileMetadata(image_filename)
    original_size_image = Image.open(os.path.join(base_path, image_filename))
    media_file.sizes.append(original_size_image.size)
    if widths:
        original_width, original_height = original_size_image.size
        for width in widths:
            ratio = float(width) / float(original_width)
            height = int(original_height * ratio)
            # open the original size image
            image_to_resize = Image.open(os.path.join(base_path, image_filename))
            image_to_resize.thumbnail((width, height), Image.ANTIALIAS)
            filename = base_filename + '_' + str(width) + 'x' + str(height) + '.png'
            image_to_resize.save(os.path.join(base_path, filename))
            media_file.sizes.append((width, height))
    media_file.insert_into_db()
    return media_file


def _get_base_file_path_and_name():
    server = random.choice(MediaServer.active_servers)
    path_level_1 = str(random.randrange(999))
    path_level_2 = str(random.randrange(999))
    base_name = str(server.id) + '_' + path_level_1 + '_' + path_level_2 + '_' + _random_name()
    base_path = os.path.join(server.path, path_level_1, path_level_2)
    if not os.path.isdir(base_path):
        os.makedirs(base_path)
    return (base_path, base_name)


_pool = string.ascii_lowercase + string.digits
def _random_name(length=20):
    return ''.join(random.choice(_pool) for _ in range(length))


def get_image_url(image_name, size=None):
    reload_servers()
    parts = image_name.split('_', 3)
    server_id = int(parts[0])
    path = parts[1] + "/" + parts[2]
    server = MediaServer.servers[server_id]

    if size and isinstance(size, (basestring, list, tuple)):
        if isinstance(size, basestring):
            if 'x' in size:
                width, height = (int(v) for v in size.split('x'))
            if ',' in size:
                width, height = (int(v) for v in size.split(','))
        else:
            width, height = size
        size_sufix = '_{width}x{height}'.format(width=width, height=height)
        name, ext = os.path.splitext(image_name)
        if not name.endswith(size_sufix):
            name += size_sufix + ext
            test_path = os.path.join(server.path, path, name)
            if os.path.exists(test_path):
                image_name = name

    url = server.url.format(path=path, media=image_name)
    return url


