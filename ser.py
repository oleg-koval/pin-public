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

from mypinnings.database import connect_db, dbget
db = connect_db()

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
import mypinnings.pin
import admin
import glob
import api_server
# #

web.config.debug = True

urls = (
    '/api', api_server.api_app,
    '/facebook', mypinnings.facebook.app,
    '/google', mypinnings.google.app,
    '/register_twitter', mypinnings.register_twitter.app,
    '/register', mypinnings.register.app,
    '/pin', mypinnings.pin.app,
    '/', 'PageIndex',
    '/(first-time)', 'PageIndex',
    '/login', 'PageLogin',
    '/reg-checkuser', 'PageCheckUsername',
    '/reg-checkpw', 'PageCheckPassword',
    '/reg-checkemail', 'PageCheckEmail',
    '/activate', 'PageActivate',
    '/resend-activation', 'PageResendActivation',
    '/logout', 'PageLogout',
    '/dashboard', 'PageDashboard',
    '/lists/(\d+)/items/?','mypinnings.lists.ListItemsJson',
    '/lists', 'PageBoards',
    '/browse', 'PageBrowse',
    '/category/.*?/(\d*)', 'mypinnings.category_listing.PageCategory',
    '/new-list', 'PageNewBoard',
    '/newaddpin', 'NewPageAddPin',
    '/newaddpinform', 'NewPageAddPinForm',

    '/add-from-website', 'PageAddPinUrl',
    '/add-to-your-own-getlist/(\d*)', 'PageRepin',
    '/remove-from-own-getlist', 'PageRemoveRepin',
    '/settings', 'PageEditProfile',
    '/settings/(email)', 'PageEditProfile',
    '/settings/(profile)', 'PageEditProfile',
    '/settings/(password)', 'PageEditProfile',
    '/settings/(social-media)', 'PageEditProfile',
    '/settings/(privacy)', 'PageEditProfile',
    '/settings/(email-settings)', 'PageEditProfile',
    '/p/(.*)', 'PagePin',
    '/(.*?)/buy-list/(\d*)', 'PageBuyList',
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
    '/changepw', 'PageChangePw',
    '/changesm', 'PageChangeSM',
    '/changeprivacy', 'PageChangePrivacy',
    '/changeemail', 'PageChangeEmail',
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
    '/setprofilepic/(\d*)', 'PageSetProfilePic',
    '/setprivacy/(\d*)', 'PageSetPrivacy',

    '/admin/input/', 'mypinnings.data_loaders.PinLoaderPage',
    '/admin/input/pins/(\d*)/?', 'mypinnings.data_loaders.LoadersEditAPI',
    '/admin/input/update_pin/?', 'mypinnings.data_loaders.UpdatePin',
    '/admin/input/pins/?', 'mypinnings.data_loaders.LoadersEditAPI',
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
    '/(.*?)/(.*?)', 'PageConnect2',
    '/(.*?)', 'PageProfile2',
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
    def GET(self, first_time=None):
        query1 = '''
            select
                pins.*, tags.tags, categories.id as category, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join follows on follows.follow = users.id
                left join categories on categories.id in
                    (select category_id from pins_categories where pin_id = pins.id limit 1)
            where follows.follower = $id
            group by tags.tags, categories.id, pins.id, users.id offset %d limit %d'''

        query2 = '''
            select
                tags.tags, pins.*, categories.id as category, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1.id) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join categories on categories.id in
                    (select category_id from pins_categories where pin_id = pins.id limit 1)
            where not users.private
            group by tags.tags, categories.id, pins.id, users.id order by timestamp desc offset %d limit %d'''

        offset = int(web.input(offset=0).offset)
        ajax = int(web.input(ajax=0).ajax)

        query = (query1 if logged_in(sess) else query2) % (offset * PIN_COUNT, PIN_COUNT)
        qvars = {}
        if logged_in(sess):
            qvars['id'] = sess.user_id

        pins = list(db.query(query, vars=qvars))

        if ajax:
            return json_pins(pins)
        return ltpl('index', pins, first_time)

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

        user = dbget('users', uid)
        if user:
            if key == hash(str(user.activation)):
                db.update('users', where='id=$id', vars={'id': uid}, activation=0)
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
        boards = db.select('boards',
            where='user_id=$user_id',
            vars={'user_id': sess.user_id})
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
        transaction = db.transaction()
        try:
            if data.board:
                board = int(data.board)
            elif data.board_name:
                board = db.insert(tablename='boards', name=data.board_name, description=data.board_name,
                                  user_id = sess.user_id)
            else:
                board=None
            pin = pin_utils.create_pin(db=db,
                                       user_id=sess.user_id,
                                       title=data.title,
                                       description=data.comments,
                                       link=data.weblink,
                                       tags=None,
                                       price=None,
                                       product_url='',
                                       price_range=1,
                                       image_filename=data.fname,
                                       board_id=board,
                                       )
            transaction.commit()
            return '/p/%s' % pin.external_id
        except Exception as e:
            logger.error('Failed to create a pin from a file upload', exc_info=True)
            transaction.rollback()
            return '/'


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


class PageAddPinUrl:
    def upload_image(self, url):
        fname = generate_salt()
        ext = os.path.splitext(url)[1].lower()
        fname = os.path.join('static', 'tmp', '{}{}'.format(fname, ext))
        urllib.urlretrieve(url, fname)
        return fname

    def POST(self):
        force_login(sess)
        data = web.input()
        transaction = db.transaction()
        try:
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

            pin = pin_utils.create_pin(db=db,
                                 user_id=sess.user_id,
                                 title=data.title,
                                 description=data.description,
                                 link=link,
                                 tags=None,
                                 price=None,
                                 product_url=data.websiteurl,
                                 price_range=data.price,
                                 image_filename=fname,
                                 board_id=board_id)
            transaction.commit()
            return '/p/%s' % pin.external_id
        except Exception as e:
            logger.error('Failed to create a pin from an image URL', exc_info=True)
            transaction.rollback()
            return web.seeother(url='?msg={}'.format('This is embarrassing. We where unable to create the product. Please try again.'),
                         absolute=False)


class PageRemoveRepin:
    def GET(self):
        global all_categories

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
        global all_categories

        force_login(sess)

        lists = db.select('boards',
            where='user_id=$user_id',
            vars={'user_id': sess.user_id})

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


class PageEditProfile:
    _form = form.Form(
        form.Textbox('name'),
        form.Dropdown('country', []),
        form.Textbox('hometown'),
        form.Textbox('city'),
        form.Textbox('zip'),
        form.Textbox('username'),
        form.Textbox('website'),
        form.Textarea('about'),
    )

    def GET(self, name=None):
        force_login(sess)
        user = dbget('users', sess.user_id)
        photos = db.select('photos', where='album_id = $id', vars={'id': sess.user_id})
        msg = web.input(msg=None)['msg']
        return ltpl('editprofile', user, settings.COUNTRIES, name, photos, msg)

    def POST(self, name=None):
        user = dbget('users', sess.user_id)
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'you need to fill in everything'

        db.update('users', where='id = $id',
            name=form.d.name, about=form.d.about, username=form.d.username,
            zip=(form.d.zip or None), website=form.d.website, country=form.d.country,
            hometown=form.d.hometown, city=form.d.city,
            vars={'id': sess.user_id})
        get_input = web.input(_method='get')
        if 'user_profile' in get_input:
            raise web.seeother('/%s?editprofile=1' % user.username)
        raise web.seeother('/settings/profile')



class PageChangeEmail:
    _form = form.Form(
        form.Textbox('email'),
        form.Textbox('username'))

    # @csrf_protected # Verify this is not CSRF, or fail
    def POST(self):
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'you need to fill in everything'
        if db.select('users', where='email = $email', vars={'email' : form.d.email}):
            return 'Pick another email address'
        if db.select('users', where='username = $username', vars={'username':form.d.username}):
            return 'Pick another username'
        db.update('users', where='id = $id', vars={'id': sess.user_id}, email=form.d.email, username=form.d.username)
        raise web.seeother('/settings/email')


class PageConnect:
    def GET(self):
        force_login(sess)

        follows = db.query('''
            select *, users.* from follows
                join users on users.id = follows.follow
            where follows.follower = $id''',
            vars={'id': sess.user_id})

        followers = db.query('''
            select *, users.* from follows
                join users on users.id = follows.follower
            where follows.follow = $id''',
            vars={'id': sess.user_id})

        friends = db.query('''
            select u1.name as u1name, u2.name as u2name,
                u1.pic as u1pic, u2.pic as u2pic,
                friends.*
            from friends
                join users u1 on u1.id = friends.id1
                join users u2 on u2.id = friends.id2
            where friends.id1 = $id or friends.id2 = $id
            ''', vars={'id': sess.user_id})

        return ltpl('connect', follows, followers, friends)


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
            return 'pin does not exist'

        form = self._form()
        if not form.validates():
            return 'form did not validate'

        if not form.d.comment:
            return 'please write a comment'

        db.insert('comments',
                  pin_id=pin.id,
                  user_id=sess.user_id,
                  comment=form.d.comment)

        if int(pin.user_id) != int(sess.user_id):
            make_notif(pin.user_id, 'Someone has commented on your pin!', '/pin/%d' % pin.id)
        results = db.where(table='pins', id=pin.id)
        for row in results:
            external_id=row.external_id
        raise web.seeother('/p/%s' % external_id)


class PageBuyList:
    def is_friends(self, category_id):
        ids = sorted([user_id, sess.user_id])

        result = db.select('friends', what='1', where='id1=$id1 and id2=$id2', vars={'id1': ids[0], 'id2': ids[1]})
        return bool(result)

    def GET(self, username, cid):
        cid = int(cid)

        user = db.select('users', where='username = $username', vars={'username': username})
        if not user:
            return 'user not found'

        user = user[0]

        offset = int(web.input(offset=0).offset)
        ajax = int(web.input(ajax=0).ajax)

        category = dbget('categories', cid)

        pins = db.query('''
            select
                tags.tags, pins.*, categories.id as category, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join users on users.id = pins.user_id
                left join tags on tags.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join pins_categories on pins.id = pins_categories.pin_id
                left join categories on categories.id = pins_categories.category_id
            where categories.id = $cid and not users.private
            group by pins.id, tags.tags, users.id, categories.id
            offset %d limit %d''' % (offset * PIN_COUNT, PIN_COUNT),
            vars={'cid': cid})

        if ajax:
            return json_pins(pins)
        print category
        return ltpl('board', user, category, pins)


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
        if not current_row or current_row.id != row.id:
            current_row = row
            tag = row.tags
            current_row.tags = []
            if tag:
                current_row.tags.append(tag)
            pins.append(current_row)
        else:
            tag = row.tags
            if tag not in current_row.tags:
                current_row.tags.append(tag)
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

class PageProfile2:
    def GET(self, username):
        user = db.query('''
            select users.*,
                count(distinct f1) as follower_count,
                count(distinct f2) as follow_count
            from users
                left join follows f1 on f1.follow = users.id
                left join follows f2 on f2.follower = users.id
            where users.username = $username group by users.id''', vars={'username': username})
        if not user:
            return 'Page not found.'

        user = user[0]

        boards = list(db.select('boards',
            where='user_id=$user_id',
            vars={'user_id': user.id}))
        categories_to_select = cached_models.get_categories_with_children(db)
        is_logged_in = logged_in(sess)

        if is_logged_in and sess.user_id != user.id:
            db.update('users', where='id = $id', vars={'id': user.id}, views=web.SQLLiteral('views + 1'))

            this_user = dbget('users', sess.user_id)
            make_notif(user.id, '%s has viewed your profile!' % this_user.name, '/%s' % this_user.username)

        offset = int(web.input(offset=0).offset)

        show_private = is_logged_in and sess.user_id == user.id
        pins = get_pins(user.id, offset=offset * PIN_COUNT, limit=PIN_COUNT, show_private=show_private)

        ajax = int(web.input(ajax=0).ajax)
        if ajax:
            return json_pins(pins, template='horzpin2')

        hashed = rs()

        if logged_in(sess):
            get_input = web.input(_method='get')
            edit_profile = edit_profile_done = None
            if 'editprofile' in get_input:
                edit_profile = True
                if get_input['editprofile']:
                    edit_profile_done = True

            ids = [user.id, sess.user_id]
            ids.sort()
            ids = {'id1': ids[0], 'id2': ids[1]}

            friend_status = db.select('friends',
                                      where='id1 = $id1 and id2 = $id2',
                                      vars=ids)
            friend_status = friend_status[0] if friend_status else False

            is_following = bool(
                db.select('follows',
                          where='follow = $follow and follower = $follower',
                          vars={'follow': int(user.id), 'follower': sess.user_id}))
            photos = db.select('photos', where='album_id = $id', vars={'id': sess.user_id}, order="id DESC")

            return ltpl('profile', user, pins, offset, PIN_COUNT, hashed, friend_status, is_following, photos, edit_profile, edit_profile_done,boards,categories_to_select)
        return ltpl('profile', user, pins, offset, PIN_COUNT, hashed)


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
        convos = db.query('''
            select convos.*, users.name from convos
                join users on users.id = (case
                    when convos.id1 = $id then convos.id2
                    else convos.id1
                end)
            where id1 = $id or id2 = $id''', vars={'id': sess.user_id})
        return ltpl('messages', convos)


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

        convo = db.query('''
            select convos.id, users.id as user_id, users.name from convos
                join users on users.id = (case
                    when convos.id1 = $id then convos.id2
                    else convos.id1
                end)
            where (convos.id = $convo_id and
                   convos.id1 = $id or convos.id2 = $id)''',
            vars={'convo_id': convo_id, 'id': sess.user_id})
        if not convo:
            return 'convo not found'

        messages = db.query('''
            select messages.*, users.name from messages
                join users on users.id = messages.sender
            where messages.convo_id = $convo_id''',
            vars={'convo_id': convo_id})

        return ltpl('convo', convo[0], messages)

    def POST(self, convo_id):
        force_login(sess)
        convo_id = int(convo_id)

        allowed = bool(
            db.select('convos', what='1',
                      where='id = $cid and (id1 = $id or id2 = $id)',
                      vars={'cid': convo_id, 'id': sess.user_id}))
        if not allowed:
            return 'convo not found'

        form = self._form()
        if not form.validates():
            return 'fill everything in'

        db.insert('messages', convo_id=convo_id, sender=sess.user_id,
                  content=form.d.content)
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
        for row in results:
            external_id = row.external_id
        raise web.seeother('/p/%s' % external_id)


class PageUsers:
    def GET(self):
        users = db.select('users')
        return ltpl('users', users)


class PageNotifications:
    def GET(self):
        force_login(sess)
        params = dict(where='user_id = $id', vars={'id': sess.user_id})
        notifs = db.select('notifs', **params)

        return ltpl('notifs', notifs)


class PageNotif:
    def GET(self, nid):
        force_login(sess)
        notif = dbget('notifs', nid)
        print notif
        if int(notif.user_id) != int(sess.user_id):
            return 'Page not found.'

        url = notif.link
        db.delete('notifs', where='id = $id', vars={'id': nid})
        raise web.seeother(url)


class PageChangePw:
    _form = form.Form(
        form.Textbox('old'),
        form.Textbox('pwd1'),
        form.Textbox('pwd2')
    )

    def POST(self):
        force_login(sess)

        form = self._form()
        if not form.validates():
            raise web.seeother('/settings/password?msg=bad input', absolute=True)

        user = dbget('users', sess.user_id)
        if not user:
            raise web.seeother('/settings/password?msg=error getting user', absolute=True)

        if form.d.pwd1 != form.d.pwd2:
            raise web.seeother('/settings/password?msg=Your passwords don\'t match!', absolute=True)

        if not form.d.pwd1 or len(form.d.pwd1) < 6:
            raise web.seeother('/settings/password?msg=Your password must have at least 6 characters.', absolute=True)

        if not auth.authenticate_user_username(user.username, form.d.old):
            raise web.seeother('/settings/password?msg=Your old password did not match!', absolute=True)

        auth.chage_user_password(sess.user_id, form.d.pwd1)
        raise web.seeother('/settings/password')


class PageChangeSM:
    _form = form.Form(
        form.Textbox('facebook'),
        form.Textbox('linkedin'),
        form.Textbox('twitter'),
        form.Textbox('gplus'),
    )

    def POST(self):
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'bad input'

        user = dbget('users', sess.user_id)
        if not user:
            return 'error getting user'

        db.update('users', where='id = $id', vars={'id': sess.user_id}, **form.d)
        raise web.seeother('/settings/social-media')


class PageChangePrivacy:
    _form = form.Form(
        form.Checkbox('private'),
    )

    def POST(self):
        force_login(sess)

        form = self._form()
        form.validates()

        db.update('users', where='id = $id', vars={'id': sess.user_id}, **form.d)
        raise web.seeother('/settings/privacy')


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

        photo = db.query('''
            select album_id from photos where photos.id = $id AND album_id = $album_id ''', vars={'id': pid, 'album_id':sess.user_id})
        if not photo:
            return 'no such photo'

        photo = photo[0]
        user = dbget('users', sess.user_id)
        if photo.album_id != sess.user_id:
            return 'no such photo'
        else:
            db.delete('photos', where="id = %s" % (pid))
            user = dbget('users', sess.user_id)
            '''if this is an avatar update to null'''
            if user.pic == pid:
                db.update('users', where='id = $id', vars={'id': sess.user_id}, pic=None, bgx=0, bgy=0)
        return web.redirect('/%s' % (user.username))


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
        global all_categories

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
        image = web.input(file={}).file
        ext = os.path.splitext(image.filename)[1].lower()

        with open('static/tmp/bg%d%s' % (sess.user_id, ext), 'w') as f:
            f.write(image.file.read())

        if ext != '.png':
            img = Image.open('static/tmp/bg%d%s' % (sess.user_id, ext))
            img.save('static/tmp/bg%d.png' % sess.user_id)

        fname = 'static/tmp/bg%d.png' % sess.user_id
        subprocess.call(['convert', fname, '-resize', '1100', fname])


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
    def upload_image(self, pid):
        image = web.input(file={}).file
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

    def POST(self):
        force_login(sess)

        '''Retire this piece of code'''
        # album = db.select('albums', where='user_id = $uid and name = $name', vars={'uid': sess.user_id, 'name': 'Profile Pictures'})
        # if album:
        #    aid = album[0].id
        # else:
        #    aid = db.insert('albums', name='Profile Pictures', user_id=sess.user_id)

        pid = db.insert('photos', album_id=sess.user_id)
        self.upload_image(pid)
        # reset the image and background positioning
        db.update('users', where='id = $id', vars={'id': sess.user_id}, pic=pid, bgx=0, bgy=0)
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
    def GET(self, uid):
        force_login(sess)

        uid = int(uid)
        user = db.query('''
            select users.*,
                count(distinct f1) as follower_count,
                count(distinct f2) as follow_count
            from users
                left join follows f1 on f1.follow = users.id
                left join follows f2 on f2.follower = users.id
            where users.id = $id group by users.id''', vars={'id': uid})
        if not user:
            return 'User not found.'

        user = user[0]

        hashed = rs()
        results = db.query('''
            select
                users.*,
                count(distinct f1) <> 0 as is_following
            from follows
                join users on users.id = follows.follow
                join follows f1 on f1.follower = $user_id and f1.follow = users.id
            where follows.follower = $id group by users.id''', vars={'id': uid, 'user_id': sess.user_id})
        return ltpl('following', user, results, hashed)


class PageFollowedBy:
    def GET(self, uid):
        force_login(sess)

        uid = int(uid)

        user = db.query('''
            select users.*,
                count(distinct f1) as follower_count,
                count(distinct f2) as follow_count
            from users
                left join follows f1 on f1.follow = users.id
                left join follows f2 on f2.follower = users.id
            where users.id = $id group by users.id''', vars={'id': uid})
        if not user:
            return 'User not found.'

        user = user[0]

        hashed = rs()
        results = db.query('''
            select
                users.*,
                count(distinct f1) <> 0 as is_following
            from follows
                join users on users.id = follows.follow
                left join follows f1 on f1.follower = $user_id and f1.follow = users.id
            where follows.follower = $id group by users.id''', vars={'id': uid, 'user_id': sess.user_id})

        return ltpl('followedby', user, results, hashed)


class PageBrowse:
    def GET(self):
        global all_categories

        categories = list(all_categories)
        categories.append({'name': 'Random', 'id': 0, 'url_name': 'random'})
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
        lists = db.select('boards',
        where='user_id=$user_id',
        vars={'user_id': sess.user_id})

        boards = db.where(table='boards', order='name', user_id=sess.user_id)

        print lists
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

        orig = web.input(q='').q
        q = make_query(orig)
        offset = int(web.input(offset=0).offset)
        ajax = int(web.input(ajax=0).ajax)

        query = """
            select
                tags.tags, pins.*, categories.id as category, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                ts_rank_cd(to_tsvector(tags.tags), query) as rank1,
                ts_rank_cd(pins.tsv, query) as rank2
            from pins
                left join tags on tags.pin_id = pins.id
                join to_tsquery('""" + q + """') query on true
                left join users on users.id = pins.user_id
                left join follows on follows.follow = users.id
                left join categories on categories.id in
                    (select category_id from pins_categories
                    where pin_id = pins.id limit 1)
            where query @@ pins.tsv or query @@ to_tsvector(tags.tags)
            group by tags.tags, categories.id, pins.id, users.id, query.query
            order by rank1, rank2 desc offset %d limit %d""" % (offset * PIN_COUNT, PIN_COUNT)

        pins = db.query(query)
        if ajax:
            return json_pins(pins, 'horzpin')
        return ltpl('search', pins, orig)


class PageSearchPeople:
    def GET(self):
        force_login(sess)

        orig = web.input(q='').q
        q = make_query(orig)

        query = """
            select
                users.*, ts_rank_cd(users.tsv, query) as rank,
                count(distinct f1) <> 0 as is_following
            from users
                join to_tsquery('""" + q + """') query on true
                left join follows f1 on f1.follower = $user_id and f1.follow = users.id
            where query @@ users.tsv group by users.id, query.query
            order by rank desc"""

        users = db.query(query, vars={'user_id': sess.user_id})
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
