'''
HTML form controls for use in web.form.Form as any
other form field type
'''
import web


class Date(web.form.Input):
    '''
    HTML 5 password field
    '''
    def get_type(self):
        return 'date'
    

class EMail(web.form.Input):
    '''
    HTML 5 email field
    '''
    def get_type(self):
        return 'email'
    

class Number(web.form.Input):
    '''
    HTML 5 number field
    '''
    def get_type(self):
        return 'number'
    

class URL(web.form.Input):
    '''
    HTML 5 url field
    '''
    def get_type(self):
        return 'url'