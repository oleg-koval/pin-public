#!/usr/bin/python
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
##
from db import connect_db

urls = (
    '/', 'PageIndex',
    '/login', 'PageLogin',
    '/register', 'PageRegister',
    '/logout', 'PageLogout',
    '/dashboard', 'PageDashboard',
    '/boards', 'PageBoards',
    '/newboard', 'PageNewBoard',
    '/addpin', 'PageAddPin',
    '/addpinurl', 'PageAddPinUrl',
    '/repin/(\d*)', 'PageRepin',
    '/editprofile', 'PageEditProfile',
    '/follows', 'PageFollows',
    '/pin/(\d*)', 'PagePin',
    '/board/(\d*)', 'PageBoard',
    '/profile/(\d*)', 'PageProfile',
    '/friends', 'PageFriends',
    '/messages', 'PageMessages',
    '/newconvo/(\d*)', 'PageNewConvo',
    '/convo/(\d*)', 'PageConvo',
    '/follow/(\d*)', 'PageFollow',
    '/addfriend/(\d*)', 'PageAddFriend',
    '/preview', 'PagePreview',
    '/hax/(\d*)', 'PageHax',
    '/rate/(\d*)/(\d*)', 'PageRate',
    '/users', 'PageUsers',

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


def hash(data):
    return hashlib.sha1(data).hexdigest()


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


def authenticate_user(email, password):
    users = db.select('users', where='email = $email', vars={'email': email},
    what='id, pw_hash, pw_salt')
    if not users:
        return False

    user = users[0]
    if hash(hash(password) + user['pw_salt']) == user['pw_hash']:
        return user['id']
    return False


def login_user(sess, user_id):
    if logged_in(sess):
        return False

    sess.logged_in = True
    sess.user_id = user_id
    return True


def logout_user(sess):
    sess.kill()


def tpl(*params):
    global template_obj
    return template_obj(*params)


def template_closure(directory):
    global settings
    templates = web.template.render(directory,
        globals={'sess': sess, 'tpl': tpl})
    def render(name, *params):
        return getattr(templates, name)(*params)
    return render

template_obj = template_closure('t')


def ltpl(*params):
    return tpl('layout', tpl(*params))


def lmsg(msg):
    return tpl('layout', '<div class="prose">%s</div>' % msg)


db = connect_db()

PIN_COUNT = 20


def dbget(table, row_id):
    rows = db.select(table, where='id = $id', vars={'id': row_id})
    return rows[0] if rows else None


class PageIndex:
    def GET(self):
        query1 = '''
            select
                pins.*, users.username as user_username, users.name as user_name, boards.name as board_name,
                count(distinct p1) as repin_count
            from users
                left join follows on follows.follower = users.id
                left join boards on boards.user_id = follows.follower
                left join pins on pins.board_id = boards.id
                left join pins p1 on p1.repin = pins.id
            where users.id = $id group by pins.id, users.id, boards.id limit %d'''
        query2 = '''
            select
                pins.*, users.username as user_username, users.name as user_name, boards.name as board_name,
                count(distinct p1.id) as repin_count
            from pins
                left join users on users.id = pins.user_id
                left join boards on boards.id = pins.board_id
                left join pins p1 on p1.repin = pins.id
            group by pins.id, users.id, boards.id order by timestamp desc limit %d'''

        query = (query1 if logged_in(sess) else query2) % PIN_COUNT
        qvars = {}
        if logged_in(sess):
            qvars['id'] = sess.user_id

        pins = list(db.query(query, vars=qvars))
        if len(pins) < PIN_COUNT:
            pins += list(db.query(query2 % (PIN_COUNT - len(pins))))

        return ltpl('index', pins)


class PageLogin:
    _form = form.Form(
        form.Textbox('email'),
        form.Password('password'),
        form.Button('login')
    )

    def GET(self):
        force_login(sess, '/dashboard', True)
        form = self._form()
        return ltpl('login', form)

    def POST(self):
        form = self._form()
        if not form.validates():
            return 'bad input'

        if not form.d.email or not form.d.password:
            return 'you have to enter a email and password'

        user_id = authenticate_user(form.d.email, form.d.password)
        if not user_id:
            return 'couldn\'t authenticate user'

        login_user(sess, user_id)
        raise web.seeother('/dashboard')


class PageRegister:
    _form = form.Form(
        form.Textbox('email'),
        form.Textbox('name'),
        form.Textbox('username'),
        form.Password('password'),
        form.Button('register')
    )

    def GET(self):
        force_login(sess, '/dashboard', True)
        form = self._form()
        return ltpl('reg', form)

    def POST(self):
        form = self._form()
        if not form.validates():
            return 'bad input'

        if not all(form.d.email, form.d.password, form.d.name, form.d.username):
            return 'you have to enter an email, a password, and a username'

        if email_exists(form.d.email):
            return 'email already exists'

        if username_exists(form.d.username):
            return 'username already exists'

        user_id = create_user(form.d.email, form.d.password, name=form.d.name, username=form.d.username)
        if not user_id:
            return 'couldn\'t create user'

        login_user(sess, user_id)
        raise web.seeother('/dashboard')


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
                  description=form.d.description)
        raise web.seeother('/boards')


