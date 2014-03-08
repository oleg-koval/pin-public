import os

try:
    import local_settings
    params = local_settings.params
except Exception:
	params = {
        'dbn': 'postgres',
        'db': 'pin',
        'user': os.environ['DB_USER'],
        'pw': os.environ['DB_PASSWORD'],
        'host': 'mypinnings.com',
        }

FACEBOOK = {'application_id': '1540569082835261',
            'application_secret': os.environ['FACEBOOK_APPLICATION_SECRET'],
            }

TWITTER = {'api_key': 'QNcMlvWvVS2ictFpHW3bQ',
           'api_secret': os.environ['TWITTER_APPLICATION_SECRET'],
           }