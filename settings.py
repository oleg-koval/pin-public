# -*- coding: utf8 -*-
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

GOOGLE = {'client_id': '985703411904-602sd2jgsl6v5ad8k3fb6tanc46a0v88.apps.googleusercontent.com',
          'client_secret': '5yH_l93eepm9c_NUws8zrQoY',
          }

LANGUAGES = (('en', 'English'),
             ('fr', 'Français'),
             ('es', 'Español'),
             )