import argparse
import psycopg2


def connect_to_db(args):
    conn = psycopg2.connect(database=args.database, user=args.user, password=args.password, host=args.server, port=args.port)
    conn.autocommit = False
    return conn


def add_slugs_to_categories(conn):
    cur = conn.cursor()
    cur.execute('select c.id, c.name, c.parent, p.name as parent_name from categories c left join categories p on c.parent=p.id;')
    for row in cur:
        cid = row[0]
        cname = row[1]
        pid = row[2]
        pname = row[3]
        update_slug(cid, cname, pid, pname, conn)
    conn.commit()


def update_slug(cid, cname, pid, pname, conn):
    if pid:
        slug = slugify(pname, None) + '/'
    else:
        slug = ''
    slug = slug + slugify(cname, pname)
    cur = conn.cursor()
    cur.execute('update categories set slug=%s where id=%s;', (slug, cid))


def slugify(name, parent_name):
    if parent_name:
        slug = name.replace(parent_name, '')
    else:
        slug = name
    slug = slug.replace('-', '')
    slug = slug.lower().strip()
    slug = slug.replace(' ', '_')
    slug = slug.replace('(', '_')
    slug = slug.replace(')', '_')
    slug = slug.replace('&', 'and')
    return slug


if __name__ =='__main__':
    parser = argparse.ArgumentParser(description="Creates the external id for pins.\nFist create the external_id column in pins table")
    parser.add_argument('--server', '-s', help='Server name or IP address (default localhost)', default='localhost')
    parser.add_argument('--port', '-p', help='Server port default(5432)', default='5432')
    parser.add_argument('--database', '-d', help='Database name (defult pin)', default='pin')
    parser.add_argument('--user', '-u', help='Database user', required=True)
    parser.add_argument('--password', '-w', help='Database password', required=True)
    args = parser.parse_args()
    conn = connect_to_db(args)
    add_slugs_to_categories(conn)