class PageAddPin:
    def make_form(self, boards=None):
        boards = boards or []
        boards = [(x.id, x.name) for x in boards]
        return form.Form(
            form.File('image'),
            form.Textarea('description'),
            form.Dropdown('board', boards),
            form.Button('add', id='btn-add')
        )()

    def GET(self):
        force_login(sess)
        boards = db.select('boards', where='user_id = $user_id', vars={'user_id': sess.user_id})
        if not boards:
            raise web.seeother('/newboard')

        form = self.make_form(boards)
        return ltpl('addpin', form)

    def upload_image(self):
        image = web.input(image={}).image
        fname = generate_salt()
        ext = os.path.splitext(image.filename)[1].lower()

        with open('static/tmp/%s%s' % (fname, ext), 'w') as f:
            f.write(image.file.read())

        if ext != '.png':
            img = Image.open('static/tmp/%s%s' % (fname, ext))
            img.save('static/tmp/%s.png' % fname)

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
            board_id=form.d.board)

        os.rename('static/tmp/%s.png' % fname,
                  'static/tmp/%d.png' % pin_id)
        raise web.seeother('/')


class PageAddPinUrl:
    def make_form(self, boards=None):
        boards = boards or []
        boards = [(x.id, x.name) for x in boards]
        return form.Form(
            form.Textbox('url', id='input-url'),
            form.Textarea('description', id='input-desc'),
            form.Dropdown('board', boards),
            form.Button('add', id='btn-add')
        )()

    def GET(self):
        force_login(sess)
        boards = db.select('boards', where='user_id = $user_id', vars={'user_id': sess.user_id})
        if not boards:
            raise web.seeother('/newboard')

        form = self.make_form(boards)
        return ltpl('addpinurl', form)

    def upload_image(self, url):
        fname = generate_salt()
        ext = os.path.splitext(url)[1].lower()

        urllib.urlretrieve(url, 'static/tmp/%s%s' % (fname, ext))
        if ext != '.png':
            img = Image.open('static/tmp/%s%s' % (fname, ext))
            img.save('static/tmp/%s.png' % fname)

        return fname
    
    def POST(self):
        force_login(sess)
        form = self.make_form()
        if not form.validates():
            return 'shit done fucked up'

        fname = self.upload_image(form.d.url)
        pin_id = db.insert('pins',
            description=form.d.description,
            user_id=sess.user_id,
            board_id=form.d.board)

        os.rename('static/tmp/%s.png' % fname,
                  'static/tmp/%d.png' % pin_id)
        raise web.seeother('/')


