import os

try:
	params = {
        'dbn': 'postgres',
        'db': 'pin',
        'user': os.environ['DB_USER'],
        'pw': os.environ['DB_PASSWORD'],
        'host': 'mypinnings.com',
        }
except Exception:
	pass