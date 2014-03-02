'''
Loads the settings from the settings module, but allows to have
a local_settings module for local development.

You showld impor from here (prefered):
from mypinnings import settings
or:
from mypinnings.settings improt *
'''
try:
    from local_settings import *
except ImportError:
    from settings import *
    pass