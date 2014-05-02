import argparse
import psycopg2
import os.path


def connect_to_db(args):
    conn = psycopg2.connect(database=args.database, user=args.user, password=args.password, host=args.server, port=args.port)
    conn.autocommit = False
    return conn


def fix_users_lists(conn):
    cur = conn.cursor()
    cur.execute('select distinct user_id from boards;')
    users_with_boards = []
    for row in cur:
        users_with_boards.append(row[0])
    cur.close()
    cur = conn.cursor()
    cur.execute('select id from users;')
    for row in cur:
        user_id = row[0]
        if user_id not in users_with_boards:
            add_default_lists(user_id, conn)


def add_default_lists(uid, conn):
    cur = conn.cursor()
    default_list = {'Things to get', 'Food to eat', 'Places to visit'}
    for x in default_list:
        cur.execute("insert into boards(user_id, name, description, public) values (%s, %s, 'Default List', 'f')", (uid, x))
    conn.commit()


def fix_users_without_pins(conn):


if __name__ =='__main__':
    parser = argparse.ArgumentParser(description="Creates the external id for pins.\nFist create the external_id column in pins table")
    parser.add_argument('--server', '-s', help='Server name or IP address (default localhost)', default='localhost')
    parser.add_argument('--port', '-p', help='Server port default(5432)', default='5432')
    parser.add_argument('--database', '-d', help='Database name (defult pin)', default='pin')
    parser.add_argument('--user', '-u', help='Database user', required=True)
    parser.add_argument('--password', '-w', help='Database password', required=True)
    args = parser.parse_args()
    conn = connect_to_db(args)
    fix_users_lists(conn)