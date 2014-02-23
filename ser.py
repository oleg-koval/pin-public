#!/usr/bin/python
from __future__ import division
import web
from web import form
import hashlib
import random
import string
import urllib
import os
from PIL import Image
import requests
import re
import json
from bs4 import BeautifulSoup
import traceback
import subprocess
import HTMLParser
import tpllib
##
from db import connect_db

urls = (
    '/', 'PageIndex',
    '/(first-time)', 'PageIndex',
    '/login', 'PageLogin',
    '/register', 'PageRegister',
    '/reg-checkuser', 'PageCheckUsername',
    '/reg-checkpw', 'PageCheckPassword',
    '/reg-checkemail', 'PageCheckEmail',
    '/activate', 'PageActivate',
    '/resend-activation', 'PageResendActivation',
    '/logout', 'PageLogout',
    '/dashboard', 'PageDashboard',
    '/lists', 'PageBoards',
    '/browse', 'PageBrowse',
    '/category/.*?/(\d*)', 'PageCategory',
    '/new-list', 'PageNewBoard',
    '/addpin', 'PageAddPin',
    '/add-from-website', 'PageAddPinUrl',
    '/add-to-your-own-getlist/(\d*)', 'PageRepin',
    '/settings', 'PageEditProfile',
    '/settings/(email)', 'PageEditProfile',
    '/settings/(profile)', 'PageEditProfile',
    '/settings/(password)', 'PageEditProfile',
    '/settings/(social-media)', 'PageEditProfile',
    '/settings/(privacy)', 'PageEditProfile',
    '/settings/(email-settings)', 'PageEditProfile',
    '/pin/(\d*)', 'PagePin2',
    '/item/(\d*)', 'PagePin',
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

    '/admin', 'admin.PageIndex',
    '/admin/', 'admin.PageIndex',
    '/admin/login', 'admin.PageLogin',
    '/admin/search', 'admin.PageSearch',
    '/admin/search/(all)', 'admin.PageSearch',
    '/admin/create', 'admin.PageCreate',
    '/admin/user/(\d*)', 'admin.PageUser',
    '/admin/closeuser/(\d*)', 'admin.PageCloseUser',
    '/admin/edituser/(\d*)', 'admin.PageEditUser',
    '/admin/createuser', 'admin.PageCreateUser',
    '/admin/logout', 'admin.PageLogout',
    '/admin/relationships', 'admin.PageRelationships',

    '/fbgm/(.*?)', 'PageHax',

    '/after-signup', 'PageAfterSignup',
    '/after-signup/(\d*)', 'PageAfterSignup',

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

    '/(.*?)', 'PageProfile2',
)

app = web.application(urls, globals())


def debuggable_session(app):
    if web.config.get('_sess') is None:
        sess = web.session.Session(app, web.session.DiskStore('sessions'))
        web.config._sess = sess
        return sess
    return web.config._sess

sess = debuggable_session(app)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def hash(data):
    return hashlib.sha1(data).hexdigest()


def rs():
    return hash(str(random.randint(1, 10000)))


def generate_salt(length=10):
    random.seed()
    pool = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(pool) for i in range(length))


def logged_in(sess):
    if 'logged_in' in sess:
        if sess.logged_in:
            return sess.user_id
    return False


def force_login(sess, page='/', check_logged_in=False):
    user_id = logged_in(sess)
    if bool(user_id) == check_logged_in:
        raise web.seeother(page)
 

def email_exists(email):
    result = db.select('users',
        what='1',
        where='email=$email',
        vars={'email': email},
        limit=1)
    return bool(result)


def username_exists(username):
    result = db.select('users',
        what='1',
        where='username=$username',
        vars={'username': username},
        limit=1)
    return bool(result)


def create_user(email, password, **params):
    pw_hash = hash(password)
    pw_salt = generate_salt()
    pw_hash = hash(pw_hash+pw_salt)

    return db.insert('users', email=email, pw_hash=pw_hash, pw_salt=pw_salt, **params)


def authenticate_user_email(email, password):
    users = db.select('users', where='email = $email', vars={'email': email},
    what='id, pw_hash, pw_salt')
    if not users:
        return False

    user = users[0]
    if hash(hash(password) + user['pw_salt']) == user['pw_hash']:
        return user['id']
    return False


