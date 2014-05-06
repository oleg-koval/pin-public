import argparse
import boto
import psycopg2
import urllib
import os

from PIL import Image


def connect_to_db(args):
    conn = psycopg2.connect(database=args.database, user=args.user, password=args.password, host=args.server, port=args.port)
    conn.autocommit = False
    return conn


def update_image_size(db):
    cursor = db.cursor()
    cursor.execute('select id, image_url, image_202_url, image_212_url from pins where image_width is null')
    number_of_uploaded_images = 0
    for i, row in enumerate(cursor):
        print('procesing: {}'.format(row[0]))
        print('retrieving: {}'.format(row[1]))
        filename, _ = urllib.urlretrieve(row[1])
        image = Image.open(filename)
        image_size = image.size
        os.unlink(filename)
        print('retrieving: {}'.format(row[2]))
        filename, _ = urllib.urlretrieve(row[2])
        image = Image.open(filename)
        image_202_size = image.size
        os.unlink(filename)
        print('retrieving: {}'.format(row[3]))
        filename, _ = urllib.urlretrieve(row[3])
        image = Image.open(filename)
        image_212_size = image.size
        os.unlink(filename)
        cursor = db.cursor()
        print('update into DB:{}'.format(row[0]))
        cursor.execute('update pins set image_width=%(width)s, image_height=%(height)s, image_202_height=%(height_202)s, image_212_height=%(height_212)s where id=%(id)s',
                       {'id': row[0],
                        'width': image_size[0],
                        'height': image_size[1],
                        'height_202': image_202_size[1],
                        'height_212': image_212_size[1],
                        })
        if i % 20 == 0:
            db.commit()
            print("{} images processed so far.".format(i))
        number_of_uploaded_images += 1
    return number_of_uploaded_images


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Creates the external id for pins.\nFist create the external_id column in pins table")
    parser.add_argument('--server', '-s', help='Server name or IP address (default localhost)', default='localhost')
    parser.add_argument('--port', '-p', help='Server port default(5432)', default='5432')
    parser.add_argument('--database', '-d', help='Database name (defult pin)', default='pin')
    parser.add_argument('--user', '-u', help='Database user', required=True)
    parser.add_argument('--password', '-w', help='Database password', required=True)
    args = parser.parse_args()
    db = connect_to_db(args)
    try:
        number_of_updated_images = update_image_size(db)
        print('Finished uploading {} images'.format(number_of_updated_images))
    finally:
        db.close()
