import web

from mypinnings.settings import *


db = None

def connect_db():
    global db
    if db is not None:
        return db
    db = web.database(**params)
    return db

def dbget(table, row_id):
    global db
    rows = db.select(table, where='id = $id', vars={'id': row_id})
    return rows[0] if rows else None

def get_db():
    global db
    return db