def authenticate_user_username(username, password):
    users = db.select('users', where='username = $username', vars={'username': username}, what='id, pw_hash, pw_salt')
    if not users:
        return False

    user = users[0]
    if hash(hash(password) + user['pw_salt']) == user['pw_hash']:
        return user['id']
    return False


def cookie_logged_in():
    try:
        cookies = web.cookies()
        result = db.select('users',
            where='id = $user_id and seriesid = $seriesid and logintoken=$logintoken',
            vars=dict((x, getattr(cookies, x)) for x in ['user_id', 'seriesid', 'logintoken']))
        if len(list(result)) == 1:
            return cookies.user_id
    except:
        return False


def update_cookie_login(user_id, new_series_id=False):
    params = {
        'user_id': user_id,
        'logintoken': generate_salt()}
    if new_series_id:
        params['seriesid'] = generate_salt()

    for k, v in params.iteritems():
        web.setcookie(k, v, 9999999) # a really long time

    del params['user_id']
    db.update('users',
        where='id = $user_id',
        vars={'user_id': user_id},
        **params)

def logged_in(sess):
    if 'logged_in' in sess:
        if sess.logged_in:
            return sess.user_id
    return False

def force_login(sess, page='/login', check_logged_in=False):
    user_id = logged_in(sess)
    if not user_id:
        user_id = cookie_logged_in()

    if user_id:
        login_user(sess, user_id)

    redirect = (bool(user_id) == check_logged_in)

    if user_id:
        update_cookie_login(user_id)
    if redirect:
        raise web.seeother(page)

def login_user(sess, user_id):
    if logged_in(sess):
        return False

    user_id = int(user_id)
    sess.logged_in = True
    sess.user_id = user_id
    update_cookie_login(user_id, new_series_id=True)
    return True

def logout_user(sess):
    sess.kill()
    for x in ['user_id', 'seriesid', 'logintoken']:
        web.setcookie(x, '', expires=-1)

def tpl(*params):
    #global template_obj
    return template_obj(*params)


def template_closure(directory):
    global settings
    templates = web.template.render(directory,
        globals={'sess': sess, 'tpl': tpl, 'tpllib': tpllib})
    def render(name, *params):
        return getattr(templates, name)(*params)
    return render

template_obj = template_closure('t')


def ltpl(*params):
    global all_categories

    if logged_in(sess):
        user = dbget('users', sess.user_id)
        acti_needed = user.activation
        notif_count = db.select('notifs', what='count(*)', where='user_id = $id', vars={'id': sess.user_id})
        all_albums = list(db.select('albums',where="user_id=%s"%(sess.user_id), order='id'))
        return tpl('layout', tpl(*params), all_categories, all_albums,user, acti_needed, notif_count[0].count)
    return tpl('layout', tpl(*params), all_categories)


def lmsg(msg):
    return tpl('layout', msg)


def make_notif(user_id, msg, url, fr_id=None):
    params = dict(user_id=user_id, message=msg, link=url)
    if fr_id is not None:
        params['fr'] = True
        params['fr_id'] = fr_id

    return db.insert('notifs', **params)


db = connect_db()
all_categories = list(db.select('categories', order='id'))


def transform_name_to_url(name):
    name = name.lower()
    name = ''.join([x for x in name if x.isalnum() or x == ' '])

    while '  ' in name:
        name = name.replace('  ', ' ')
    return name.replace(' ', '-')

for x in all_categories:
    x['url_name'] = transform_name_to_url(x['name'])


PIN_COUNT = 20


def dbget(table, row_id):
    rows = db.select(table, where='id = $id', vars={'id': row_id})
    return rows[0] if rows else None


def json_pins(pins, template=None):
    template = template or 'onepin'
    pins = [str(tpl(template, x)) for x in pins]
    return json.dumps(pins)

