import random
import os
import os.path

import boto.s3.connection
import boto.s3.key
from PIL import Image


NAME_CHARACTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-._'


def store_image_from_filename(db, filename, widths=[]):
    '''
    Saves the image from the filename into one of the active media servers.

    db - A connection to the data base.
    filename - A valid filename, full path or relative, that the application
        can actually read
    widths - A list of integers with the widths of the images you would like
        to be saved in the media server. Like [220, 40]

    This saves one image (if width is empty or None) or many images (if width is a list
    of integers).

    Returns a dict(int: string) the keys are the widths of the images, the values
    are the actual URL to serve the image. To obtain the URL for the image in the
    original width (and size), look for the key 0 (zero):
    
    >>> dict_of_images = store_image_from_filename(db, '/tmp/myfile.jpg', widths=(212, 202))
    >>> dict_of_images[0] # this returns the URL for the image with the original width (and size).
    'http://http://32.media.mypinnings.com/asd/qwe/zxc/asdqwezxcasdfasdfasdf.jpg'
    >>> dict_of_images[212] # returns the URL for the image scaled to a width of 212
    'http://http://32.media.mypinnings.com/asd/qwe/zxc/asdqwezxcasdfasdfasdf_212.jpg'
    >>> dict_of_images[212] # returns the URL for the image scaled to a width of 202
    'http://http://32.media.mypinnings.com/asd/qwe/zxc/asdqwezxcasdfasdfasdf_202.jpg'

    The image is saved in its original size, plus the sizes of the widths you
    specify. The aspect ratio is preserved when scaling. The image is renamed,
    so use the returned dictionary to obtain the filenames for each size.
    '''
    server = _get_an_active_server(db)
    images_by_width = dict()
    path, _, original_extension = _split_path_for(filename)
    new_filename = _generate_a_new_filename(server, original_extension)
    new_filename = os.path.join(path, new_filename)
    os.rename(filename, new_filename)
    image_url = _upload_file_to_bucket(server, new_filename)
    original_image_width = _get_image_width(new_filename)
    images_by_width[original_image_width] = image_url
    images_by_width[0] = image_url
    if widths:
        for width in widths:
            scaled_image_filename = _scale_image(new_filename, width)
            scaled_image_url = _upload_file_to_bucket(server, scaled_image_filename)
            images_by_width[width] = scaled_image_url
            # once uploaded to the media server, this file is no longer used
            os.unlink(scaled_image_filename)
    # once uploaded to the media server and scaled to the widths, this file is no longer used
    os.unlink(new_filename)
    return images_by_width


def _get_an_active_server(db):
    '''
    Returns a media server that is active: accepts file uploads.
    
    Some servers may not be active in order to prevent more file
    uploads to that servers. The term active means here that we can
    use that server to upload files; inactive servers are not used
    to upload new files, but the still can be serving files uploaded
    time ago.
    '''
    results = list(db.where(table='media_servers', active=True))
    return random.choice(results)
        
        
def _split_path_for(filename):
    '''
    Returns a 3-tuple containing: path, filename, extension.
    
    Splits the complete filename and returns a 3-tuple containing:
    - path: the path just before the filename
    - filename: the file name without the path and without the extension
    - extension: the string after the last point .
    
    Example:
    >>>_split_path_for('/tmp/camilo/image.jpg')
    ('/tmp/camilo/', 'image', 'jpg')
    '''
    path, filename_and_extension = os.path.split(filename)
    name, extension = os.path.splitext(filename_and_extension)
    return (path, name, extension)
    

def _generate_a_new_filename(server, file_extension):
    '''
    Returns a new unique filename using the existing extension.
    
    We use the file_extension to be appended to the randomly generated
    name. Also a test is performed in the S3 server to see if the image
    already exists.
    '''
    filename = _new_random_name(size=32)
    filename = '{}{}'.format(filename, file_extension)
    while _file_already_exists_in_server(server, filename):
        filename = _new_random_name(size=32)
        filename = '{}{}'.format(filename, file_extension)
    return filename


def _new_random_name(size=32):
    '''
    Returns a new random name of the provided size.
    '''
    sample = random.sample(NAME_CHARACTERS, size)
    name = ''.join(sample)
    return name

def _file_already_exists_in_server(server, filename):
    '''
    Test if the filename already exists in the  S3 server.
    
    True if exits, false otherwise.
    '''
    pathname = _generate_path_name_for(filename)
    bucket_name = server.path
    connection = boto.s3.connection.S3Connection()
    bucket = connection.get_bucket(bucket_name)
    key = bucket.get_key(pathname)
    connection.close()
    return key != None


def _generate_path_name_for(filename):
    '''
    Returns a path for the URL in the server.
    
    This is a path to put the image into, consisting of 3
    directories. The 3 directories are the of 3 characters each,
    and corresponds to the first characters of the filename.
    
    This is made this way to allow for millions of files in
    filesystems where each directory has a limit in the number
    of files it can allow. S3 does not suffer from this, but other
    filesystems like ext4 does. If later we move the files to a
    different storage, this can save us from a large amount of work.
    '''
    pathname = os.path.join(filename[0:3], filename[3:6], filename[6:9], filename)
    return pathname


def _upload_file_to_bucket(server, filename):
    '''
    Upload the file to the bucket and returns the URL to serve that file.
    
    Using the server, upload filename to a bucket. The bucket
    is in server.path. After that, user server.url to generate
    the URL that will be used to server the image from now on
    and return that URL.
    '''
    _, filename_part = os.path.split(filename)
    pathname = _generate_path_name_for(filename_part)
    bucket_name = server.path
    connection = boto.s3.connection.S3Connection()
    bucket = connection.get_bucket(bucket_name)
    key = boto.s3.key.Key(bucket)
    key.key = pathname
    key.set_contents_from_filename(filename)
    connection.close()
    return '{}/{}'.format(server.url, pathname)
    
    
def _get_image_width(filename):
    '''
    Returns the width of the image contained in the file.
    '''
    image = Image.open(filename)
    width, _ = image.size
    return width
    

def _scale_image(filename, width):
    '''
    Scales the image to a width and returns the new filename for the scaled image.
    
    Using the image in filename as a base, scale to the indicated width,
    then save to a new filename and return the new filename of the sacaled image.
    '''
    path, name, extension = _split_path_for(filename)
    scaled_image_filename = '{}_{}{}'.format(name, width, extension)
    scaled_image_filename = os.path.join(path, scaled_image_filename)
    image = Image.open(filename)
    original_width, original_height = image.size
    scale_ratio = float(width) / float(original_width)
    height = int(original_height * scale_ratio)
    scaled_size = (width, height)
    image.thumbnail(scaled_size, Image.ANTIALIAS)
    image.save(scaled_image_filename)
    return scaled_image_filename
