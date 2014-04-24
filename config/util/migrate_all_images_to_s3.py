import argparse
import os.path
import random

import psycopg2
import boto.s3.connection
from PIL import Image


NAME_CHARACTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-._'
BUCKET_NAME = '32.media.mypinnings.com'
SERVER_URL = 'http://32.media.mypinnings.com'


def connect_to_db(args):
    conn = psycopg2.connect(database=args.database, user=args.user, password=args.password, host=args.server, port=args.port)
    conn.autocommit = False
    return conn


def connect_to_s3(args):
    if args.s3key and args.s3secret:
        s3connection = boto.s3.connection.S3Connection(args.s3key, args.s3secret)
    else:
        s3connection = boto.s3.connection.S3Connection()
    return s3connection


def move_pin_images_to_s3(db, s3conn):
    cursor = db.cursor()
    cursor.execute('select id from pins where image_202_url is null')
    number_of_uploaded_images = 0
    for i, row in enumerate(cursor):
        try:
            if i % 20 == 0:
                print('{} images uploaded so far.'.format(i))
            pin_id = row[0]
            original_image_filename = os.path.join('..', '..', 'static', 'tmp', '{}.png'.format(pin_id))
            original_image_202_filename = os.path.join('..', '..', 'static', 'tmp', 'pinthumb{}.png'.format(pin_id))
            original_image_212_filename = os.path.join('..', '..', 'static', 'tmp', 'pinthumb_212_{}.png'.format(pin_id))
            new_name, new_name_202, new_name_212 = generate_new_names(s3conn)
            if os.path.exists(original_image_filename):
                image_url = _upload_file_to_bucket(s3conn, original_image_filename, new_name)
            else:
                print('This pin does not have image: {}'.format(pin_id))
                continue
            if os.path.exists(original_image_202_filename):
                image_url_202 = _upload_file_to_bucket(s3conn, original_image_202_filename, new_name_202)
            else:
                scale_image(original_image_filename, original_image_202_filename, 202)
                image_url_202 = _upload_file_to_bucket(s3conn, original_image_202_filename, new_name_202)
            if os.path.exists(original_image_212_filename):
                image_url_212 = _upload_file_to_bucket(s3conn, original_image_212_filename, new_name_212)
            else:
                scale_image(original_image_filename, original_image_212_filename, 212)
                image_url_212 = _upload_file_to_bucket(s3conn, original_image_212_filename, new_name_212)
            update_pin_images(db, pin_id, image_url, image_url_202, image_url_212)
            db.commit()
            number_of_uploaded_images += 1
        except Exception as e:
            db.rollback()
            print('Failed to migrate image for pin: {}: {}'.format(pin_id, e))
    return number_of_uploaded_images
        
        
def generate_new_names(s3conn):
    name = _generate_a_new_filename(s3conn)
    filename = '{}.png'.format(name)
    filename_202 = '{}_202.png'.format(name)
    filename_212 = '{}_212.png'.format(name)
    return (filename, filename_202, filename_212)


def _generate_a_new_filename(s3conn):
    name = _new_random_name(size=32)
    filename = '{}.png'.format(name)
    while _file_already_exists_in_server(s3conn, filename):
        name = _new_random_name(size=32)
        filename = '{}.png'.format(name)
    return name


def _new_random_name(size=32):
    sample = random.sample(NAME_CHARACTERS, size)
    name = ''.join(sample)
    return name

def _file_already_exists_in_server(connection, filename):
    pathname = _generate_path_name_for(filename)
    bucket = connection.get_bucket(BUCKET_NAME)
    key = bucket.get_key(pathname)
    return key != None


def _generate_path_name_for(filename):
    pathname = os.path.join(filename[0:3], filename[3:6], filename[6:9], filename)
    return pathname


def _upload_file_to_bucket(connection, filename, new_name):
    pathname = _generate_path_name_for(new_name)
    bucket = connection.get_bucket(BUCKET_NAME)
    key = boto.s3.key.Key(bucket)
    key.key = pathname
    key.set_contents_from_filename(filename)
    key.set_acl('public-read')
    return '{}/{}'.format(SERVER_URL, pathname)
    

def scale_image(filename, scaled_image_filename, width):
    image = Image.open(filename)
    original_width, original_height = image.size
    scale_ratio = float(width) / float(original_width)
    height = int(original_height * scale_ratio)
    scaled_size = (width, height)
    image.thumbnail(scaled_size, Image.ANTIALIAS)
    image.save(scaled_image_filename)
    return scaled_image_filename


def update_pin_images(db, pin_id, image_url, image_202_url, image_212_url):
    cursor = db.cursor()
    update_statement = '''update pins set image_url=%(image_url)s, image_202_url=%(image_202_url)s,
                            image_212_url=%(image_212_url)s where id=%(pin_id)s'''
    data = {'pin_id': pin_id,
            'image_url': image_url,
            'image_202_url': image_202_url,
            'image_212_url': image_212_url,
            }
    cursor.execute(update_statement, data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Creates the external id for pins.\nFist create the external_id column in pins table")
    parser.add_argument('--server', '-s', help='Server name or IP address (default localhost)', default='localhost')
    parser.add_argument('--port', '-p', help='Server port default(5432)', default='5432')
    parser.add_argument('--database', '-d', help='Database name (defult pin)', default='pin')
    parser.add_argument('--user', '-u', help='Database user', required=True)
    parser.add_argument('--password', '-w', help='Database password', required=True)
    parser.add_argument('--s3key', '-k', help='S3 API Key (taken from AWS_ACCESS_KEY_ID environment variable if empty)')
    parser.add_argument('--s3secret', '-sec', help='S3 API Secret (taken from AWS_SECRET_ACCESS_KEY environment variable if empty)')
    args = parser.parse_args()
    db = connect_to_db(args)
    s3conn = connect_to_s3(args)
    try:
        number_of_uploaded_images = move_pin_images_to_s3(db, s3conn)
        print('Finished uploading {} images'.format(number_of_uploaded_images))
    finally:
        s3conn.close()
        db.close()