class PageIndex:
    def GET(self, first_time=None):
        query1 = '''
            select
                pins.*, tags.tags, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join follows on follows.follow = users.id
                left join categories on categories.id = pins.category
            where follows.follower = $id
            group by tags.tags, categories.id, pins.id, users.id offset %d limit %d'''

        query2 = '''
            select
                tags.tags, pins.*, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1.id) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join categories on categories.id = pins.category
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
        form.Password('password', id='email'),
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
        raise web.seeother('/dashboard')


def send_activation_email(email, hashed, user_id):
    web.sendmail('noreply@mypinnings.com', email, 'Please activate your MyPinnings account',
                 str(tpl('email', hashed, user_id)), headers={'Content-Type': 'text/html;charset=utf-8'})


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


class PageRegister:
    _form = form.Form(
        form.Textbox('email', autocomplete='off', id='email', placeholder='Where we\'ll never spam you.'),
        form.Textbox('username', id='username', autocomplete='off', placeholder='The name in your url.'),
        form.Password('password', id='password', autocomplete='off', placeholder='Something you\'ll remember but others won\'t guess.'),
        form.Textbox('name', autocomplete='off', placeholder='The name next to your picture.'),
        form.Button('Let\'s get started!')
    )

    def msg(self, s):
        raise web.seeother('/register?msg=%s' % s)

    def GET(self):
        force_login(sess, '/dashboard', True)
        form = self._form()
        message = web.input(msg=None).msg
        if message:
            return ltpl('reg', form, message)
        return tpl('reg', form)

    def POST(self):
        form = self._form()
        form.validates()

        if not all([form.d.email, form.d.password, form.d.name, form.d.username]):
            self.msg('Please enter an email, pasword, and username.')

        if email_exists(form.d.email):
            self.msg('Sorry, that email already exists.')

        if username_exists(form.d.username):
            self.msg('Sorry, that username already exists.')

        activation = random.randint(1, 10000)
        hashed = hash(str(activation))

        user_id = create_user(form.d.email, form.d.password, name=form.d.name, username=form.d.username, activation=activation)
        if not user_id:
            self.msg('Sorry, a database error occurred and we couldn\'t create your account.')

        send_activation_email(form.d.email, hashed, user_id)
        login_user(sess, user_id)
        raise web.seeother('/after-signup')


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
    def GET(self):
        force_login(sess)
        boards = db.select('boards',
            where='user_id=$user_id',
            vars={'user_id': sess.user_id})
        return ltpl('boards', boards)


class PageNewBoard:
    _form = form.Form(
        form.Textbox('name'),
        form.Textarea('description'),
        form.Checkbox('private'),
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
                  description=form.d.description, public=not form.d.private)
        raise web.seeother('/lists')


def make_tag(tag):
    return tag[1:] if tag[0] == '#' else tag


class PageAddPin:
    def make_form(self, categories=None):
        categories = categories or []
        categories = [(x.id, x.name) for x in categories]
        return form.Form(
            form.File('image'),
            form.Textarea('description'),
            form.Dropdown('category', categories),
            form.Textbox('tags', description='tags (optional)', placeholder='#this #is #awesome'),
            form.Button('add', id='btn-add')
        )()

    def GET(self):
        global all_categories

        force_login(sess)
        form = self.make_form(all_categories)
        return ltpl('addpin', form)

    def upload_image(self):
        image = web.input(image={}).image
        fname = generate_salt()
        web.debug(image.filename)
        web.debug(image.value)
        ext = os.path.splitext(image.filename)[1].lower()

        with open('static/tmp/%s%s' % (fname, ext), 'w') as f:
            f.write(image.file.read())

        if ext != '.png':
            img = Image.open('static/tmp/%s%s' % (fname, ext))
            img.save('static/tmp/%s.png' % fname)

        img = Image.open('static/tmp/%s.png' % fname)
        width, height = img.size
        ratio = 202 / width
        width = 202
        height *= ratio
        img.thumbnail((width, height), Image.ANTIALIAS)
        img.save('static/tmp/pinthumb%s.png' % fname)

        return fname
    
    def POST(self):
        force_login(sess)
        form = self.make_form()
        if not form.validates():
            return lmsg('Form couldn\'t validate.')

        fname = self.upload_image()
        
        pin_id = db.insert('pins',
            description=form.d.description,
            user_id=sess.user_id,
            category=form.d.category)

        if form.d.tags:
            tags = ' '.join([make_tag(x) for x in form.d.tags.split(' ')])
            db.insert('tags', pin_id=pin_id, tags=tags)

        os.rename('static/tmp/%s.png' % fname,
                  'static/tmp/%d.png' % pin_id)
        os.rename('static/tmp/pinthumb%s.png' % fname,
                  'static/tmp/pinthumb%d.png' % pin_id)
        raise web.seeother('/pin/%d' % pin_id)


class PageAddPinUrl:
    def make_form(self, categories=None):
        categories = categories or []
        categories = [(x.id, x.name) for x in categories]
        return form.Form(
            form.Textbox('url', id='input-url'),
            form.Textarea('description', id='input-desc'),
            form.Dropdown('category', categories),
            form.Textbox('tags', description='tags (optional)', placeholder='#this #is #awesome'),
            form.Hidden('link', id='input-link'),
            form.Button('add', id='btn-add')
        )()

    def GET(self):
        global all_categories
        force_login(sess)
        return ltpl('addpinurl', self.make_form(all_categories))

    def upload_image(self, url):
        fname = generate_salt()
        ext = os.path.splitext(url)[1].lower()

        urllib.urlretrieve(url, 'static/tmp/%s%s' % (fname, ext))
        if ext != '.png':
            img = Image.open('static/tmp/%s%s' % (fname, ext))
            img.save('static/tmp/%s.png' % fname)

        img = Image.open('static/tmp/%s.png' % fname)
        width, height = img.size
        ratio = 202 / width
        width = 202
        height *= ratio
        img.thumbnail((width, height), Image.ANTIALIAS)
        img.save('static/tmp/pinthumb%s.png' % fname)

        return fname
    
    def POST(self):
        force_login(sess)
        form = self.make_form()
        if not form.validates():
            return 'shit done fucked up'

        fname = self.upload_image(form.d.url)

        link = form.d.link
        if '://' not in link:
            link = 'http://%s' % link

        pin_id = db.insert('pins',
            description=form.d.description,
            user_id=sess.user_id,
            category=form.d.category,
            link=link)

        if form.d.tags:
            tags = ' '.join([make_tag(x) for x in form.d.tags.split(' ')])
            db.insert('tags', pin_id=pin_id, tags=tags)

        os.rename('static/tmp/%s.png' % fname,
                  'static/tmp/%d.png' % pin_id)
        os.rename('static/tmp/pinthumb%s.png' % fname,
                  'static/tmp/pinthumb%d.png' % pin_id)
        raise web.seeother('/pin/%d' % pin_id)


class PageRepin:
    def make_form(self, pin=None, categories=None):
        categories = categories or []
        categories = [(x.id, x.name) for x in categories]
        
        if pin is None:
            return form.Form(
                form.Textarea('description'),
                form.Dropdown('category', categories),
                form.Textbox('tags', description='tags (optional)', placeholder='#this #is #awesome'),
                form.Button('add to getlist')
            )()
        return form.Form(
            form.Textarea('description', value=pin.description),
            form.Dropdown('category', categories),
            form.Textbox('tags', description='tags (optional)', placeholder='#this #is #awesome'),
            form.Button('add to getlist')
        )()

    def GET(self, pin_id):
        global all_categories

        force_login(sess)

        pin_id = int(pin_id)
        pin = dbget('pins', pin_id)
        if pin is None:
            return 'pin doesn\'t exist'

        return ltpl('repin', pin, self.make_form(pin, all_categories))

    def POST(self, pin_id):
        force_login(sess)

        pin_id = int(pin_id)
        pin = dbget('pins', pin_id)
        if pin is None:
            return 'pin doesn\'t exist'
        
        if pin.repin:
            pin_id = pin.repin

        form = self.make_form()
        if not form.validates():
            return 'shit done fucked up'

        pin_id = db.insert('pins',
            description=form.d.description,
            user_id=sess.user_id,
            category=form.d.category,
            repin=pin_id)

        if form.d.tags:
            tags = ' '.join([make_tag(x) for x in form.d.tags.split(' ')])
            db.insert('tags', pin_id=pin_id, tags=tags)

        make_notif(pin.user_id, 'Someone has added your item to their Getlist!', '/pin/%d' % pin_id)
        raise web.seeother('/pin/%d' % pin_id)


countries = [
    'United States', 'Canada', 'Afghanistan', 'Aland Islands', 'Albania', 'Algeria', 'American Samoa', 'Andorra', 'Angola', 'Anguilla', 'Antarctica', 'Antigua and Barbuda', 'Argentina', 'Armenia', 'Aruba', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh',
    'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bermuda', 'Bhutan', 'Bolivia, Plurinational State of', 'Bonaire, Sint Eustatius and Saba', 'Bosnia and Herzegovina', 'Botswana', 'Bouvet Island', 'Brazil', 'British Indian Ocean Territory',
    'Brunei Darussalam', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon', 'Cape Verde', 'Cayman Islands', 'Central African Republic', 'Chad', 'Chile',
    'China', 'Christmas Island', 'Cocos (keeling) Islands', 'Colombia', 'Comoros', 'Congo', 'Congo, Democratic Republic of The', 'Cook Islands', 'Costa Rica', 'Cote Divoire',
    'Croatia', 'Cuba', 'Curacao', 'Cyprus', 'Czech Republic', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Ethiopia', 'Falkland Islands (malvinas)', 'Faroe Islands', 'Fiji', 'Finland',
    'France', 'French Guiana', 'French Polynesia', 'French Southern Territories', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Gibraltar', 'Greece', 'Greenland', 'Grenada', 'Guadeloupe', 'Guam', 'Guatemala', 'Guernsey', 'Guinea', 'Guinea-bissau', 'Guyana', 'Haiti', 'Heard Island and Mcdonald Islands', 'Holy See (Vatican City State)', 'Honduras',
    'Hong Kong', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq', 'Ireland', 'Isle of Man', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jersey', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati', 'Korea, North', 'Korea, South',
    'Kuwait', 'Kyrgyzstan', 'Lao People&#;s Democratic Republic', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Macao', 'Macedonia', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Martinique', 'Mauritania',
    'Mauritius', 'Mayotte', 'Mexico', 'Micronesia, Federated States of', 'Moldova, Republic of', 'Monaco', 'Mongolia', 'Montenegro', 'Montserrat', 'Morocco',
    'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal',
    'Netherlands', 'New Caledonia', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Niue', 'Norfolk Island',
    'Northern Mariana Islands', 'Norway', 'Oman', 'Pakistan', 'Palau', 'Palestinian Territory', 'Panama', 'Papua New Guinea', 'Paraguay',
    'Peru', 'Philippines', 'Pitcairn', 'Poland', 'Portugal', 'Puerto Rico', 'Qatar', 'Reunion', 'Romania', 'Russian Federation', 'Rwanda',
    'Samoa', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore', 'Sint Maarten (dutch Part)', 'Slovakia', 'Slovenia', 'Solomon Islands', 'Somalia',
    'South Africa', 'South Georgia', 'South Sudan', 'Spain', 'Sri Lanka', 'St. Barthelemy', 'St. Helena', 'St. Kitts And Nevis', 'St. Lucia', 'St. Martin (french Part)', 'St. Pierre And Miquelon', 'St. Vincent And The Grenadines', 'Sudan', 'Suriname', 'Svalbard and Jan Mayen', 'Swaziland', 'Sweden', 'Switzerland', 'Syrian Arab Republic', 'Taiwan, Province of China',
    'Tajikistan', 'Tanzania, United Republic of', 'Thailand', 'Timor-leste', 'Togo', 'Tokelau', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Turks and Caicos Islands', 'Tuvalu', 'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States Minor Outlying Islands', 'Uruguay',
    'Uzbekistan', 'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam',
    'Virgin Islands, British', 'Virgin Islands, U.s.', 'Wallis and Futuna', 'Western Sahara', 'Yemen', 'Zambia', 'Zimbabwe',
]


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
        return ltpl('editprofile', user, countries, name)

    def POST(self, name=None):
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'you need to fill in everything'

        db.update('users', where='id = $id',
            name=form.d.name, about=form.d.about, username=form.d.username,
            zip=(form.d.zip or None), website=form.d.website, country=form.d.country,
            hometown=form.d.hometown, city=form.d.city,
            vars={'id': sess.user_id})

        raise web.seeother('/settings/profile')


class PageChangeEmail:
    _form = form.Form(
        form.Textbox('email'))

    def POST(self):
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'you need to fill in everything'

        db.update('users', where='id = $id', vars={'id': sess.user_id}, email=form.d.email)
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


class PagePin2:
    def GET(self, pin_id):
        raise web.seeother('/item/%s' % pin_id)


class PagePin:
    _form = form.Form(
        form.Textarea('comment'))

    def GET(self, pin_id):
        pin_id = int(pin_id)

        logged = logged_in(sess)
        query1 = '(not count(distinct likes) = 0)' if logged else 'false'
        query2 = 'left join likes on likes.user_id = $uid and likes.pin_id = pins.id' if logged else ''

        qvars = {'id': pin_id, 'uid': 0}
        if logged:
            qvars['uid'] = sess.user_id

        pin = db.query('''
            select
                tags.tags, pins.*, users.name as user_name, categories.name as cat_name, users.pic as user_pic, users.username as user_username,
                ''' + query1 + ''' as liked,
                count(distinct l2) as likes,
                count(distinct p1) as repin_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join categories on categories.id = pins.category
                ''' + query2 + '''
                left join likes l2 on l2.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
            where pins.id = $id and (not users.private or pins.user_id = $uid)
            group by pins.id, tags.tags, users.id, categories.id''', vars=qvars)
        if not pin:
            return 'pin not found'

        pin = pin[0]
        if not pin.category:
            return 'pin not found'

        if logged and sess.user_id != pin.user_id:
            db.update('pins', where='id = $id', vars={'id': pin_id}, views=web.SQLLiteral('views + 1'))

        comments = db.query('''
            select
                comments.*, users.pic as user_pic, users.username as user_username, users.name as user_name
            from comments
                join users on users.id = comments.user_id
            where pin_id = $id
            order by timestamp asc''', vars={'id': pin_id})

        rating = db.select('ratings', what='avg(rating)',
                            where='pin_id = $id', vars={'id': pin_id})
        if not rating:
            return 'could not get rating'

        rating = rating[0]
        if not rating.avg:
            rating.avg = 0
                
        rating = round(float(rating.avg), 2)
        return ltpl('pin', pin, comments, rating)

    def POST(self, pin_id):
        force_login(sess)

        pin = dbget('pins', pin_id)
        if not pin:
            return 'pin does not exist'

        pin_id = int(pin_id)
        form = self._form()
        if not form.validates():
            return 'form did not validate'

        if not form.d.comment:
            return 'please write a comment'

        db.insert('comments',
                  pin_id=pin_id,
                  user_id=sess.user_id,
                  comment=form.d.comment)

        if int(pin.user_id) != int(sess.user_id):
            make_notif(pin.user_id, 'Someone has commented on your pin!', '/pin/%d' % pin_id)

        raise web.seeother('/pin/%d' % pin_id)


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
                tags.tags, pins.*, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join users on users.id = pins.user_id
                left join tags on tags.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join categories on categories.id = pins.category
            where pins.category = $cid and not users.private
            group by pins.id, tags.tags, users.id, categories.id
            offset %d limit %d''' % (offset * PIN_COUNT, PIN_COUNT),
            vars={'cid': cid})

        if ajax:
            return json_pins(pins)
        return ltpl('board', user, category, pins)


