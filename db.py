import web
import os

db = None

def connect_db():
    global db
    if db is not None:
        return db

    params = {
        'dbn': 'postgres',
        'db': 'pin',
        'user': os.environ['DB_USER'],
        'pw': os.environ['DB_PASSWORD'],
        'host': 'mypinnings.com',
    }
    db = web.database(**params)
    return db
