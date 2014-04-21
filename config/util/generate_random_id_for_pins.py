import argparse
import random

import psycopg2


DIGITS = '1234567890'
LETTERS = 'abcdefghijklmnopqrstuvwxwzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def connect_to_db(args):
    conn = psycopg2.connect(database=args.database, user=args.user, password=args.password, host=args.server, port=args.port)
    conn.autocommit = False
    return conn


def update_pins(conn):
    cur = conn.cursor()
    cur.execute('select id from pins where external_id is null;')
    rows = cur.fetchall()
    for i, row in enumerate(rows):
        id = row[0]
        external_id = _new_external_id()
        while _already_exists(external_id, conn):
            external_id = _new_external_id()
        cur.execute('update pins set external_id=%s where id=%s;', (external_id, id))
        if i % 500 == 0:
            conn.commit()
            print('Processing {} rows...'.format(i))
    conn.commit()
    print('Finished {} rows.'.format(i))
        
        
def _new_external_id():
    digits = random.sample(DIGITS, 6)
    letters = random.sample(LETTERS, 3)
    digits_and_letters = []
    digits_and_letters.extend(digits)
    digits_and_letters.extend(letters)
    random.shuffle(digits_and_letters)
    return ''.join(digits_and_letters)


def _already_exists(external_id, conn):
    cur = conn.cursor()
    cur.execute('select 1 from pins where external_id=%s', (external_id,))
    for row in cur:
        cur.close()
        return True
    cur.close()
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Creates the external id for pins.\nFist create the external_id column in pins table")
    parser.add_argument('--server', '-s', help='Server name or IP address (default localhost)', default='localhost')
    parser.add_argument('--port', '-p', help='Server port default(5432)', default='5432')
    parser.add_argument('--database', '-d', help='Database name (defult pin)', default='pin')
    parser.add_argument('--user', '-u', help='Database user', required=True)
    parser.add_argument('--password', '-w', help='Database password', required=True)
    args = parser.parse_args()
    db = connect_to_db(args)
    update_pins(db)
    print('Now alter the pins table and create the index.')