def get_pins(user_id, offset=None, limit=None, show_private=False):
    query = '''
        select
            tags.tags, pins.*, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
            count(distinct p1) as repin_count,
            count(distinct l1) as like_count
        from users
            left join pins on pins.user_id = users.id
            left join tags on tags.pin_id = pins.id
            left join pins p1 on p1.repin = pins.id
            left join likes l1 on l1.pin_id = pins.id
            left join categories on categories.id = pins.category
        where users.id = $id ''' + ('' if show_private else 'and not users.private') + '''
        group by categories.id, tags.tags, pins.id, users.id
        order by timestamp desc'''

    if offset is not None:
        query += ' offset %d' % offset
    if limit is not None:
        query += ' limit %d' % limit

    return db.query(query, vars={'id': user_id})


class PageProfile:
    def GET(self, user_id):
        user_id = int(user_id)

        user = dbget('users', user_id)
        if not user:
            return 'User not found.'
        
        raise web.seeother('/' + user.username)


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

        is_logged_in = logged_in(sess)

        if is_logged_in and sess.user_id != user.id:
            db.update('users', where='id = $id', vars={'id': user.id}, views = web.SQLLiteral('views + 1'))

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
            photos = db.select('photos', where='album_id = $id', vars={'id': sess.user_id},  order="id DESC")


            return ltpl('profile', user, pins, offset, PIN_COUNT, hashed, friend_status, is_following, photos)
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


