import os

params = {
    'dbn': 'postgres',
    'db': 'dbname',
    'user': 'yourname',
    'pw': '1',
    'host': 'localhost',
    }

PRJ_DIR = os.path.realpath(os.path.dirname(__file__))
MEDIA_PATH = os.path.join(PRJ_DIR, "media")