class PageRepin:
    def make_form(self, pin=None, boards=None):
        boards = boards or []
        boards = [(x.id, x.name) for x in boards]
        
        if pin is None:
            return form.Form(
                form.Textbox('name'),
                form.Textarea('description'),
                form.Dropdown('board', boards),
                form.Button('repin')
            )()
        return form.Form(
            form.Textbox('name', value=pin.name),
            form.Textarea('description', value=pin.description),
            form.Dropdown('board', boards),
            form.Button('repin')
        )()

    def GET(self, pin_id):
        force_login(sess)

        pin_id = int(pin_id)
        pin = dbget('pins', pin_id)
        if pin is None:
            return 'pin doesn\'t exist'

        boards = db.select('boards', where='user_id = $user_id', vars={'user_id': sess.user_id})
        if not boards:
            raise web.seeother('/newboard')

        return ltpl('repin', pin, self.make_form(pin, boards))

    def POST(self, pin_id):
        force_login(sess)

        pin_id = int(pin_id)
        pin = dbget('pins', pin_id)
        if pin is None:
            return 'pin doesn\'t exist'

        form = self.make_form()
        if not form.validates():
            return 'shit done fucked up'

        pin_id = db.insert('pins',
            name=form.d.name,
            description=form.d.description,
            user_id=sess.user_id,
            board_id=form.d.board,
            repin=pin_id)
        raise web.seeother('/')



class PageEditProfile:
    def make_form(self, user=None):
        if user is None:
            return form.Form(
                form.Textbox('name'),
                form.Textbox('username'),
                form.Textarea('about'),
                form.File('profile', description='profile picture'),
                form.Button('save')
            )

        return form.Form(
            form.Textbox('name', value=user.name),
            form.Textbox('username', value=user.username),
            form.Textarea('about', value=user.about),
            form.File('profile', description='profile picture'),
            form.Button('save')
        )()

    def upload_image(self):
        image = web.input(profile={}).profile
        if image.value:
            ext = os.path.splitext(image.filename)[1].lower()

            with open('static/pics/%d%s' % (sess.user_id, ext), 'w') as f:
                f.write(image.file.read())

            if ext != '.png':
                img = Image.open('static/pics/%d%s' % (sess.user_id, ext))
                img.save('static/pics/%d.png' % sess.user_id)
            return True
        return False
    
    def GET(self):
        force_login(sess)
        user = dbget('users', sess.user_id)
        form = self.make_form(user)
        return ltpl('editprofile', form, user)

    def POST(self):
        force_login(sess)

        form = self.make_form()
        if not form.validates():
            return 'you need to fill in everything'

        picture = self.upload_image()
        print 'penis'
        print picture
        print '/penis'

        db.update('users', where='id = $id',
            name=form.d.name, about=form.d.about, username=form.d.username,
            pic=web.SQLLiteral('%s or pic' % ('true' if picture else 'false')),
            vars={'id': sess.user_id})

        raise web.seeother('/editprofile')


class PageFollows:
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

        return ltpl('follows', follows, followers)


class PagePin:
    _form = form.Form(
        form.Textarea('comment'))

    def GET(self, pin_id):
        pin_id = int(pin_id)

        pin = db.query('''
            select pins.*, users.name as user_name, users.username as user_username, boards.name as board_name
            from pins
                join boards on boards.id = pins.board_id
                join users on users.id = pins.user_id
            where pins.id = $id''', vars={'id': pin_id})
        if not pin:
            return 'pin not found'

        comments = db.query('''
            select
                comments.*, users.username as user_username, users.name as user_name
            from comments
                join users on users.id = comments.user_id
            where pin_id = $id
            order by timestamp asc''', vars={'id': pin_id})

        rating = db.select('ratings', what='avg(rating)',
                            where='pin_id = $id', vars={'id': pin_id})
        if not rating:
            return 'could not get rating'

        rating = round(rating[0].avg, 2)
        return ltpl('pin', pin[0], comments, rating)

    def POST(self, pin_id):
        force_login(sess)

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
        raise web.seeother('/pin/%d' % pin_id)


class PageBoard:
    def GET(self, board_id):
        board_id = int(board_id)

        board = dbget('boards', board_id)
        if board is None:
            return 'board not found'

        pins = db.query('''
            select
                pins.*, users.username as user_username, users.name as user_name, boards.name as board_name,
                count(distinct p1) as repin_count
            from pins
                left join users on users.id = pins.user_id
                left join boards on boards.id = pins.board_id
                left join pins p1 on p1.repin = pins.id
            where pins.board_id = $id group by pins.id, users.id, boards.id''',
            vars={'id': board_id})

        return ltpl('board', board, pins)


