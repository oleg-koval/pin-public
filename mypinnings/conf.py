'''
Loads the settings from the settings module, but allows to have
a local_settings module for local development. Those modules must
be in the root of the application, not inside pachage mypinnings

You showld import from here:
from mypinnings.conf import settings

and access the parameters like:
**settings.params
settings.FACEBOOK['application_id']
'''
import imp
import os.path


class Settings():
    '''
    This holds the real settings.

    Is capable of load a local_settings.py for development environments, or
    settings.py for live. Those files must be in the root of the application.
    '''
    def __init__(self):
        '''
        Try to dinamically load the settings and save the module
        '''
        base_dir = os.path.dirname(os.path.dirname(__file__))
        local_settings = os.path.join(base_dir, 'local_settings.py')
        try:
            self.module = imp.load_source('local_settings', local_settings)
        except IOError:
            main_settings = os.path.join(base_dir, 'settings.py')
            self.module = imp.load_source('settings', main_settings)

    def __getattr__(self, name):
        '''
        Returns a value from the settings module (the one in the root directory
        of the application)
        '''
        return getattr(self.module, name)

'''
This is the settings provider object, use this to access settings
'''
settings = Settings()