MAX_IMAGES = 10


def get_url_info(contents, base_url):
    links = re.findall(r'<img.*?src\=\"([^\"]*)\"', contents, re.DOTALL)
    # soup = BeautifulSoup(contents)
    # links = [x['src'] for x in soup.find_all('img')]
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
        except:
            return json.dumps({'status': 'error'})


class PageLike:
    def GET(self, pin_id):
        force_login(sess)
        pin_id = int(pin_id)

        try:
            db.insert('likes', user_id=sess.user_id, pin_id=pin_id)
        except:
            pass
        raise web.seeother('/pin/%d' % pin_id)


class PageUnlike:
    def GET(self, pin_id):
        force_login(sess)
        pin_id = int(pin_id)

        db.delete('likes', where='user_id = $uid and pin_id = $pid',
                  vars={'uid': sess.user_id, 'pid': pin_id})
        raise web.seeother('/pin/%d' % pin_id)


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
        form.Textbox('new1'),
        form.Textbox('new2')
    )

    def POST(self):
        force_login(sess)

        form = self._form()
        if not form.validates():
            return 'bad input'

        user = dbget('users', sess.user_id)
        if not user:
            return 'error getting user'

        if form.d.new1 != form.d.new2:
            return 'Your passwords don\'t match!'

        if not form.d.new1:
            return 'Your password cannot be blank.'

        if hash(hash(form.d.old) + user.pw_salt) != user.pw_hash:
            return 'Your old password did not match!'

        pw_hash = hash(form.d.new1)
        pw_hash = hash(pw_hash + user.pw_salt)
        db.update('users', where='id = $id', vars={'id': sess.user_id},
                  pw_hash=pw_hash)
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

        album = dbget('albums', aid)
        if album.user_id != sess.user_id:
            return 'Album not found.'

        photos = db.select('photos', where='album_id = $id', vars={'id': aid})
        return ltpl('album', album, photos)


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
            new_photo = db.select('photos',where="album_id=%s"%(sess.user_id), order='id DESC', limit=1)
            if new_photo:
                db.update('users', where='id = $id', vars={'id': sess.user_id}, pic=new_photo[0].id)            
        return web.redirect('/%s' % (user.username))