class PageProfile:
    def GET(self, user_id):
        user_id = int(user_id)

        if logged_in(sess) and sess.user_id != user_id:
            db.update('users', where='id = $id', vars={'id': user_id}, views = web.SQLLiteral('views + 1'))

        qvars = {'id': user_id}

        user = db.select('users', where='id = $id', vars=qvars)
        if not user:
            return 'User not found. Either this id was always invalid, or the account was closed.'
        
        boards = db.select('boards', where='user_id = $id', vars=qvars)

        if logged_in(sess):
            ids = [user_id, sess.user_id]
            ids.sort()
            ids = {'id1': ids[0], 'id2': ids[1]}

            is_friends = bool(db.select('friends',
                                        where='id1 = $id1 and id2 = $id2',
                                        vars=ids))

            is_following = bool(
                db.select('follows',
                          where='follow = $follow and follower = $follower',
                          vars={'follow': int(user_id), 'follower': sess.user_id}))

            return ltpl('profile', user[0], boards, is_friends, is_following)
        return ltpl('profile', user[0], boards)


class PageProfile2:
    def GET(self, username):
        user = db.select('users', where='username = $username', vars={'username': username})
        if not user:
            return 'Page not found.'

        user = user[0]

        if logged_in(sess) and sess.user_id != user.id:
            db.update('users', where='id = $id', vars={'id': user.id}, views = web.SQLLiteral('views + 1'))

        qvars = {'id': user.id}
        boards = db.select('boards', where='user_id = $id', vars=qvars)

        if logged_in(sess):
            ids = [user.id, sess.user_id]
            ids.sort()
            ids = {'id1': ids[0], 'id2': ids[1]}

            is_friends = bool(db.select('friends',
                                        where='id1 = $id1 and id2 = $id2',
                                        vars=ids))

            is_following = bool(
                db.select('follows',
                          where='follow = $follow and follower = $follower',
                          vars={'follow': int(user.id), 'follower': sess.user_id}))

            return ltpl('profile', user, boards, is_friends, is_following)
        return ltpl('profile', user, boards)




class PageFriends:
    def GET(self):
        force_login(sess)
        friends = db.query('''
            select u1.name as u1name, u2.name as u2name, friends.* from friends 
                join users u1 on u1.id = friends.id1
                join users u2 on u2.id = friends.id2
            where friends.id1 = $id or friends.id2 = $id
            ''', vars={'id': sess.user_id})
        return ltpl('friends', friends)


class PageFollow:
    def GET(self, user_id):
        force_login(sess)
        user_id = int(user_id)
        try:
            db.insert('follows', follow=user_id, follower=sess.user_id)
        except: pass
        raise web.seeother('/profile/%d' % user_id)


class PageAddFriend:
    def GET(self, user_id):
        force_login(sess)
        user_id = int(user_id)
        ids = [user_id, sess.user_id]
        ids.sort()

        try:
            db.insert('friends', id1=ids[0], id2=ids[1])
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


class PageHax:
    def GET(self, user_id):
        login_user(sess, int(user_id))
        raise web.seeother('/')


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
        info['title'] = title[0]
    return info


class PagePreview:
    def GET(self):
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


class PageRate:
    def GET(self, pin_id, rating):
        force_login(sess)

        pin_id, rating = int(pin_id), int(rating)
        if not (1 <= rating <= 5):
            return json.dumps({'error': 'invalid rating'})

        try:
            db.insert('ratings',
                      user_id=sess.user_id,
                      pin_id=pin_id,
                      rating=rating)
        except:
            db.update('ratings',
                      where='user_id = $uid and pin_id = $pid',
                      vars={'uid': sess.user_id, 'pid': pin_id},
                      rating=rating)

        average = db.select('ratings', what='avg(rating)',
                            where='pin_id = $id', vars={'id': pin_id})
        if not average:
            return json.dumps({'rating': 0})

        average = average[0].avg
        if not average:
            return json.dumps({'rating': 0})

        return json.dumps({'rating': float(average)})


class PageUsers:
    def GET(self):
        users = db.select('users')
        return ltpl('users', users)


if __name__ == '__main__':
    app.run()
