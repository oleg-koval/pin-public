'''
Centrally manages the media upload (images).

You use the API to upload images like this:

from mypinnings import media

if you have an URL to grab the image:

>>> image_metadata = media.store_image_from_url(url=image_url)

if you have an URL and like the image stored in many sizes (dictated by the image width)
this will save 3 images: oner with the original size, two rescaled to a width of 200 and 40

>>> image_metadata = media.store_image_from_url(url=image_url, widths=[220, 40])

you can then use the id, filename and sizes of the file:

>>> print(image_metadata.id)
159
>>> print(image_metadata.filename)
'2_345_324_34jlksh34hkhskj54kj3hwk43h.png'
>>> print(image_metadata.sizes)
[(250,250), (220,220), (40,40)]

Note that we add one more size to the sizes, that is the original size of the image.

You can the user the image_metadata.id to relate this image to content like: albums, pins,
users pic, etc.

After that, you will need to recover the image and construct the image URL to put into the
templates. You should query the photos table to get the image by id; remember that is your
responsability to store the image_metadata.id in the database. You should get at least the
filename from the photos table, but you can get also the sizes and user that to see if the
image have a size that suits your needs. You don't user the id to get the URL of the image
only the filename

You request the image url with get_image_url() like this:

>>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png')
>>> print(url)
'http://mypinnings.com/static/media/345/3247/2_345_324_34jlksh34hkhskj54kj3hwk43h.png'

to grab the 40x40 image size, you can use:

>>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png', size='40x40)
>>> print(url)
'http://mypinnings.com/static/media/345/3247/2_345_324_34jlksh34hkhskj54kj3hwk43h_40x40.png'

Note that the following 3 calls are all equivalent, because the size can accept a tuple, or
a string in the format 40x40 or 40,40:

>>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png', size='40x40)
>>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png', size='40,40)
>>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png', size=(40, 40))
'''
import time
import random
import string
import os
import os.path
import urllib

from PIL import Image

from mypinnings import database


# number of seconds to reload the server list
SERVER_LIST_CACHE_EXPIRATION = 500


class MediaFileMetadata(object):
    '''
    Represents a media file (like an image) uploaded to the server.

    Attributes:
    * id contains the id of the media in the DB (in table photos)
    * filename is the complete file name.
    * sizes is a list of tuples with image sizes saved: [(250,250), (120,120), (40,40)]

    The sizes is saved in the photos table as a string of the form: 250x250,120x120,40x40
    To obtain the URL that serves the file to the world, use the function get_image_url()
    '''
    def __init__(self, filename):
        '''
        Creates with a filename, the id is None and the sizes is empty list.

        You can add sizes after creation like:

        >>> mfm = MediaFileMetadata('asdf.png')
        >>> mfm.sizes.append((30, 40))

        Only append 2-tuples to the sizes list.
        '''
        self.id = None
        self.filename = filename
        self.sizes = []

    def insert_into_db(self):
        '''
        Saves the image to the photos table, including the sizes.

        We don't expect you to save images outside of this module.

        The sizes are saved in the sizes field as a string in the format: 250x250,120x120,40x40
        After saving, you get the id

        >>> mfm = MediaFileMetadata('asdf.png')
        >>> print(mfm.id)
        None
        >>> mfm.save()
        >>> print(mfm.id)
        5487
        '''
        db = database.get_db()
        string_of_sizes = ','.join('{}x{}'.format(*pair) for pair in self.sizes)
        self.id = db.insert(tablename='photos', filename=self.filename, sizes=string_of_sizes)


class MediaServer(object):
    '''
    Reprsents a media server of a pool

    We use the media servers to serve images from different servers and
    have escalability. You are not expected to use this outside of this
    module.

    The servers are stores in the media_servers table. They are reloaded from
    the database from time to time according to SERVER_LIST_CACHE_EXPIRATION.

    From the server pool, there are active servers, that are servers currently
    accepting file uploads. The other unactive servers only serve images
    already uploaded to them.
    '''
    # a dict with the servers, by server id
    servers = {}
    # list of active servers, servers that we can upload images to
    active_servers = []
    # timestamp of last pool refresh
    cache_timestamp = 0

    def __init__(self, id, url, path, active):
        self.id = id
        self.url = url
        self.path = path
        self.active = active


def reload_servers():
    '''
    Perform a re-load of the media server's list from the database
    '''
    new_timestamp = time.time()
    if new_timestamp > MediaServer.cache_timestamp + SERVER_LIST_CACHE_EXPIRATION:
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
    '''
    Saves the image from the URL into one of the active media servers.

    url - A valid URL for an image
    widths - A list of integer with the widths of the images you would like
        to be saved in the media server. Like [220, 40]

    Returns a MediaFileMetadata with the id, filename for the stored image,
        and the sizes of other rescaled images according to 'widths' parameter.

    The image is saved in it original size, plus the sizes of the widths you
    specify. The aspect ratio is preserved when scaling. The image is renamed,
    so use the returned metadata to obtains the filename.
    '''
    downloaded_filename, headers = urllib.urlretrieve(url)
    return store_image_from_filename(downloaded_filename, widths)


def store_image_from_filename(original_filename, widths=[]):
    '''
    Saves the image from the filename into one of the active media servers.

    filename - A valid filename, full path or relative, that the application
        can actually read
    widths - A list of integer with the widths of the images you would like
        to be saved in the media server. Like [220, 40]

    Returns a MediaFileMetadata with the id, filename for the stored image,
        and the sizes of other rescaled images according to 'widths' parameter.

    The image is saved in it original size, plus the sizes of the widths you
    specify. The aspect ratio is preserved when scaling. The image is renamed,
    so use the returned metadata to obtains the filename.
    '''
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
    '''
    Randomly selects a server and a base filename for the file
    '''
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
    '''
    Generates random names of the specified length.
    '''
    return ''.join(random.choice(_pool) for _ in range(length))


def get_image_url(image_name, size=None):
    '''
    Returns the URL of an image given the image_name.

    The image names are stored in the photos table, so you can obtain the
    images associated to your content along with the available image sizes.

    >>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png')
    >>> print(url)
    'http://mypinnings.com/static/media/345/3247/2_345_324_34jlksh34hkhskj54kj3hwk43h.png'

    to grab the 40x40 image size, you can use:

    >>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png', size='40x40)
    >>> print(url)
    'http://mypinnings.com/static/media/345/3247/2_345_324_34jlksh34hkhskj54kj3hwk43h_40x40.png'

    Note that the following 3 calls are all equivalent, because the size can accept a tuple, or
    a string in the format 40x40 or 40,40:

    >>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png', size='40x40)
    >>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png', size='40,40)
    >>> url = get_image_url(image_name='2_345_324_34jlksh34hkhskj54kj3hwk43h.png', size=(40, 40))
    '''
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