class PageSetProfilePic:
    def GET(self, pid):
        force_login(sess)
        pid = int(pid)

        photo = db.query('''
            select albums.user_id from photos
                join albums on albums.id = photos.album_id
            where photos.id = $id''', vars={'id': pid})
        if not photo:
            return 'no such photo'

        photo = photo[0]
        if photo.user_id != sess.user_id:
            return 'no such photo'

        db.update('users', where='id = $id', vars={'id': sess.user_id}, pic=pid)
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
                tags.tags, pins.*, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1.id) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join categories on categories.id = pins.category
            where pins.category = $cid and not users.private
            group by tags.tags, categories.id, pins.id, users.id order by timestamp desc limit %d offset %d''' % (PIN_COUNT, offset * PIN_COUNT)

        pins = list(db.query(query, vars={'cid': cid}))
        return ltpl('category', pins, category, name, offset, PIN_COUNT)


def atpl(*params, **kwargs):
    if 'phase' not in kwargs:
        raise Exception('phase needed in atpl')
    return tpl('asignup', tpl(*params), kwargs['phase'])

class PageAfterSignup:
    def phase1(self):
        global all_categories

        return atpl('aphase1', all_categories, phase=1)

    _form1 = form.Form(form.Hidden('ids'))

    def phase2(self):
        form = self._form1()
        form.validates()
        ids = map(str, map(int, form.d.ids.split(',')))

        users = db.query('''
            select
                users.*,
                count(distinct pins) as pin_count
            from users
                left join pins on pins.user_id = users.id
            where pins.category in (%s)
            group by users.id
            order by pin_count desc
            limit 10''' % ', '.join(ids))
        return atpl('aphase2', users, phase=2)

    def phase_post_2(self):
        try:
            form = self._form1()
            form.validates()
            ids = map(str, map(int, form.d.ids.split(',')))

            print ids
            if len(ids) > 10:
                ids = ids[:10]

            follows = [{'follow': x, 'follower': sess.user_id} for x in ids]
            db.multiple_insert('follows', follows)
        except:
            pass
        raise web.seeother('/after-signup/3')

    def phase3(self):
        return atpl('aphase3', phase=3)

    def GET(self, phase=None):
        force_login(sess)
        phase = int(phase or 1)
        try:
            return getattr(self, 'phase%d' % phase)()
        except AttributeError as e:
            raise web.notfound()

    def POST(self, phase=None):
        force_login(sess)
        phase = int(phase or 1)

        try:
            return getattr(self, 'phase_post_%d' % phase)()
        except AttributeError:
            raise web.notfound()


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


class PageChangeBGPos:
    _form = form.Form(
        form.Textbox('x'),
        form.Textbox('y'))

    def POST(self):
        force_login(sess)

        form = self._form()
        form.validates()

        db.update('users', where='id=$id', vars={'id':sess.user_id}, bgx=form.d.x, bgy=form.d.y)
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
        #album = db.select('albums', where='user_id = $uid and name = $name', vars={'uid': sess.user_id, 'name': 'Profile Pictures'})
        #if album:
        #    aid = album[0].id
        #else:
        #    aid = db.insert('albums', name='Profile Pictures', user_id=sess.user_id)

        pid = db.insert('photos', album_id=sess.user_id)
        self.upload_image(pid)
        db.update('users', where='id = $id', vars={'id': sess.user_id}, pic=pid)
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
        raise web.seeother('/pin/%d' % pin_id)


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
            where = 'pins.category = $cid'

        query = '''
            select
                tags.tags, pins.*, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                count(distinct p1) as repin_count,
                count(distinct l1) as like_count
            from pins
                left join tags on tags.pin_id = pins.id
                left join pins p1 on p1.repin = pins.id
                left join likes l1 on l1.pin_id = pins.id
                left join users on users.id = pins.user_id
                left join follows on follows.follow = users.id
                left join categories on categories.id = pins.category
            where ''' + where + '''
            group by tags.tags, categories.id, pins.id, users.id
            order by timestamp desc offset %d limit %d''' % (offset * PIN_COUNT, PIN_COUNT)

        pins = db.query(query, vars={'cid': cid})
        if ajax:
            return json_pins(pins, 'horzpin')
        return ltpl('category', pins, category, all_categories)


class PageResendActivation:
    def GET(self):
        force_login(sess)

        user = dbget('users', sess.user_id)
        if not user:
            raise web.seeother('/')

        if user.activation == 0:
            raise web.seeother('/')

        hashed = hash(str(user.activation))
        send_activation_email(user.email, hashed, user.id)
        return lmsg('An email has been resent. <a href="/"><b>Back</b></a> |  <a href=""><b>Send another one</b></a>')

    
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
                tags.tags, pins.*, categories.name as cat_name, users.pic as user_pic, users.username as user_username, users.name as user_name,
                ts_rank_cd(to_tsvector(tags.tags), query) as rank1,
                ts_rank_cd(pins.tsv, query) as rank2
            from pins 
                left join tags on tags.pin_id = pins.id
                join to_tsquery('""" + q + """') query on true
                left join users on users.id = pins.user_id
                left join follows on follows.follow = users.id
                left join categories on categories.id = pins.category
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


if __name__ == '__main__':
    app.run()
