'''
This module is for interfaces to speed user data loading, like Pin Loaders
'''
import web

from mypinnings import cached_models
from mypinnings import template
from mypinnings import session
from mypinnings import auth


class PinLoaderPage(object):
    def get_form(self):
        categories = tuple((cat.id, cat.name) for cat in cached_models.all_categories)
        form = web.form.Form(web.form.Dropdown('category', categories, web.form.notnull),
                             web.form.Textbox('imageurl1'),
                             web.form.Textbox('imageurl2'),
                             web.form.Textbox('imageurl3'),
                             web.form.Textbox('imageurl4'),
                             web.form.Textbox('imageurl5'),
                             web.form.Textbox('imageurl6'),
                             web.form.Textbox('imageurl7'),
                             web.form.Textbox('imageurl8'),
                             web.form.Textbox('imageurl9'),
                             web.form.Textbox('imageurl10'),
                             web.form.File('image1'),
                             web.form.File('image2'),
                             web.form.File('image3'),
                             web.form.File('image4'),
                             web.form.File('image5'),
                             web.form.File('image6'),
                             web.form.File('image7'),
                             web.form.File('image8'),
                             web.form.File('image9'),
                             web.form.File('image10'),
                             web.form.Textbox('title1'),
                             web.form.Textbox('title2'),
                             web.form.Textbox('title3'),
                             web.form.Textbox('title4'),
                             web.form.Textbox('title5'),
                             web.form.Textbox('title6'),
                             web.form.Textbox('title7'),
                             web.form.Textbox('title8'),
                             web.form.Textbox('title9'),
                             web.form.Textbox('title10'),
                             web.form.Textarea('description1'),
                             web.form.Textarea('description2'),
                             web.form.Textarea('description3'),
                             web.form.Textarea('description4'),
                             web.form.Textarea('description5'),
                             web.form.Textarea('description6'),
                             web.form.Textarea('description7'),
                             web.form.Textarea('description8'),
                             web.form.Textarea('description9'),
                             web.form.Textarea('description10'),
                             web.form.Textbox('tags1', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags2', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags3', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags4', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags5', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags6', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags7', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags8', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags9', placeholder='#this #is #awesome'),
                             web.form.Textbox('tags10', placeholder='#this #is #awesome'),
                             web.form.Button('add', id='btn-add')
                             )
        return form()

    def GET(self):
        auth.force_login(session.get_session())
        form = self.get_form()
        return template.ltpl('pin_loader', form)
