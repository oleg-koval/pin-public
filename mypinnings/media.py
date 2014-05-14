import random
import os
import os.path

import boto.s3.connection
import boto.s3.key
from PIL import Image

from Queue import Queue
from threading import Thread
import multiprocessing
import threadpool
import concurrent.futures
import shutil
import os

NAME_CHARACTERS = '1234567890' * 10
DIRECTORY_CHARACTERS = 'qwertyuiopasdfghjklzxcvbnm01234657901234657980123465789'
NUM_THREADS = 50

def store_image_from_filename(db, filename, widths=[]):
    '''
    Saves the image from the filename into one of the active media servers.

    db - A connection to the data base.
    filename - A valid filename (string) or list of filenames (list of strings). 
	Filename(s) should be a full path or relative, that the application can actually read
    widths - A list of integers with the widths of the images you would like
        to be saved in the media server. Like [220, 40]

    This saves one image (if width is empty or None) or many images (if width is a list
    of integers). The images are saved renamed, so you don't need to generate random
    names or unique names.

    Returns :
	1) For one image - a dict(int: string) the keys are the widths of the images, the values
    	are the actual URL to serve the image. To obtain the URL for the image in the
    	original width (and size), look for the key 0 (zero)
	2) For many images - a dict of dicts(int:string) the keys are names of the images with extension, 
	the values are dicts which keys are width value specified as input parameter and values are URL for the image
	To obtain the URL for the image in the original width (and size), look for the key 0 (zero)
	To obtain the URL for the image in the specified width as an input parameter, look for the specified width

	Ad.1.
	    >>> dict_of_images = store_image_from_filename(db, '/tmp/myfile.jpg', widths=(212, 202))
	    >>> dict_of_images[0] # this returns the URL for the image with the original width (and size).
	    'http://http://32.media.mypinnings.com/asd/qwe/zxc/asdqwezxcasdfasdfasdf.jpg'
	    >>> dict_of_images[212] # returns the URL for the image scaled to a width of 212
	    'http://http://32.media.mypinnings.com/asd/qwe/zxc/asdqwezxcasdfasdfasdf_212.jpg'
	    >>> dict_of_images[212] # returns the URL for the image scaled to a width of 202
	    'http://http://32.media.mypinnings.com/asd/qwe/zxc/asdqwezxcasdfasdfasdf_202.jpg'
	Ad.2.
	    >>> filepath0 = '/tmp/tux0.png'
	    >>> filepath1 = '/tmp/tux1.png'
	    >>> fileslist = []
		fileslist.append(filepath0)
		fileslist.append(filepath1)
	    >>> dict_of_dicts_of_images = store_image_from_filename(db, fileslist, widths=(212, 202))
	    >>> {'tux0.png': {0: {'url': 'http://32.media.mypinnings.com/98u/196/46a/03419071145676531021621434279195.png'}, 
		202: {'url': 'http://32.media.mypinnings.com/327/v35/4ej/03419071145676531021621434279195_202.png', 'width': 202, 'height': 246}, 
		212: {'url': 'http://32.media.mypinnings.com/7lr/2o7/ema/03419071145676531021621434279195_212.png', 'width': 212, 'height': 258}, 
		222: {'url': 'http://32.media.mypinnings.com/98u/196/46a/03419071145676531021621434279195.png', 'width': 222, 'height': 271}}, 
		'tux1.png': {0: {'url': 'http://32.media.mypinnings.com/c1x/zqt/5ku/08492460583817663485035255370941.png'}, 
		202: {'url': 'http://32.media.mypinnings.com/96f/3nj/c1m/08492460583817663485035255370941_202.png', 'width': 202, 'height': 246}, 
		212: {'url': 'http://32.media.mypinnings.com/j2y/p5y/q56/08492460583817663485035255370941_212.png', 'width': 212, 'height': 258}, 
		222: {'url': 'http://32.media.mypinnings.com/c1x/zqt/5ku/08492460583817663485035255370941.png', 'width': 222, 'height': 271}}}

    The image(s) is(are) saved in its original size, plus the sizes of the widths you
    specify. The aspect ratio is preserved when scaling. The image is renamed,
    so use the returned dictionary to obtain the filenames for each size.
    '''

    images_queue = Queue()
    images_by_width = dict()
    images_by_width_list = dict()

    def processstoringimages(queue_element, queue_type):
	while True:
	    server = _get_an_active_server(db)
	    path, _, original_extension = _split_path_for(queue_element)
	    new_filename = _generate_a_new_filename(server, original_extension)
	    new_filename = os.path.join(path, new_filename)
	    os.rename(queue_element, new_filename)
	    image_url = _upload_file_to_bucket(server, new_filename)
	    original_image_width, original_image_height = _get_image_size(new_filename)

	    if queue_type == 1:
		images_by_width[original_image_width] = {'url': image_url,
                                             'width': original_image_width,
                                             'height': original_image_height}
		images_by_width[0] = {'url': image_url,
                         'width': original_image_width,
                         'height': original_image_height}
		if widths:
		   for width in widths:
		       scaled_image_filename, width, height = _scale_image(new_filename, width)
		       scaled_image_url = _upload_file_to_bucket(server, scaled_image_filename)
		       images_by_width[width] = {'url': scaled_image_url,
                                     'width': width,
                                     'height': height}
		       os.unlink(scaled_image_filename)
		os.unlink(new_filename)
		queue_element.task_done()
	    elif queue_type == 2:
		if widths:
		   smalldict = dict()
		   smalldict[0] = {'url': image_url}
		   smalldict[original_image_width] = {'url': image_url,
                                     'width': original_image_width,
                                     'height': original_image_height}

		   for width in widths:
		       scaled_image_filename, width, height = _scale_image(new_filename, width)
		       scaled_image_url = _upload_file_to_bucket(server, scaled_image_filename)
		       smalldict[width] = {'url': scaled_image_url,
                                     'width': width,
                                     'height': height}
		       os.unlink(scaled_image_filename)
		   images_by_width_list[_+original_extension] = smalldict
		os.unlink(new_filename)
	    	queue_element.task_done()

    filetype = None
    if isinstance(filename, str):
	images_queue.put(filename)
	filetype = 1
    elif isinstance(filename, list):
	for files in range(0, len(filename)):
	    images_queue.put(filename[files])
	    filetype = 2
    else:
	print "Unsupported filename data type"
	return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
	for num in range(0, images_queue.qsize()):
	    executor.submit(processstoringimages, images_queue.get(), filetype)

    with images_queue.mutex:
	images_queue.queue.clear()

    if (filetype == 1):
	return images_by_width
    elif (filetype == 2):
	return images_by_width_list
    else:
	return None

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
    #connection = boto.s3.connection.S3Connection()
    connection = boto.connect_s3(
	aws_access_key_id = _get_aws_access_key_id(),
	aws_secret_access_key = _get_aws_secret_access_key())
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
    path1 = ''.join(random.sample(DIRECTORY_CHARACTERS, 3))
    path2 = ''.join(random.sample(DIRECTORY_CHARACTERS, 3))
    path3 = ''.join(random.sample(DIRECTORY_CHARACTERS, 3))
    pathname = os.path.join(path1, path2, path3, filename)
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
    #connection = boto.s3.connection.S3Connection()
    connection = boto.connect_s3(
	aws_access_key_id = _get_aws_access_key_id(),
	aws_secret_access_key = _get_aws_secret_access_key())
    bucket = connection.get_bucket(bucket_name)
    key = boto.s3.key.Key(bucket)
    key.key = pathname
    key.set_contents_from_filename(filename)
    key.set_acl('public-read')
    connection.close()
    return '{}/{}'.format(server.url, pathname)
    
    
def _get_image_size(filename):
    '''
    Returns the width of the image contained in the file.
    '''
    image = Image.open(filename)
    return image.size
    

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
    return (scaled_image_filename, width, height)


def _get_aws_access_key_id():
    '''
    Returns AWS_ACCESS_KEY_ID from environment variables
    '''
    return os.environ.get('AWS_ACCESS_KEY_ID')


def _get_aws_secret_access_key():
    '''
    Returns AWS_SECRET_ACCESS_KEY from environment variables
    '''
    return os.environ.get('AWS_SECRET_ACCESS_KEY')
