import web


db = None


#try to import local settings
# Localhost settings
try:
    from local_settings import *
except ImportError:
    from settings import *
    pass


def connect_db():
    global db
    if db is not None:
        return db
    db = web.database(**params)
    return db
