import argparse
import psycopg2
import os.path


def connect_to_db(args):
    conn = psycopg2.connect(database=args.database, user=args.user, password=args.password, host=args.server, port=args.port)
    conn.autocommit = False
    return conn


def fix_pins(conn):
    try:
        cur = conn.cursor()
        cur.execute('select id from pins;')
        pins_to_delete = []
        pins_without_category = 0
        for row in cur:
            id = row[0]
            if does_not_have_image(id):
                pins_to_delete.append(id)
            elif does_not_have_category(conn, id):
                add_to_recomendations_category(conn, id)
                pins_without_category += 1
        if pins_to_delete:
            delete_pins(conn, pins_to_delete)
        conn.commit()
        print('Pins added to recomendations category: {}'.format(pins_without_category))
        print('Pins deleted because do not have image: {}'.format(len(pins_to_delete)))
    except:
        conn.rollback()
        print('An error ocurred, no changes saved to the database')
        raise
    
    
def does_not_have_image(id):
    image_filename = '{}.png'.format(id)
    image_path = os.path.join('..', '..', 'static', 'tmp', image_filename)
    return not os.path.exists(image_path)


def does_not_have_category(conn, id):
    cur = conn.cursor()
    cur.execute('select category_id from pins_categories where pin_id = {}'.format(id))
    return len(cur.fetchall()) == 0


def add_to_recomendations_category(conn, id):
    cur = conn.cursor()
    cur.execute('insert into pins_categories(pin_id, category_id) values ({}, 1)'.format(id))
    
    
def delete_pins(conn, list_of_pin_ids):
    string_of_pin_ids = ','.join((str(x) for x in list_of_pin_ids))
    cur = conn.cursor()
    cur.execute('delete from pins_categories where pin_id in ({})'.format(string_of_pin_ids))
    cur.execute('delete from comments where pin_id in ({})'.format(string_of_pin_ids))
    cur.execute('delete from cool_pins where pin_id in ({})'.format(string_of_pin_ids))
    cur.execute('delete from likes where pin_id in ({})'.format(string_of_pin_ids))
    cur.execute('delete from ratings where pin_id in ({})'.format(string_of_pin_ids))
    cur.execute('delete from tags where pin_id in ({})'.format(string_of_pin_ids))
    cur.execute('delete from pins where id in ({})'.format(string_of_pin_ids))


if __name__ =='__main__':
    parser = argparse.ArgumentParser(description="Creates the external id for pins.\nFist create the external_id column in pins table")
    parser.add_argument('--server', '-s', help='Server name or IP address (default localhost)', default='localhost')
    parser.add_argument('--port', '-p', help='Server port default(5432)', default='5432')
    parser.add_argument('--database', '-d', help='Database name (defult pin)', default='pin')
    parser.add_argument('--user', '-u', help='Database user', required=True)
    parser.add_argument('--password', '-w', help='Database password', required=True)
    args = parser.parse_args()
    conn = connect_to_db(args)
    fix_pins(conn)