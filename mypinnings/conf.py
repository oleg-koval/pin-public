'''
Loads the settings from the settings module, but allows to have
a local_settings module for local development.

You showld impor from here (prefered):
from mypinnings import settings
or:
from mypinnings.settings improt *
'''
import imp
import os.path


class Settings():
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        local_settings = os.path.join(base_dir, 'local_settings.py')
        try:
            self.module = imp.load_source('local_settings', local_settings)
        except IOError, ImportError:
            main_settings = os.path.join(base_dir, 'settings.py')
            self.module = imp.load_source('settings', main_settings)

    def __getattr__(self, name):
        return getattr(self.module, name)

settings = Settings()