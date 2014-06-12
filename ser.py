#!/usr/local/bin/python2.7
from __future__ import division
import web
from web import form
import hashlib
import random
import urllib
import os
from PIL import Image
import requests
import re
import json
import subprocess
import HTMLParser
import logging
import decimal
import BeautifulSoup
import cStringIO
import urllib2

from mypinnings.database import connect_db, dbget, redis_connect, refresh_individual_user
db = connect_db()
rd = redis_connect()

from mypinnings import auth
from mypinnings.auth import authenticate_user_email, force_login, logged_in, \
    authenticate_user_username, login_user, username_exists, email_exists, \
    logout_user, generate_salt
from mypinnings.template import tpl, ltpl, lmsg
import mypinnings.session
from mypinnings import cached_models
from mypinnings.conf import settings
from mypinnings import pin_utils
import mypinnings.register
import mypinnings.facebook
import mypinnings.google
import mypinnings.register_twitter
from mypinnings.register import valid_email
import mypinnings.pin
import mypinnings.profile_settings
import admin
import glob
import api_server
from settings import SEARCH_PINS

from mypinnings.api import api_request, convert_to_id, convert_to_logintoken

# #

web.config.debug = True

urls = (
    '/api', api_server.api_app,
    '/facebook', mypinnings.facebook.app,
    '/google', mypinnings.google.app,
    '/register_twitter', mypinnings.register_twitter.app,
    '/register', mypinnings.register.app,
    '/pin', mypinnings.pin.app,
    '/settings', mypinnings.profile_settings.app,
    '/', 'PageIndex',
    '/(first-time)', 'PageIndex',
    '/login', 'PageLogin',
    '/reg-checkuser', 'PageCheckUsername',
    '/reg-checkpw', 'PageCheckPassword',
    '/reg-checkemail', 'PageCheckEmail',
    '/activate', 'PageActivate',
    '/resend-activation', 'mypinnings.register.PageResendActivation',
    '/logout', 'PageLogout',
    '/dashboard', 'PageDashboard',
    '/lists/(\d+)/items/?','mypinnings.lists.ListItemsJson',
    '/lists', 'PageBoards',
    '/browse', 'PageBrowse',
    '/category/(.*)', 'mypinnings.category_listing.PageCategory',
    '/new-list', 'PageNewBoard',
    '/newaddpin', 'NewPageAddPin',
    '/newaddpinform', 'NewPageAddPinForm',

    '/add-from-website', 'PageAddPinUrl',
    '/add-to-your-own-getlist/(\d*)', 'PageRepin',
    '/remove-from-own-getlist', 'PageRemoveRepin',
    # '/settings', 'PageEditProfile',
    # '/settings/(email)', 'PageEditProfile',
    # '/settings/(profile)', 'PageEditProfile',
    # '/settings/(password)', 'PageEditProfile',
    # '/settings/(social-media)', 'PageEditProfile',
    # '/settings/(privacy)', 'PageEditProfile',
    # '/settings/(email-settings)', 'PageEditProfile',
    '/p/(.*)', 'PagePin',
    '/messages', 'PageMessages',
    '/newconvo/(\d*)', 'PageNewConvo',
    '/convo/(\d*)', 'PageConvo',
    '/follow/(\d*)', 'PageFollow',
    '/addfriend/(\d*)', 'PageAddFriend',
    '/preview', 'PagePreview',
    '/like/(\d*)', 'PageLike',
    '/unlike/(\d*)', 'PageUnlike',
    '/users', 'PageUsers',
    '/notifications', 'PageNotifications',
    '/notif/(\d*)', 'PageNotif',
    # '/changepw', 'PageChangePw',
    # '/changesm', 'PageChangeSM',
    # '/changeprivacy', 'PageChangePrivacy',
    # '/changeemail', 'PageChangeEmail',
    '/categories/(.*?)/', 'PageViewCategory',
    '/changebg', 'PageChangeBG',
    '/bg/remove', 'PageRemoveBg',
    '/changebgpos', 'PageChangeBGPos',
    '/share/(\d*)', 'PageShare',
    '/followed-by/(\d*)', 'PageFollowedBy',
    '/following/(\d*)', 'PageFollowing',

    '/unfriend/(\d*)', 'PageUnfriend',
    '/cancelfr/(\d*)', 'PageUnfriend',
    '/acceptfr/(\d*)', 'PageAcceptFR',
    '/unfollow/(\d*)', 'PageUnfollow',

    '/.*?/photos', 'PagePhotos',
    '/photos', 'PagePhotos',
    '/newalbum', 'PageNewAlbum',
    '/album/(\d*)', 'PageAlbum',
    '/album/(\d*)/remove', 'PageAlbum',
    '/newpic/(\d*)', 'PageNewPicture',
    '/photo/(\d*)', 'PagePhoto',
    '/photo/(\d*)/remove', 'PageRemovePhoto',
    '/photo/(\d*)/default', 'PageDefaultPhoto',
    '/photo/(\d*)/like', 'PageLikePhoto',
    '/photo/(\d*)/dislike', 'PageDislikePhoto',
    '/photo/(\d*)/comment', 'PageCommentPhoto',
    '/background/(\d*)/like', 'PageLikeBackground',
    '/background/(\d*)/dislike', 'PageDislikeBackground',
    '/background/(\d*)/comment', 'PageCommentBackground',
    '/background/(\d*)/remove', 'PageRemoveBackground',
    '/setprofilepic/(\d*)', 'PageSetProfilePic',
    '/setprivacy/(\d*)', 'PageSetPrivacy',

    '/admin/input/', 'mypinnings.data_loaders.PinLoaderPage',
    '/admin/input/pins/(\d*)/?', 'mypinnings.data_loaders.LoadersEditAPI',
    '/admin/input/update_pin/?', 'mypinnings.data_loaders.UpdatePin',
    '/admin/input/pins/?', 'mypinnings.data_loaders.LoadersEditAPI',
    '/admin/input/list', 'mypinnings.data_loaders.PaginateLoadedItems',
    '/admin/input/change_pin_categories/?', 'mypinnings.data_loaders.ChangePinsCategories',
    '/admin/input/change_page_size_for_loaded_items/?', 'mypinnings.data_loaders.ChangePageSizeForLoadedItems',
    '/admin/input/change_filter_by_tag_for_loaded_items/?', 'mypinnings.data_loaders.ChangeFilterByTagForLoadedItems',
    '/admin/input/change_filter_by_category_for_loaded_items/?', 'mypinnings.data_loaders.ChangeFilterByCategoryForLoadedItems',
    '/admin/input/get_categories_for_items', 'mypinnings.data_loaders.GetCategoriesForItems',
    '/admin', admin.app,

    '/fbgm/(.*?)', 'PageHax',

    '/connect', 'PageConnect',
    '/profile/(\d*)', 'PageProfile',

    '/sort', 'PageSort',
    '/sort/(\d*)', 'PageSort',
    '/sort/(\d*)/(back)', 'PageSort',
    '/sort/(\d*)/(\d*)', 'PageSortPut',
    '/sortdelete/(\d*)', 'PageSortDelete',

    '/changeprofile', 'PageChangeProfile',
    '/maintain/site/david/is/awesome', 'PageDavid',

    '/search/items', 'PageSearchItems',
    '/search/people', 'PageSearchPeople',

    '/recover_password/?', 'mypinnings.recover_password.PasswordRecoveryStart',
    '/recover_password_username_test/', 'mypinnings.recover_password.UsernameOrEmailValidator',
    '/recover_password_sent/?', 'mypinnings.recover_password.EmailSentPage',
    '/pwreset/(\d*)/(\d*)/(.*)/', 'mypinnings.recover_password.PasswordReset',
    '/recover_password_complete/', 'mypinnings.recover_password.RecoverPasswordComplete',
    '/getuserpins/(.*?)', 'GetUserPins',
    '/(.*?)', 'PageProfile2',
    '/(.*?)/(.*?)', 'PageConnect2',

)

app = web.application(urls, globals())
mypinnings.session.initialize(app)
sess = mypinnings.session.sess
mypinnings.template.initialize(directory='t')
cached_models.initialize(db)
from mypinnings.cached_models import all_categories


PIN_COUNT = 20


logger = logging.getLogger('ser')


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def hash(data):
    return hashlib.sha1(data).hexdigest()


def rs():
    return hash(str(random.randint(1, 10000)))




def make_notif(user_id, msg, url, fr_id=None):
    params = dict(user_id=user_id, message=msg, link=url)
    if fr_id is not None:
        params['fr'] = True
        params['fr_id'] = fr_id

    return db.insert('notifs', **params)


def transform_name_to_url(name):
    name = name.lower()
    name = ''.join([x for x in name if x.isalnum() or x == ' '])

    while '  ' in name:
        name = name.replace('  ', ' ')
    return name.replace(' ', '-')

for x in all_categories:
    x['url_name'] = transform_name_to_url(x['name'])



def json_pins(pins, template=None):
    template = template or 'onepin'
    pins = [str(tpl(template, x)) for x in pins]
    return json.dumps(pins)


class PageIndex:
    if not hasattr(settings, 'LANGUAGES') or not settings.LANGUAGES:
        languages = (('en', 'English'),)
    else:
        languages = settings.LANGUAGES
    _form = web.form.Form(
        web.form.Textbox('username', web.form.notnull, id='username', autocomplete='off'),
        web.form.Textbox('name', web.form.notnull, autocomplete='off',
                         description="Complete name"),
        web.form.Textbox('email', valid_email, web.form.notnull, autocomplete='off', id='email'),
        web.form.Password('password', web.form.notnull, id='password', autocomplete='off'),
        web.form.Dropdown('language', languages, web.form.notnull),
        web.form.Button('Let\'s get started!')
    )

    def GET(self, first_time=None):
        # query1 = '''
        #     select
        #         pins.*, tags.tags, categories.slug as category, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
        #         count(distinct p1) as repin_count,
        #         count(distinct l1) as like_count
        #     from pins
        #         left join tags on tags.pin_id = pins.id
        #         left join pins p1 on p1.repin = pins.id
        #         left join likes l1 on l1.pin_id = pins.id
        #         left join users on users.id = pins.user_id
        #         left join follows on follows.follow = users.id
        #         left join categories on categories.id in
        #             (select category_id from pins_categories where pin_id = pins.id limit 1)
        #     where users.id = $id
        #     group by tags.tags, categories.id, pins.id, users.id offset %d limit %d'''

        # query2 = '''
        #     select
        #         tags.tags, pins.*, categories.slug as category, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
        #         count(distinct p1.id) as repin_count,
        #         count(distinct l1) as like_count
        #     from pins
        #         left join tags on tags.pin_id = pins.id
        #         left join users on users.id = pins.user_id
        #         left join pins p1 on p1.repin = pins.id
        #         left join likes l1 on l1.pin_id = pins.id
        #         left join categories on categories.id in
        #             (select category_id from pins_categories where pin_id = pins.id limit 1)
        #     where not users.private
        #     group by tags.tags, categories.id, pins.id, users.id order by timestamp desc offset %d limit %d'''

        offset = int(web.input(offset=1).offset)
        ajax = int(web.input(ajax=0).ajax)
        pins = []

        if logged_in(sess):
            data_to_send = {
                'csid_from_client': '',
                'page': offset,
                # 'items_per_page': PIN_COUNT
                'items_per_page': 100
            }

            # if logged_in(sess):
            #     data_to_send['user_id'] = sess.user_id
            #     url = "api/profile/userinfo/pins"
            # else:
            data_to_send['query_type'] = "range"
            data_to_send['not_private'] = True
            url = "api/image/query/category"

            data = api_request(url, "POST", data_to_send)
            if data['status'] == 200:
                image_id_list = data['data'].get('image_id_list', None)
                if image_id_list is None:
                    pins_list = data['data'].get('pins_list', [])
                    image_id_list = [pin['id'] for pin in pins_list]

                data_for_image_query = {
                    "csid_from_client": '',
                    "query_params": image_id_list
                }
                data_from_image_query = api_request("api/image/query",
                                                    "POST",
                                                    data_for_image_query)

                if data_from_image_query['status'] == 200:
                    pins = data_from_image_query['data']['image_data_list']

            pins = [pin_utils.dotdict(pin) for pin in pins]
            request_data = {}
            request_data['user_id'] = sess.user_id 
            logintoken = convert_to_logintoken(sess.user_id)
            request_data['logintoken'] = logintoken
            request_data['csid_from_client'] = ''
            request_data['use_redis'] = False

            # Retrieve user feeds
            data_from_feeds = api_request("/api/profile/feed/get", data=request_data)
            pins = None
            if data_from_feeds['status'] == 200:
                pins = data_from_feeds['data']['feeds']
                pins = [pin_utils.dotdict(pin) for pin in pins]

        if ajax:
            return json_pins(pins)

        form = self._form()
        return ltpl('index', pins, first_time, form)

class PageLogin:
    _form = form.Form(
        form.Textbox('email', description='Email/Username', id='email'),
        form.Password('password', id='pwd'),
        form.Button('login')
    )

    def msg(self, s):
        raise web.seeother('/login?msg=%s' % s)

    def GET(self):
        force_login(sess, '/dashboard', True)
        form = self._form()
        message = web.input(msg=None).msg
        if message:
            return ltpl('login', form, message)
        return ltpl('login', form)

    def POST(self):
        form = self._form()
        form.validates()

        if not form.d.email or not form.d.password:
            self.msg('Please enter both an email and password.')

        user_id = authenticate_user_email(form.d.email, form.d.password)
        if not user_id:
            user_id = authenticate_user_username(form.d.email, form.d.password)

        if not user_id:
            self.msg('That login was not correct, sorry. (You can login with your username or email.)')

        login_user(sess, user_id)
        results = db.where(table='users', what='is_pin_loader', id=user_id)
        for row in results:
            if row.is_pin_loader:
                raise web.seeother('/admin/input/', absolute=True)
        raise web.seeother('/dashboard')

class PageCheckUsername:
    def GET(self):
        u = web.input(u='').u
        return 'taken' if username_exists(u) else 'ok'


class PageCheckPassword:
    def GET(self):
        p = web.input(p='').p
        return pw_hash(p)


class PageCheckEmail:
    def GET(self):
        e = web.input(e='').e
        return 'taken' if email_exists(e) else 'ok'


class PageActivate:
    def GET(self):
        key = web.input(key='').key
        uid = web.input(uid=0).uid

        logintoken = convert_to_logintoken(uid)

        if logintoken:
            data = {
                "logintoken": logintoken,
                "hashed_activation": key,
            }

            data = api_request("api/signup/confirmuser", "POST", data)


        # user = dbget('users', uid)
        # if user:
        #     if key == hash(str(user.activation)):
        #         db.update('users', where='id=$id', vars={'id': uid}, activation=0)

        raise web.seeother('/')


class PageLogout:
    def GET(self):
        logout_user(sess)
        raise web.seeother('/')


class PageDashboard:
    def GET(self):
        raise web.seeother('/')


class PageBoards:
    def GET(self, bid = None):
        force_login(sess)
        data = {
            'csid_from_client': "",
            'user_id': sess.user_id
        }

        boards = api_request("/api/profile/userinfo/boards",
                             data=data).get("data", [])
        boards = [pin_utils.dotdict(board) for board in boards]
        user = dbget('users',sess.user_id)
        return ltpl('boards', boards, user)


class PageNewBoard:
    _form = form.Form(
        form.Textbox('name'),
        form.Textarea('description'),
        #form.Checkbox('private'),
        form.Button('create'),
    )

    def GET(self):
        force_login(sess)
        form = self._form()
        return ltpl('addboard', form)

    def POST(self):
        form = self._form()
        if not form.validates():
            return 'you need to fill in everything'

        db.insert('boards', user_id=sess.user_id, name=form.d.name,
                  description=form.d.description, public=False)
        raise web.seeother('/lists')


def make_tag(tag):
    return tag.replace('#', '')


class NewPageAddPinForm:
    def POST(self):
        data = web.input()
        if data.board:
            board = int(data.board)
        elif data.board_name:
            board = db.insert(tablename='boards', name=data.board_name, description=data.board_name,
                              user_id = sess.user_id)
        else:
            board=None

        link = data.weblink
        if link and '://' not in link:
            link = 'http://%s' % link

        logintoken = convert_to_logintoken(sess.user_id)

        data_to_send = {
            'image_title': data.title,
            'image_descr': data.comments,
            'link': link,
            'price': None,
            # 'product_url': data.websiteurl,
            'price_range': 1,
            'board_id': board,
            "csid_from_client": '',
            "logintoken": logintoken
        }

        files = {'image_file': open(data.fname)}

        data = api_request("api/image/upload", "POST", data_to_send, files)
        if data['status'] == 200:
            return '/p/%s' % data['data']['external_id']


class NewPageAddPin:
    def upload_image(self):
        image = web.input(image={}).image
        fname = generate_salt()
        ext = os.path.splitext(image.filename)[1].lower()
        new_filename = os.path.join('static', 'tmp', '{}{}'.format(fname, ext))

        with open(new_filename, 'w') as f:
            f.write(image.file.read())

        return new_filename, image.filename

    def POST(self):
        force_login(sess)
        fname, original_filename = self.upload_image()
        return json.dumps({'fname':fname, 'original_filename':original_filename})


class MyOpener(urllib.FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'

class PageAddPinUrl:
    def upload_image(self, url):
        fname = generate_salt()
        ext = os.path.splitext(url)[1].lower()
        fname = os.path.join('static', 'tmp', '{}{}'.format(fname, ext))
        opener = MyOpener()
        opener.retrieve(url, fname)
        if ext.strip() == '':
            im = Image.open(fname)
            new_filename = '{}{}'.format(fname, '.png')
            im.save(new_filename)
            return new_filename
        return fname

    def POST(self):
        force_login(sess)
        data = web.input()
        fname = self.upload_image(data.image_url)

        link = data.link
        if link and '://' not in link:
            link = 'http://%s' % link

        # create a new board if necessary
        if data.list:
            board_id = int(data.list)
        elif data.board_name:
            board_id = db.insert(tablename='boards', name=data.board_name, description=data.board_name,
                                 user_id=sess.user_id)
        else:
            board_id = None

        logintoken = convert_to_logintoken(sess.user_id)

        data = {
            'image_title': data.title,
            'image_descr': data.description,
            'link': link,
            'price': None,
            'product_url': data.websiteurl,
            'price_range': data.price,
            'board_id': board_id,
            "csid_from_client": '',
            "logintoken": logintoken
        }

        files = {'image_file': open(fname)}

        data = api_request("api/image/upload", "POST", data, files)
        if data['status'] == 200:
            return '/p/%s' % data['data']['external_id']


class PageRemoveRepin:
    def GET(self):
        all_categories = cached_models.get_categories()

        force_login(sess)
        info = {'error':True}
        get_input = web.input(_method='get')
        if 'repinid' in get_input and 'pinid' in get_input:
            pin_id = int(get_input['pinid'])
            try:
                pin_utils.delete_pin_from_db(db=db, pin_id=pin_id, user_id=sess.user_id)
                info = {'error':False}
            except:
                #just return the info with error set to True
                logger.error('Could not delete pin', exc_info=True)
        return json.dumps(info)



class PageRepin:
    def make_form(self, pin=None, boards=None):
        boards = boards or []
        boards = [(x.id, x.name) for x in boards]

        if pin is None:
            return form.Form(
                form.Textarea('description'),
                form.Dropdown('board', boards),
                form.Textbox('board_name'),
                form.Textbox('tags', description='tags (optional)', placeholder='#this #is #awesome'),
                form.Button('add to getlist')
            )()
        return form.Form(
            form.Textarea('description', value=pin.description),
            form.Dropdown('board', boards),
            form.Textbox('board_name'),
            form.Textbox('tags', description='tags (optional)', placeholder='#this #is #awesome'),
            form.Button('add to getlist')
        )()

    def GET(self, pin_id):
        all_categories = cached_models.get_categories()

        force_login(sess)

        data = {
            'csid_from_client': "",
            'user_id': sess.user_id
        }

        boards = api_request("/api/profile/userinfo/boards",
                             data=data).get("data", [])
        lists = [pin_utils.dotdict(board) for board in boards]

        pin_id = int(pin_id)
        pin = dbget('pins', pin_id)
        if pin is None:
            return 'pin doesn\'t exist'

        return ltpl('repin', pin, self.make_form(pin, lists))

    def POST(self, pin_id):
        force_login(sess)

        pin_id = int(pin_id)
        transaction = db.transaction()
        try:
            pin = dbget('pins', pin_id)
            if pin is None:
                return 'pin doesn\'t exist'

            form = self.make_form()
            if not form.validates():
                return 'please fill out all the form fields'
            if form.d.board and form.d.board != '':
                board = int(form.d.board)
            elif form.d.board_name != '':
                board = db.insert(tablename='boards', name=form.d.board_name, description=form.d.board_name,
                                  user_id=sess.user_id)
            else:
                return 'Please fill aout all the form fields'
            # preserve all data from original pin, update description, repin and board
            new_pin = pin_utils.create_pin(db=db,
                                       user_id=sess.user_id,
                                       title=pin.name,
                                       description=form.d.description,
                                       link=pin.link,
                                       tags=form.d.tags,
                                       price=pin.price,
                                       product_url=pin.product_url,
                                       price_range=pin.price_range,
                                       image_filename=None,
                                       board_id=board,
                                       repin=pin.id
                                       )
            # copy the same images url from the old pin, no need to upload the same image
            pin_utils.update_pin_image_urls(db=db,
                                            pin_id=new_pin.id,
                                            user_id=sess.user_id,
                                            image_url=pin.image_url,
                                            image_width=pin.image_width,
                                            image_height=pin.image_height,
                                            image_202_url=pin.image_202_url,
                                            image_202_height=pin.image_202_height,
                                            image_212_url=pin.image_212_url,
                                            image_212_height=pin.image_212_height,
                                            )
            # preserve all the categories from original pin
            results = db.where(table='pins_categories', pin_id=pin_id)
            categories_from_previous_item = (row.category_id for row in results)
            pin_utils.add_pin_to_categories(db=db, pin_id=new_pin.id, category_id_list=categories_from_previous_item)

            user = dbget('users', sess.user_id)
            make_notif(pin.user_id, 'Someone has added your item to their Getlist!', '/p/%s' % pin.external_id)
            transaction.commit()
            raise web.seeother('/%s' % user.username)
        except:
            logger.error('Failed to add to get list', exc_info=True)
            transaction.rollback()
            return 'Server error'


# class PageChangeEmail:
#     _form = form.Form(
#         form.Textbox('email'),
#         form.Textbox('username'))

#     # @csrf_protected # Verify this is not CSRF, or fail
#     def POST(self):
#         force_login(sess)

#         form = self._form()
#         if not form.validates():
#             return 'you need to fill in everything'
#         if db.select('users', where='email = $email', vars={'email' : form.d.email}):
#             return 'Pick another email address'
#         if db.select('users', where='username = $username', vars={'username':form.d.username}):
#             return 'Pick another username'
#         db.update('users', where='id = $id', vars={'id': sess.user_id}, email=form.d.email, username=form.d.username)
#         raise web.seeother('/settings/email')


class PageConnect:
    def GET(self):
        """
        Renders the /connect page
        """
        force_login(sess)
        uid = int(sess.user_id)
        logintoken = convert_to_logintoken(sess.user_id)

        follow_url = "/api/social/query/following"
        followers_context = {
            "csid_from_client": "",
            "user_id": uid,
            "logintoken": logintoken}
        followers = api_request(follow_url, data=followers_context).get("data")
        followers = [pin_utils.dotdict(follow) for follow in followers]

        # Getting followers of a given user
        follow_url = "/api/social/query/followed-by"
        followers_context = {
            "csid_from_client": "",
            "user_id": uid,
            "logintoken": logintoken}
        follows = api_request(follow_url, data=followers_context).get("data")
        follows = [pin_utils.dotdict(follow) for follow in follows]
        return ltpl('connect', follows, followers)


class PagePin:
    _form = form.Form(
        form.Textarea('comment'))

    def GET(self, external_id):
        logged = logged_in(sess)
        query1 = '(not count(distinct likes) = 0)' if logged else 'false'
        query2 = 'left join likes on likes.user_id = $uid and likes.pin_id = pins.id' if logged else ''

        qvars = {'external_id': external_id, 'uid': 0}
        if logged:
            qvars['uid'] = sess.user_id

        pin = db.query('''
            select
                pins.*, users.name as user_name, users.pic as user_pic, users.username as user_username,
                ''' + query1 + ''' as liked,
                count(distinct l2) as likes,
                count(distinct p1) as repin_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join users on users.id = pins.user_id
                ''' + query2 + '''
                left join likes l2 on l2.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
            where pins.external_id = $external_id
            group by pins.id, users.id''', vars=qvars)
        if not pin:
            return 'pin not found'

        pin = pin[0]
        pin.categories = db.select(tables=['pins_categories', 'categories'], what="categories.*",
                            where='pins_categories.category_id=categories.id and pins_categories.pin_id=$id',
                            vars={'id': pin.id},
                            order='categories.name')

        if logged and sess.user_id != pin.user_id:
            db.update('pins', where='id = $id', vars={'id': pin.id}, views=web.SQLLiteral('views + 1'))
            refresh_individual_user(sess.user_id, pin.id)

        results = db.where(table='tags', pin_id=pin.id)
        pin.tags = [row.tags for row in results]

        comments = db.query('''
            select
                comments.*, users.pic as user_pic, users.username as user_username, users.name as user_name
            from comments
                join users on users.id = comments.user_id
            where pin_id = $id
            order by timestamp asc''', vars={'id': pin.id})

        rating = db.select('ratings', what='avg(rating)',
                            where='pin_id = $id', vars={'id': pin.id})
        if not rating:
            return 'could not get rating'

        rating = rating[0]
        if not rating.avg:
            rating.avg = 0

        rating = round(float(rating.avg), 2)
        embed = web.input(embed=False).embed
        if embed:
            return tpl('pin', pin, comments, rating, True)
        else:
            return ltpl('pin', pin, comments, rating, False)

    def POST(self, external_id):
        force_login(sess)

        pin = db.where('pins', external_id=external_id)[0]
        if not pin:
            return web.seeother('/')

        form = self._form()
        if not form.validates():
            return web.seeother('/p/%s' % external_id)

        if not form.d.comment:
            return web.seeother('/p/%s' % external_id)

        db.insert('comments',
                  pin_id=pin.id,
                  user_id=sess.user_id,
                  comment=form.d.comment)

        if int(pin.user_id) != int(sess.user_id):
            make_notif(pin.user_id, 'Someone has commented on your pin!', '/p/%s' % external_id)
        raise web.seeother('/p/%s' % external_id)


def get_pins(user_id, offset=None, limit=None, show_private=False):
    query = '''
        select
            tags.tags, pins.*, users.pic as user_pic, users.username as user_username, users.name as user_name,
            count(distinct p1) as repin_count,
            count(distinct l1) as like_count
        from users
            left join pins on pins.user_id = users.id
            left join tags on tags.pin_id = pins.id
            left join pins p1 on p1.repin = pins.id
            left join likes l1 on l1.pin_id = pins.id
        where users.id = $id ''' + ('' if show_private else 'and not users.private') + '''
        group by tags.tags, pins.id, users.id
        order by timestamp desc'''

    if offset is not None:
        query += ' offset %d' % offset
    if limit is not None:
        query += ' limit %d' % limit

    results = db.query(query, vars={'id': user_id})
    pins = []
    current_row = None
    for row in results:
        if not row.id:
            continue
        if not current_row or current_row.id != row.id:
            current_row = row
            tag = row.tags
            current_row.tags = ""
            if tag:
                current_row.tags = tag
            pins.append(current_row)
        else:
            tag = row.tags
            if tag not in current_row.tags:
                current_row.tags = tag
    return pins


class PageProfile:
    def GET(self, user_id):
        user_id = int(user_id)

        user = dbget('users', user_id)
        if not user:
            return 'User not found.'
        raise web.seeother('/' + user.username)


class PageConnect2:
    def GET(self, username, action):
        user = db.query('''
            select users.*,
                count(distinct f1) as follower_count,
                count(distinct f2) as follow_count,
                id as user_id
            from users
                left join follows f1 on f1.follow = users.id
                left join follows f2 on f2.follower = users.id
            where users.username = $username group by users.id''', vars={'username': username})
        if not user:
            return 'Page not found.'
        else:
            user = user[0]
            if 'followers' == action or 'following' == action:
                follows = db.query('''
                    select *, users.* from follows
                        join users on users.id = follows.follow
                    where follows.follower = $id''',
                    vars={'id': user.id})

                followers = db.query('''
                    select *, users.* from follows
                        join users on users.id = follows.follower
                    where follows.follow = $id''',
                    vars={'id': user.id})

                friends = db.query('''
                    select u1.name as u1name, u2.name as u2name,
                        u1.pic as u1pic, u2.pic as u2pic,
                        friends.*
                    from friends
                        join users u1 on u1.id = friends.id1
                        join users u2 on u2.id = friends.id2
                    where friends.id1 = $id or friends.id2 = $id
                    ''', vars={'id': user.id})
            else:
                return 'Page not found'
        return ltpl('connect2',user, follows, followers, friends, action)


class GetUserPins:
    def GET(self, username):
        force_login(sess)
        # logintoken = convert_to_logintoken(sess.user_id)
        # data = {"csid_from_client": ""}

        # # Getting profile of a given user
        # profile_url = "/api/profile/userinfo/info"
        # profile_owner_context = {
        #     "csid_from_client": "",
        #     "username": username,
        #     "logintoken": logintoken}
        # user = api_request(profile_url, data=profile_owner_context)\
        #     .get("data", [])
        # # import ipdb; ipdb.set_trace()
        # if len(user) == 0:
        #     return u"Profile was not found"

        # user = pin_utils.dotdict(user)
        # offset = int(web.input(offset=1).offset)

        # # Updating api_request data with user_id
        # data['user_id'] = user.id
        # data['page'] = offset
        # data['items_per_page'] = PIN_COUNT
        # pins_api_response = api_request("/api/profile/userinfo/pins", data=data)
        # pins = pins_api_response.get('data').get('pins_list')

        # return ltpl('getmorepins.html')
        return ltpl('index.html')


class PageProfile2:
    def GET(self, username):
        """
        Returns user profile information by username
        """
        force_login(sess)
        logintoken = convert_to_logintoken(sess.user_id)
        data = {"csid_from_client": ""}

        # Getting profile of a given user
        profile_url = "/api/profile/userinfo/info"
        profile_owner_context = {
            "csid_from_client": "",
            "username": username,
            "logintoken": logintoken}
        user = api_request(profile_url, data=profile_owner_context)\
            .get("data", [])

        if len(user) == 0:
            return u"Profile was not found"

        photos_context = {
            "csid_from_client": "",
            "user_id": user['id']}

        if logintoken:
            photos_context['logintoken'] = logintoken

        photos = api_request("/api/profile/userinfo/get_photos",
                             data=photos_context)\
            .get("data", {}).get("photos", [])

        photos = [pin_utils.dotdict(photo) for photo in photos]
        user['photos'] = photos

        likes_data = {
            "csid_from_client": "",
            "bg_id": user['id']}

        if logintoken:
            likes_data['logintoken'] = logintoken

        likes_data = api_request("/api/social/background/get_likes",
                             data=likes_data)\
            .get("data", {})
        user['bg_likes'] = pin_utils.dotdict(likes_data)

        comments_data = {
            "csid_from_client": "",
            "bg_id": user['id']}

        if logintoken:
            comments_data['logintoken'] = logintoken

        comments_data = api_request("/api/social/background/get_comments",
                             data=comments_data)\
            .get("data", {})
        user['bg_comments'] = pin_utils.dotdict(comments_data)


        user = pin_utils.dotdict(user)

        # Updating api_request data with user_id
        data['user_id'] = user.id

        # Getting boards of a given user
        boards = api_request("/api/profile/userinfo/boards",
                             data=data).get("data", [])

        pins_ids = []
        for board in boards:
            if len(board['pins_ids']) > 0:
                pins_ids.append(board['pins_ids'][0])

        logintoken = convert_to_logintoken(sess.user_id)
        data_for_image_query = {
            "csid_from_client": '',
            "logintoken": logintoken,
            "query_params": pins_ids
        }
        data_from_image_query = api_request("api/image/query",
                                            "POST",
                                            data_for_image_query)

        boards_first_pins = {}
        if data_from_image_query['status'] == 200:
            for pin in data_from_image_query['data']['image_data_list']:
                boards_first_pins[pin['board_id']] = pin

        boards_list = [pin_utils.dotdict(board) for board in boards]
        # Takes only boards with pins
        boards = [board for board in boards_list if len(board.get("pins_ids")) > 0]


        # Getting categories. Required in case when user
        # is editing own pins.
        categories_to_select = cached_models\
            .get_categories_with_children(db)

        # Updates views & notify profile owner
        is_logged_in = logged_in(sess)
        if is_logged_in and sess.user_id != user.id:
            # Update views of given user profile
            url = "/api/profile/updateviews/%s" % (user.username)
            update_views_context = {
                "csid_from_client": "",
                "logintoken": convert_to_logintoken(sess.user_id)}
            api_request(url, data=data)

            # Notify user about update
            url = "/api/profile/userinfo/info"
            this_user_context = {"csid_from_client": "", "id": sess.user_id}
            this_user = api_request(url, data=this_user_context)\
                .get("data", [])
            # Sending notification in case, it's possible to detect this_user
            if len(this_user) > 0:
                msg = '%s has viewed your profile!' % this_user.get("name", "")
                notif_context = {
                    "csid_from_client": "",
                    "msg": msg,
                    "url": '/%s' % this_user.get("username", "")}
                api_request("/notifications/add", data=notif_context)

        # Offset for rendering
        offset = int(web.input(offset=1).offset)
        data['page'] = offset
        data['items_per_page'] = PIN_COUNT

        show_private = is_logged_in and sess.user_id == user.id

        # pins = api_request("/api/profile/userinfo/pins", data=data)\
        #     .get("data").get("pins_list")
        pins_api_response = api_request("/api/profile/userinfo/pins", data=data)
        pins = pins_api_response.get('data').get('pins_list')
        total = pins_api_response.get('data').get("total")
        total_owned = pins_api_response.get('data').get("total_owned")

        logintoken = convert_to_logintoken(sess.user_id)
        data_for_image_query = {
            "csid_from_client": '',
            "logintoken": logintoken,
            "query_params": [pin['id'] for pin in pins]
        }
        data_from_image_query = api_request("api/image/query",
                                            "POST",
                                            data_for_image_query)

        if data_from_image_query['status'] == 200:
            pins = data_from_image_query['data']['image_data_list']

        pins = [pin_utils.dotdict(pin) for pin in pins]

        data_for_feeds = {
            'csid_from_client': '',
            'logintoken': logintoken,
            'user_id': user.id,
            'limit': 0,
            'offset': 0,
            'use_redis': False
        }

        data_from_feeds = api_request("api/profile/feed/get", "POST", data_for_feeds)
        feeds = None
        if data_from_feeds['status'] == 200:
            feeds = data_from_feeds['data']['feeds']
            feeds = [pin_utils.dotdict(feed) for feed in feeds]


        # Handle ajax request to pins
        ajax = int(web.input(ajax=0).ajax)
        if ajax:
            return json_pins(pins, template='horzpin2')

        # Building hash to use with images
        hashed = rs()

        # Getting link to edit profile...
        if show_private:
            get_input = web.input(_method='get')
            edit_profile = edit_profile_done = None
            if 'editprofile' in get_input:
                edit_profile = True
                if get_input['editprofile']:
                    edit_profile_done = True
            return ltpl('profile', user, pins, offset, PIN_COUNT, hashed,
                        edit_profile, edit_profile_done, boards,
                        categories_to_select, boards_first_pins, total, total_owned, feeds)
        return ltpl('profile', user, pins, offset, PIN_COUNT, hashed,feeds)


class PageFollow:
    def GET(self, user_id):
        force_login(sess)
        user_id = int(user_id)

        user = dbget('users', sess.user_id)
        if not user:
            return 'Your user doesn\'t exist.'

        try:
            db.insert('follows', follow=user_id, follower=sess.user_id)
            make_notif(user_id, '<b>%s</b> is now following you!' % user.username, '/%s' % user.username)
        except: pass
        raise web.seeother('/profile/%d' % user_id)


class PageAddFriend:
    def GET(self, user_id):
        force_login(sess)
        user_id = int(user_id)
        ids = [user_id, sess.user_id]
        ids.sort()

        user = dbget('users', sess.user_id)
        if not user:
            return 'Your user doesn\'t exist.'

        try:
            db.insert('friends', id1=ids[0], id2=ids[1], accepted=sess.user_id)
            make_notif(user_id, '<b>%s</b> wants to be your friend!' % user.name, '/%s' % user.username, fr_id=sess.user_id)
        except: pass
        raise web.seeother('/profile/%d' % user_id)


class PageMessages:
    def GET(self):
        force_login(sess)
        logintoken = convert_to_logintoken(sess.user_id)

        if logintoken:
            data = {
                "logintoken": logintoken,
                "csid_from_client": '',
            }

            data = api_request("api/social/query/conversations", "POST", data)

            if data['status'] == 200:
                conversations = [pin_utils.dotdict(c) for
                    c in data['data']['conversations']]
                return ltpl('messages', conversations)


class PageNewConvo:
    def GET(self, user_id):
        force_login(sess)
        ids = sorted([user_id, sess.user_id])
        print 'ids:', ids
        convo = db.select('convos', where='id1 = $id1 and id2 = $id2',
                          vars={'id1': ids[0], 'id2': ids[1]})
        if convo:
            raise web.seeother('/convo/%d' % convo[0].id)

        print 'convo:', [dict(x) for x in list(convo)]

        convo_id = db.insert('convos', id1=ids[0], id2=ids[1])
        raise web.seeother('/convo/%d' % convo_id)


class PageConvo:
    _form = form.Form(
        form.Textarea('content')
    )

    def GET(self, convo_id):
        force_login(sess)
        convo_id = int(convo_id)

        logintoken = convert_to_logintoken(sess.user_id)

        if logintoken:
            data = {
                "logintoken": logintoken,
                "csid_from_client": '',
                "conversation_id": convo_id,
            }

            data = api_request("api/social/query/messages", "POST", data)

            if data['status'] == 200:
                convo = pin_utils.dotdict(data['data']['conversation'])
                messages = [pin_utils.dotdict(m) for
                    m in data['data']['messages']]

                return ltpl('convo', convo, messages)
            else:
                return data['error_code']

    def POST(self, convo_id):
        force_login(sess)
        convo_id = int(convo_id)

        form = self._form()
        if not form.validates() or not form.d.content:
            return 'fill everything in'

        logintoken = convert_to_logintoken(sess.user_id)

        if logintoken:
            data = {
                "logintoken": logintoken,
                "csid_from_client": '',
                "conversation_id_list": [convo_id],
                "content": form.d.content
            }

            data = api_request("api/social/message_to_conversation",
                               "POST",
                               data)

            if data['status'] == 200:
                raise web.seeother('/convo/%d' % convo_id)
            else:
                raise web.seeother('/convo/%d?msg=%s' % (convo_id,
                                                         data['error_code']))

        raise web.seeother('/convo/%d' % convo_id)


def get_base_url(url):
    return url[:url.rfind('/') + 1]


MAX_IMAGES = 100


def get_url_info(contents, base_url):
    #links = re.findall(r'<img.*?src\=\"([^\"]*)\"', contents, re.DOTALL)
    soup = BeautifulSoup.BeautifulSoup(contents)
    links = [x['src'] for x in soup("img") if x.get('src', 0)!=0]
    links = ['http:' + x if x.startswith('//') else x for x in links]
    links = [x if '://' in x else base_url + x for x in links]
    if len(links) > MAX_IMAGES:
        links = random.sample(links, MAX_IMAGES)

    info = {'images': links}

    title = re.findall(r'<title>(.*?)</title>', contents, re.DOTALL)
    if title:
        parser = HTMLParser.HTMLParser()
        info['title'] = parser.unescape(title[0])
    return info


class PagePreview:
    def GET(self):
        try:
            url = web.input(url=None).url
            if url is None:
                return 'url needed'

            if url.replace('https://', '').replace('http://', '').find('/') == -1:
                url += '/'
            if url.startswith('//'):
                url = 'http:' + url
            if not '://' in url:
                url = 'http://' + url

            info = {}

            print url
            r = requests.get(url)
            if 'image' in r.headers['content-type']:
                info = {'images': [url]}
            else:
                base_url = get_base_url(url)
                info = get_url_info(r.text, base_url)

            return json.dumps(info)
        except IOError:
            return json.dumps({'status': 'error'})


class PageLike:
    def GET(self, pin_id):
        force_login(sess)
        pin_id = int(pin_id)

        try:
            db.insert('likes', user_id=sess.user_id, pin_id=pin_id)
            #Update redis
            refresh_individual_user(sess.user_id, pin_id)
        except:
            pass
        results = db.where(table='pins', id=pin_id)
        for row in results:
            external_id = row.external_id
        raise web.seeother('/p/%s' % external_id)


class PageUnlike:
    def GET(self, pin_id):
        force_login(sess)
        pin_id = int(pin_id)

        db.delete('likes', where='user_id = $uid and pin_id = $pid',
                  vars={'uid': sess.user_id, 'pid': pin_id})
        results = db.where(table='pins', id=pin_id)
        #Update redis
        refresh_individual_user(sess.user_id, pin_id)

        for row in results:
            external_id = row.external_id
        raise web.seeother('/p/%s' % external_id)


class PageUsers:
    def GET(self):
        users = db.select('users')
        return ltpl('users', users)


class PageNotifications:
    """ Responsible for rendering a list of notifications for user profile"""
    def GET(self):
        """ Renders notifications """
        force_login(sess)
        logintoken = convert_to_logintoken(sess.user_id)
        url = "/api/query/notification"
        context = {
            "logintoken": logintoken,
            "csid_from_client": "1"
        }
        response_data = api_request(url, data=context).get("data")
        notifs = [pin_utils.dotdict(notif) for notif in response_data]
        return ltpl('notifs', notifs)


class PageNotif:
    """ View responsible for rendering individual notifications pages """
    def GET(self, nid):
        force_login(sess)

        url = "/api/notification/%s" % (nid)
        context = {
            "logintoken": convert_to_logintoken(sess.user_id),
            "csid_from_client": "1"
        }
        response = api_request(url, data=context)
        if response.get("status") != 200:
            msg = "It was not possible to open this notification"
            raise web.seeother("/notifications?msg=%s" % msg)
        notif = response.get("data")
        raise web.seeother(notif.get("link"))



# class PageChangePw:
#     _form = form.Form(
#         form.Textbox('old'),
#         form.Textbox('pwd1'),
#         form.Textbox('pwd2')
#     )

#     def POST(self):
#         force_login(sess)

#         form = self._form()
#         if not form.validates():
#             raise web.seeother('/settings/password?msg=bad input', absolute=True)

#         # user = dbget('users', sess.user_id)
#         # if not user:
#         #     raise web.seeother('/settings/password?msg=error getting user', absolute=True)

#         # if form.d.pwd1 != form.d.pwd2:
#         #     raise web.seeother('/settings/password?msg=Your passwords don\'t match!', absolute=True)

#         if not form.d.pwd1 or len(form.d.pwd1) < 6:
#             raise web.seeother('/settings/password?msg=Your password must have at least 6 characters.', absolute=True)

#         # if not auth.authenticate_user_username(user.username, form.d.old):
#         #     raise web.seeother('/settings/password?msg=Your old password did not match!', absolute=True)

#         logintoken = convert_to_logintoken(sess.user_id)

#         if logintoken:
#             data = {
#                 "old_password": form.d.old,
#                 "new_password": form.d.pwd1,
#                 "new_password2": form.d.pwd2,
#                 "logintoken": logintoken
#             }

#             data = api_request("api/profile/pwd", "POST", data)
#             if data['status'] == 200:
#                 raise web.seeother('/settings/password')
#             else:
#                 msg = data['error_code']
#                 raise web.seeother('/settings/password?msg=%s' % msg, absolute=True)


#         # auth.chage_user_password(sess.user_id, form.d.pwd1)



# class PageChangeSM:
#     _form = form.Form(
#         form.Textbox('facebook'),
#         form.Textbox('linkedin'),
#         form.Textbox('twitter'),
#         form.Textbox('gplus'),
#     )

#     def POST(self):
#         force_login(sess)

#         form = self._form()
#         if not form.validates():
#             return 'bad input'

#         user = dbget('users', sess.user_id)
#         if not user:
#             return 'error getting user'

#         db.update('users', where='id = $id', vars={'id': sess.user_id}, **form.d)
#         raise web.seeother('/settings/social-media')


# class PageChangePrivacy:
#     _form = form.Form(
#         form.Checkbox('private'),
#     )

#     def POST(self):
#         force_login(sess)

#         form = self._form()
#         form.validates()

#         db.update('users', where='id = $id', vars={'id': sess.user_id}, **form.d)
#         raise web.seeother('/settings/privacy')


class PageUnfriend:
    def GET(self, user_id):
        force_login(sess)
        user_id = int(user_id)

        ids = sorted([sess.user_id, user_id])

        db.delete('friends', where='id1 = $id1 and id2 = $id2',
                vars={'id1': ids[0], 'id2': ids[1]})
        raise web.seeother('/profile/%d' % user_id)


class PageAcceptFR:
    def GET(self, user_id):
        force_login(sess)
        user_id = int(user_id)

        ids = sorted([sess.user_id, user_id])
        db.update('friends', where='id1 = $id1 and id2 = $id2 and accepted = $accepted',
                  vars={'id1': ids[0], 'id2': ids[1], 'accepted': user_id},
                  accepted=sum(ids))
        raise web.seeother('/profile/%d' % user_id)


class PageUnfollow:
    def GET(self, user_id):
        force_login(sess)
        user_id = int(user_id)

        db.delete('follows', where='follower = $follower and follow = $following',
                vars={'follower': sess.user_id, 'following': user_id})
        raise web.seeother('/profile/%d' % user_id)


class PageHax:
    def GET(self, username):
        user = db.select('users', where='username = $username', vars={'username': username})
        login_user(sess, user[0].id)
        raise web.seeother('/')


class PagePhotos:
    def GET(self):
        force_login(sess)
        albums = db.select('albums', where='user_id = $uid', vars={'uid': sess.user_id})
        return ltpl('albums', albums)


class PageNewAlbum:
    _form = form.Form(
        form.Textbox('name'),
        form.Button('create new album'),
    )

    def GET(self):
        force_login(sess)
        return ltpl('newalbum', self._form())

    def POST(self):
        force_login(sess)
        form = self._form()
        form.validates()

        album_id = db.insert('albums', user_id=sess.user_id, name=form.d.name)
        raise web.seeother('/album/%d' % album_id)


class PageAlbum:
    def GET(self, aid):
        force_login(sess)
        aid = int(aid)
        # if sess.user_id != aid:
        #    raise web.seeother('/404')
        user = dbget('users', aid)
        if not user:
            raise web.seeother('/404')
        photos = db.select('photos', where='album_id = $id', vars={'id': aid})
        carousel = db.select('photos', where='album_id = $id', vars={'id': aid})
        return ltpl('album', user, photos, carousel)


class PageNewPicture:
    def upload_image(self, pid):
        image = web.input(pic={}).pic
        if image.value:
            ext = os.path.splitext(image.filename)[1].lower()

            with open('static/pics/%d%s' % (pid, ext), 'w') as f:
                f.write(image.file.read())

            if ext != '.png':
                img = Image.open('static/pics/%d%s' % (pid, ext))
                img.save('static/pics/%d.png' % pid)

            img = Image.open('static/pics/%d.png' % pid)
            width, height = img.size
            ratio = 80 / width
            width = 80
            height *= ratio
            img.thumbnail((width, height), Image.ANTIALIAS)
            img.save('static/pics/userthumb%d.png' % pid)

            return True
        return False

    def GET(self, aid):
        force_login(sess)
        aid = int(aid)

        album = dbget('albums', aid)
        if not album:
            return 'no album'

        return ltpl('newpic', album)

    def POST(self, aid):
        force_login(sess)
        aid = int(aid)

        album = dbget('albums', aid)
        if not album:
            return 'no such album'

        if album.user_id != sess.user_id:
            return 'not your album'

        pid = db.insert('photos', album_id=aid)
        picture = self.upload_image(pid)
        raise web.seeother('/album/%d' % aid)


class PagePhoto:
    def GET(self, pid):
        force_login(sess)
        pid = int(pid)

        photo = db.query('''
            select photos.*, albums.name as album_name, albums.user_id from photos
                join albums on albums.id = photos.album_id
            where photos.id = $id''', vars={'id': pid})
        if not photo:
            return 'no such photo'

        photo = photo[0]
        if photo.user_id != sess.user_id:
            return 'no such photo'

        user = dbget('users', sess.user_id)
        return ltpl('photo', photo, user.pic == pid)


class PageRemovePhoto:
    def GET(self, pid):
        force_login(sess)
        pid = int(pid)
        logintoken = convert_to_logintoken(sess.user_id)

        photos_context = {
            "csid_from_client": "",
            "photo_id": pid,
            "logintoken": logintoken}

        data = api_request("/api/profile/userinfo/remove_pic",
                           data=photos_context)

        profile_url = "/api/profile/userinfo/info"
        profile_owner_context = {
            "csid_from_client": "",
            "id": sess.user_id,
            "logintoken": logintoken}
        user = api_request(profile_url, data=profile_owner_context)\
            .get("data", [])

        return web.redirect('/%s' % (user['username']))


class PageDefaultPhoto:
    def GET(self, pid):
        force_login(sess)
        pid = int(pid)
        logintoken = convert_to_logintoken(sess.user_id)

        photos_context = {
            "csid_from_client": "",
            "user_id": sess.user_id}

        photos = api_request("/api/profile/userinfo/get_photos",
                             data=photos_context)\
            .get("data", []).get("photos", [])

        for photo in photos:
            if photo['id'] == pid:
                pass

                break

        profile_update_url = "/api/profile/userinfo/update"
        profile_update_owner_context = {
            "csid_from_client": "",
            "pic": pid,
            "logintoken": logintoken}
        api_request(profile_update_url,
                    data=profile_update_owner_context)

        profile_url = "/api/profile/userinfo/info"
        profile_owner_context = {
            "csid_from_client": "",
            "id": sess.user_id,
            "logintoken": logintoken}
        user = api_request(profile_url, data=profile_owner_context)\
            .get("data", [])

        return web.redirect('/%s' % (user['username']))


class PageLikePhoto:
    def GET(self, pid):
        return like_dislike_photo(pid, "like")


class PageDislikePhoto:
    def GET(self, pid):
        return like_dislike_photo(pid, "dislike")


def like_dislike_photo(pid, action):
    # force_login(sess)
    pid = int(pid)
    logintoken = convert_to_logintoken(sess.user_id)

    photos_context = {
        "csid_from_client": "",
        "photo_id": pid,
        "logintoken": logintoken,
        "action": action}

    data = api_request("/api/social/photo/like_dislike",
                         data=photos_context)

    return_data = {}

    if data['status'] == 200:
        data = data.get('data', {})
        if data['count_likes'] > 0:
            return_data['likes'] = str(data['count_likes']) + \
                " like" + ('s' if data['count_likes'] != 1 else '')
        else:
            return_data['likes'] = ""

    return json.dumps(return_data)


class PageCommentPhoto:
    def POST(self, pid):
        comment = web.input(comment='').comment

        pid = int(pid)
        logintoken = convert_to_logintoken(sess.user_id)

        photo_comment_context = {
            "csid_from_client": "",
            "photo_id": pid,
            "logintoken": logintoken,
            "comment": comment}

        data = api_request("/api/social/photo/add_comment",
                             data=photo_comment_context)

        comment = None

        if data['status'] == 200:
            data = data.get('data', {})
            comment = data.get('comment', None)

        return tpl('comment', comment)


class PageLikeBackground:
    def GET(self, bg_id):
        return like_dislike_background(bg_id, "like")


class PageDislikeBackground:
    def GET(self, bg_id):
        return like_dislike_background(bg_id, "dislike")


def like_dislike_background(bg_id, action):
    # force_login(sess)
    bg_id = int(bg_id)
    logintoken = convert_to_logintoken(sess.user_id)

    photos_context = {
        "csid_from_client": "",
        "bg_id": bg_id,
        "logintoken": logintoken,
        "action": action}

    data = api_request("/api/social/background/like_dislike",
                         data=photos_context)

    return_data = {}

    if data['status'] == 200:
        data = data.get('data', {})
        if data['count_likes'] > 0:
            return_data['likes'] = str(data['count_likes']) + \
                " like" + ('s' if data['count_likes'] != 1 else '')
        else:
            return_data['likes'] = ""

    return json.dumps(return_data)


class PageCommentBackground:
    def POST(self, bg_id):
        comment = web.input(comment='').comment

        bg_id = int(bg_id)
        logintoken = convert_to_logintoken(sess.user_id)

        photo_comment_context = {
            "csid_from_client": "",
            "bg_id": bg_id,
            "logintoken": logintoken,
            "comment": comment}

        data = api_request("/api/social/background/add_comment",
                             data=photo_comment_context)

        comment = None

        if data['status'] == 200:
            data = data.get('data', {})
            comment = data.get('comment', None)

        return tpl('comment', comment)


class PageRemoveBackground:
    def GET(self, pid):
        force_login(sess)
        pid = int(pid)
        logintoken = convert_to_logintoken(sess.user_id)

        photos_context = {
            "csid_from_client": "",
            "logintoken": logintoken}

        data = api_request("/api/profile/userinfo/remove_bg",
                           data=photos_context)

        profile_url = "/api/profile/userinfo/info"
        profile_owner_context = {
            "csid_from_client": "",
            "id": sess.user_id,
            "logintoken": logintoken}
        user = api_request(profile_url, data=profile_owner_context)\
            .get("data", [])

        return web.redirect('/%s' % (user['username']))


class PageSetProfilePic:
    def GET(self, pid):
        force_login(sess)
        pid = int(pid)

        photo = db.query('''
            select id from photos
                where album_id = $sessid
            AND id = $id''', vars={'id': pid, 'sessid': sess.user_id})
        if not photo:
            return 'no such photo'

        photo = photo[0]
        print photo
        if photo.id != pid:
            return 'no such photo'
        db.update('users', where='id = $id', vars={'id': sess.user_id}, pic=pid, bgx=0, bgy=0)
        raise web.seeother('/photo/%d' % pid)


class PageSort:
    def GET(self, pin_id=None, action='next'):
        all_categories = cached_models.get_categories()

        if pin_id is None:
            pin = db.select('temp_pins', where='category is null', limit=1)
            if not pin:
                return 'end of the line'
            raise web.seeother('/sort/%d' % pin[0].id)

        pin_id = int(pin_id)

        pin = dbget('temp_pins', pin_id)
        if not pin:
            raise web.seeother('/sort')

        if pin.deleted:
            if action == 'next':
                raise web.seeother('/sort/%d' % (pin_id + 1))
            raise web.seeother('/sort/%d' % (pin_id - 1))

        pin.description = pin.description.strip()

        return tpl('sort', pin, all_categories)


class PageSortPut:
    def GET(self, pid, cid):
        pid = int(pid)
        cid = int(cid)

        db.update('temp_pins', where='id = $id', vars={'id': pid},
                  category=cid)
        raise web.seeother('/sort/%d' % (pid + 1))


class PageSortDelete:
    def GET(self, pid):
        pid = int(pid)
        db.update('temp_pins', where='id = $id', vars={'id': pid}, deleted=True)
        raise web.seeother('/sort')


category_table = [
    '',
    'recommendations',
    'bikes',
    'cars',
    'arts-collectibles',
    'beauty',
    'books',
    'cell-phones',
    'fashion',
    'gadgets',
    'jewelry',
    'money',
    'movies-and-music',
    'shoes',
    'travel',
    'watches',
    'wine-and-champagne',
]

class PageViewCategory:
    def GET(self, name):
        try:
            cid = category_table.index(name)
            category = dbget('categories', cid)
        except ValueError:
            return 'category not found'

        offset = int(web.input(offset=0).offset)
        ajax = int(web.input(ajax=0).ajax)

        query = '''
            select
                tags.tags, pins.*, categories.id as category, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1.id) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                join pins_categories on pins_categories.pin_id = pins.id
                left join categories on categories.id = pins_categories.category_id
            where pins_categories.category_id = $cid and not users.private
            group by tags.tags, categories.id, pins.id, users.id order by timestamp desc limit %d offset %d''' % (PIN_COUNT, offset * PIN_COUNT)

        pins = list(db.query(query, vars={'cid': cid}))
        return ltpl('category', pins, category, name, offset, PIN_COUNT)


class PageShare:
    def GET(self, pid):
        pin = dbget('pins', pid)
        if not pin:
            return 'Pin not found.'

        return ltpl('share', pin)


class PageChangeBG:
    def upload_image(self):
        file_data = web.input(file={}).file



        new_filename = os.path.join('static',
                                    'tmp',
                                    '{}'.format(file_data.filename))

        with open(new_filename, 'w') as f:
            f.write(file_data.file.read())

        files = {'file': open(new_filename)}

        logintoken = convert_to_logintoken(sess.user_id)

        data_to_send = {
            "csid_from_client": '',
            "logintoken": logintoken
        }

        data = api_request("api/profile/userinfo/upload_bg",
                           "POST",
                           data_to_send,
                           files)

        if data['status'] == 200:
            return True
        return False


    def POST(self):
        force_login(sess)
        self.upload_image()

        db.update('users', where='id = $id', vars={'id': sess.user_id}, bg=True)
        raise web.seeother('/profile/%d' % sess.user_id)


class PageRemoveBg:
    def GET(self):
        force_login(sess)
        user = dbget('users', sess.user_id)
        if user.bg:
            db.update('users', where='id = $id', vars={'id': sess.user_id}, bg=False)
        return web.redirect('/%s' % (user.username))


class PageChangeBGPos:
    _form = form.Form(
        form.Textbox('x'),
        form.Textbox('y'))

    def POST(self):
        force_login(sess)

        form = self._form()
        form.validates()

        db.update('users', where='id=$id', vars={'id':sess.user_id}, headerbgx=form.d.x, headerbgy=form.d.y)
        return '%s %s' % (form.d.x, form.d.y)


class PageChangeProfile:
    def upload_image(self):
        file_data = web.input(file={}).file

        logintoken = convert_to_logintoken(sess.user_id)

        data_to_send = {
            "csid_from_client": '',
            "logintoken": logintoken
        }

        new_filename = os.path.join('static',
                                    'tmp',
                                    '{}'.format(file_data.filename))

        with open(new_filename, 'w') as f:
            f.write(file_data.file.read())

        files = {'file': open(new_filename)}

        data = api_request("api/profile/userinfo/upload_pic",
                           "POST",
                           data_to_send,
                           files)

        if data['status'] == 200:
            return True
        return False

    def POST(self):
        force_login(sess)

        '''Retire this piece of code'''
        # album = db.select('albums', where='user_id = $uid and name = $name', vars={'uid': sess.user_id, 'name': 'Profile Pictures'})
        # if album:
        #    aid = album[0].id
        # else:
        #    aid = db.insert('albums', name='Profile Pictures', user_id=sess.user_id)

        # pid = db.insert('photos', album_id=sess.user_id)
        self.upload_image()
        # reset the image and background positioning
        # db.update('users', where='id = $id', vars={'id': sess.user_id}, pic=pid, bgx=0, bgy=0)
        raise web.seeother('/profile/%d' % sess.user_id)


class PageSetPrivacy:
    def make_form(self, privacy=None):
        return form.Form(
            form.Dropdown('privacy', [(0, 'Default'), (1, 'Private'), (2, 'Public')], value=privacy),
            form.Button('Save')
        )()

    def GET(self, pin_id):
        force_login(sess)
        pin_id = int(pin_id)

        pin = dbget('pins', pin_id)
        if not pin:
            return 'access denied'

        form = self.make_form(pin.privacy)
        return ltpl('privacy', pin, form)

    def POST(self, pin_id):
        force_login(sess)
        pin_id = int(pin_id)

        form = self.make_form()
        form.validates()

        db.update('pins', where='id = $id', vars={'id': pin_id}, privacy=form.d.privacy)
        results = db.where(table='pins', id=pin_id)
        for row in results:
            external_id = row.external_id
        raise web.seeother('/p/%s' % external_id)


class PageDavid:
    def GET(self):
        return ltpl('david')


class PageFollowing:
    """
    Renders the page with a list of users followed by profile owner
    """
    def GET(self, uid):
        force_login(sess)
        uid = int(uid)
        logintoken = convert_to_logintoken(sess.user_id)
        # Getting profile of a given user
        profile_url = "/api/profile/userinfo/info"
        profile_owner_context = {
            "csid_from_client": "",
            "id": uid,
            "logintoken": logintoken}
        user = api_request(profile_url, data=profile_owner_context)\
            .get("data", [])
        if len(user) == 0:
            return u"Profile was not found"
        user = pin_utils.dotdict(user)

        hashed = rs()

        # Getting followers of a given user
        follow_url = "/api/social/query/following"
        followers_context = {
            "csid_from_client": "",
            "user_id": user.id,
            "logintoken": logintoken}
        followers = api_request(follow_url, data=followers_context).get("data")
        results = [pin_utils.dotdict(follower) for follower in followers]
        return ltpl('following', user, results, hashed)


class PageFollowedBy:
    def GET(self, uid):
        force_login(sess)

        uid = int(uid)
        logintoken = convert_to_logintoken(sess.user_id)
        # Getting profile of a given user
        profile_url = "/api/profile/userinfo/info"
        profile_owner_context = {
            "csid_from_client": "",
            "id": uid,
            "logintoken": logintoken}
        user = api_request(profile_url, data=profile_owner_context)\
            .get("data", [])
        if len(user) == 0:
            return u"Profile was not found"

        user = pin_utils.dotdict(user)

        hashed = rs()

        # Getting followers of a given user
        follow_url = "/api/social/query/followed-by"
        followers_context = {
            "csid_from_client": "",
            "user_id": user.id,
            "logintoken": logintoken}

        follows = api_request(follow_url, data=followers_context).get("data")
        results = [pin_utils.dotdict(follow) for follow in follows]
        return ltpl('followedby', user, results, hashed)


class PageBrowse:
    def GET(self):
        all_categories = cached_models.get_categories()

        categories = list(all_categories)
        categories.append({'name': 'Random', 'id': 0, 'slug': ''})
        return ltpl('browse', categories)


class PageCategory:
    def GET(self, cid):
        cid = int(cid)

        if cid == 0:
            category = AttrDict(name='Random', id=0)
        else:
            category = dbget('categories', cid)
            if not category:
                return 'Category not found.'

        offset = int(web.input(offset=0).offset)
        ajax = int(web.input(ajax=0).ajax)

        if cid == 0:
            where = 'random() < 0.1'
        else:
            where = 'categories.id = $cid'

        query = '''
            select
                tags.tags, pins.*, categories.id as category, categories.name as cat_name, users.pic as user_pic,
                users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join follows on follows.follow = users.id
                join pins_categories on pins.id=pins_categories.pin_id
                join categories on pins_categories.category_id = categories.id
            where ''' + where + '''
            group by tags.tags, categories.id, pins.id, users.id
            order by timestamp desc offset %d limit %d''' % (offset * PIN_COUNT, PIN_COUNT)

        subcategories = db.where(table='categories', parent=cid, order='is_default_sub_category desc, name')
        existsrs = db.query('select exists(' + query + ') as exists', vars={'cid': cid})
        for r in existsrs:
            if not r.exists:
                subcatrs = db.where(table='categories', parent=cid, is_default_sub_category=True)
                for scrow in subcatrs:
                    cid = scrow.id
                    break
        pins = db.query(query, vars={'cid': cid})
        data = {
            'csid_from_client': "",
            'user_id': sess.user_id
        }

        boards = api_request("/api/profile/userinfo/boards",
                             data=data).get("data", [])
        boards = [pin_utils.dotdict(board) for board in boards]
        if ajax:
            return json_pins(pins, 'horzpin')
        return ltpl('category', pins, category, all_categories, subcategories, boards)


def make_query(q):
    q = ''.join([x if x.isalnum() else ' ' for x in q])
    while '  ' in q:
        q = q.replace('  ', ' ')

    return q.replace(' ', ' | ')


class PageSearchItems:
    def GET(self):
        force_login(sess)
        pins = None

        orig = web.input(q='').q
        users_found = db.query('select count(*) as c from users where username=$name', vars={'name': orig})
        if 1 == users_found[0].c:
            return web.seeother('/' + orig)

        hashtag = web.input(h='').h
        if SEARCH_PINS:
            offset = int(web.input(offset=1).offset)
            ajax = int(web.input(ajax=0).ajax)

            logintoken = convert_to_logintoken(sess.get('user_id'))
            data = {
                "csid_from_client": '',
                "logintoken": logintoken,
                "page": offset,
                "items_per_page": PIN_COUNT
            }

            if hashtag:
                data['hashtag'] = hashtag
                url = "api/image/query/get_by_hashtags"
            else:
                data['query'] = orig
                url = "api/search/items"

            pins = []

            data = api_request(url, "POST", data)
            if data['status'] == 200:
                data_for_image_query = {
                    "csid_from_client": '',
                    "logintoken": logintoken,
                    "query_params": data['data']['image_id_list']
                }
                data_from_image_query = api_request("api/image/query",
                                                    "POST",
                                                    data_for_image_query)

                if data_from_image_query['status'] == 200:
                    pins = data_from_image_query['data']['image_data_list']

            pins = [pin_utils.dotdict(pin) for pin in pins]

            if ajax:
                return json_pins(pins, 'horzpin')
        return ltpl('search', pins, orig, hashtag)


class PageSearchPeople:
    def GET(self):
        force_login(sess)

        orig = web.input(q='').q
        q = make_query(orig)

        logintoken = convert_to_logintoken(sess.get('user_id'))
        data = {
            "csid_from_client": '',
            "logintoken": logintoken,
            "query": orig
        }

        data = api_request("api/search/people", "POST", data)
        if data['status'] == 200:
            users = data['data']['users']

        users = [pin_utils.dotdict(user) for user in users]

        return ltpl('searchpeople', users, orig)


def csrf_protected(f):
    def decorated(*args, **kwargs):
        inp = web.input()
        if not (inp.has_key('csrf_token') and inp.csrf_token == session.pop('csrf_token', None)):
            raise web.HTTPError(
                "400 Bad request",
                {'content-type':'text/html'},
                """Cross-site request forgery (CSRF) attempt (or stale browser form).
<a href="">Back to the form</a>.""")
        return f(*args, **kwargs)
    return decorated

if __name__ == '__main__':

    app.run()
