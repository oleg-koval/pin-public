import web
import os

from api.utils import api_response, save_api_request
from api.entities import UserProfile

from api.views.base import BaseAPI
from mypinnings.database import connect_db
import facebook
import urllib
import requests

db = connect_db()


class PostingOnUserPage(BaseAPI):
    """
    Provides sharing pins to social networks

    Method PostingOnUserPage must receive next required params:

    share_list - list of pin's ids
    access_token - access token for social network
    social_network - name of social network (for example "facebook")
    """
    def POST(self):
        """
        Share pins to social network
        """
        request_data = web.input(
            share_list=[],
        )

        # Get data from request
        share_list = map(int, request_data.get("share_list"))
        access_token = request_data.get("access_token")
        social_network = request_data.get("social_network")
        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']

        # Initialize default posted pins list
        posted_pins = []
        # Setting default status code as 200
        status = 200
        # Setting empty error
        error_code = ""

        # Check input data and set appropriate code if not valid
        if not access_token or not social_network:
            status = 400
            error_code = "Invalid input data"
        else:
            posted_pins, status, error_code = share(
                access_token,
                share_list,
                social_network,
            )

        # Setting data for return
        data = {
            "posted_pins": posted_pins
        }

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


def share(access_token, share_list, social_network="facebook"):
    """
    Share pins to social network, using access token
    """
    # Initialize default access token status
    access_token_status = True

    # Get status of access token for social network
    if social_network == "facebook":
        access_token_status = check_facebook_access_token(access_token)
    if social_network == "linkedin":
        access_token_status = check_linkedin_access_token(access_token)

    if not access_token_status:
        return [], 400, "Bad access token for social network"

    # Initialize shared pins list
    shared_pins = []

    for pin_id in share_list:
        pin = db.select('pins', vars={'id': pin_id}, where='id=$id')

        if len(pin) == 0:
            continue

        pin = pin[0]
        message = ""
        link = ""

        if pin.get('name'):
            message += pin.get('name') + "\n"
        if pin.get('description'):
            message += pin.get('description') + "\n"
        if pin.get('price'):
            message += "Price: " + pin.get('price') + "\n"
        if pin.get('link'):
            link = pin.get('link')

        image_url = pin.get('image_url')

        share_pin_status = False
        if social_network == "facebook":
            share_pin_status = share_via_facebook(access_token,
                                                  message,
                                                  link,
                                                  image_url)

        if social_network == "linkedin":
            share_pin_status = share_via_linkedin(access_token,
                                                  message,
                                                  link,
                                                  image_url)

        if share_pin_status:
            shared_pins.append(pin_id)

    return shared_pins, 200, ""


def check_facebook_access_token(access_token):
    try:
        graph = facebook.GraphAPI(access_token)
        profile = graph.get_object("me")
        return True
    except facebook.GraphAPIError, exc:
        return False


def check_linkedin_access_token(access_token):
    try:
        url = 'https://api.linkedin.com/v1/people/~' + \
            '?oauth2_access_token=%s' % access_token

        result = requests.get(url)

        if result.status_code == 200:
            return True
        else:
            return False
    except Exception, exc:
        return False


def share_via_facebook(access_token, message, link, image_url):
    """
    Share pin to facebook
    """
    if link:
        message += link + "\n"

    try:
        graph = facebook.GraphAPI(access_token)
        if image_url:
            graph.put_photo(urllib.urlopen(image_url), message)
        else:
            graph.put_object("me", "feed", message=message)

        return True
    except Exception, exc:
        return False


def share_via_linkedin(access_token, message, link, image_url):
    """
    Share pin to Linkedin
    """
    try:
        url = 'https://api.linkedin.com/v1/people/~/shares' + \
            '?oauth2_access_token=%s' % access_token
        data = ""
        data += "<share>"
        data += "<content>"
        data += "<description>%s</description>" % message
        data += "<submitted-url>%s</submitted-url>" % link

        if image_url:
            data += "<submitted-image-url>%s</submitted-image-url>" % image_url

        data += "</content>"
        data += "<visibility>"
        data += "<code>anyone</code>"
        data += "</visibility>"
        data += "</share>"

        headers = {'content-type': 'application/xml'}

        result = requests.post(
            url,
            data=data,
            headers=headers
        )

        if result.status_code == 201:
            return True
        else:
            return False
    except Exception, exc:
        return False


class QueryFollows(BaseAPI):
    """
    Class responsible for providing access to followers of a given user
    """
    def POST(self, query_type):
        """ Depending on query_type (which can be follow or followers) returns
        a list of users (ids), following or followed by current user

        Can be tested this way:

        curl --data "csid_from_client=1&user_id=78&logintoken=RxPu7fLYgv" \
        http://localhost:8080/api/social/query/following
        returns all users who followed by user oleg

        curl --data "csid_from_client=1&user_id=78&logintoken=RxPu7fLYgv" \
        http://localhost:8080/api/social/query/followed-by
        returns all users who follow user oleg
        """

        data = web.input()
        uid = data.get("user_id")
        logintoken = data.get("logintoken", "")
        status, response_or_user = self.authenticate_by_token(logintoken)

        # Login was not successful
        if not status:
            return response_or_user
        if query_type == "followed-by":
            follows = UserProfile.query_followed_by(uid, response_or_user.id)
        else:
            follows = UserProfile.query_following(uid, response_or_user.id)
        csid_from_client = data.pop('csid_from_client')
        return api_response(data=follows, csid_from_client=csid_from_client,
                            csid_from_server="")


class SocialMessage(BaseAPI):
    """
    API method that sends message to user
    """
    def POST(self):
        request_data = web.input(
            user_id_list=[],
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        user_id_list = map(int,
                           request_data.get("user_id_list"))
        content = request_data.get("content")

        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        if not content:
            status = 400
            error_code = "Content cannot be empty"

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        from_user_id = user['id']

        if status == 200:
            for to_user_id in user_id_list:
                ids = sorted([to_user_id, from_user_id])
                convo = db.select('convos',
                                  where='id1 = $id1 and id2 = $id2',
                                  vars={'id1': ids[0], 'id2': ids[1]})\
                    .list()
                if convo:
                    convo_id = convo[0].id
                else:
                    convo_id = db.insert('convos', id1=ids[0], id2=ids[1])

                db.insert('messages', convo_id=convo_id, sender=from_user_id,
                          content=content)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


class SocialMessageToConversation(BaseAPI):
    """
    API method that sends message to conversation
    """
    def POST(self):
        request_data = web.input(
            conversation_id_list=[],
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        conversation_id_list = map(int,
                           request_data.get("conversation_id_list"))
        content = request_data.get("content")

        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        if not content:
            status = 400
            error_code = "Content cannot be empty"

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        from_user_id = user['id']

        if status == 200:
            for conversation_id in conversation_id_list:
                convo = db.select('convos',
                                  where='id = $id',
                                  vars={'id': conversation_id})\
                    .list()
                if len(convo) > 0:
                    db.insert('messages',
                              convo_id=conversation_id,
                              sender=from_user_id,
                              content=content)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


class SocialQueryConversations(BaseAPI):
    """
    API method that allows to get conversations
    """
    def POST(self):
        request_data = web.input(
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from 
        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        from_user_id = user['id']

        if status == 200:
            convos = db.query('''
                select convos.*, users.name from convos
                    join users on users.id = (case
                        when convos.id1 = $id then convos.id2
                        else convos.id1
                    end)
                where id1 = $id or id2 = $id''', vars={'id': from_user_id})\
                .list()
            if len(convos) > 0:
                data['conversations'] = convos
            else:
                data['conversations'] = []

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


class SocialQueryMessages(BaseAPI):
    """
    API method that allows to get messages from conversation
    """
    def POST(self):
        request_data = web.input(
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from 
        conversation_id = request_data.get('conversation_id', False)
        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        from_user_id = user['id']

        if not conversation_id:
            status = 400
            error_code = "conversation_id cannot be empty"

        if status == 200:
            convo = db.query('''
                select convos.id, users.id as user_id, users.name from convos
                    join users on users.id = (case
                        when convos.id1 = $id then convos.id2
                        else convos.id1
                    end)
                where (convos.id = $convo_id and
                       convos.id1 = $id or convos.id2 = $id)''',
                vars={'convo_id': conversation_id, 'id': from_user_id})\
                .list()
            if not convo:
                status = 400
                error_code = "conversation not found"
            else:
                data['conversation'] = convo[0]

                messages = db.query('''
                    select messages.*, users.name from messages
                        join users on users.id = messages.sender
                    where messages.convo_id = $convo_id''',
                    vars={'convo_id': conversation_id})\
                    .list()
                if len(messages) > 0:
                    data['messages'] = messages
                else:
                    data['messages'] = []

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


class AddCommentToPhoto(BaseAPI):
    """
    API method that adds comment to photo
    """
    def POST(self):
        request_data = web.input(
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        comment = request_data.get("comment")
        photo_id = request_data.get("photo_id")

        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)

        if not comment:
            status = 400
            error_code = "Comment cannot be empty"

        if not photo_id:
            status = 400
            error_code = "photo_id cannot be empty"

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        from_user_id = user['id']

        if status == 200:
            db.insert('profile_photo_comments',
                      photo_id=photo_id,
                      user_id=from_user_id,
                      comment=comment)

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


class LikeDislikePhoto(BaseAPI):
    """
    API method that adds likes to photo
    """
    def POST(self):
        request_data = web.input(
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from request
        photo_id = request_data.get("photo_id")
        action = request_data.get("action", "like")

        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user = self.authenticate_by_token(logintoken)
            
        if not photo_id:
            status = 400
            error_code = "photo_id cannot be empty"

        # User id contains error code
        if not user_status:
            return user

        csid_from_server = user['seriesid']
        user_id = user['id']

        if status == 200:
            if not action or action == "like":
                likes = db.select(
                    'profile_photo_likes',
                    where='photo_id = $photo_id and user_id = $user_id',
                    vars={'photo_id': photo_id, 'user_id': user_id}
                ).list()

                if len(likes) == 0:
                    db.insert('profile_photo_likes',
                              photo_id=photo_id,
                              user_id=user_id)
                    data['action'] = 'like'
            else:
                db.delete(
                    'profile_photo_likes',
                    where='photo_id = $photo_id and user_id = $user_id',
                    vars={'photo_id': photo_id, 'user_id': user_id}
                )
                data['action'] = 'dislike'

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


class GetCommentsToPhoto(BaseAPI):
    """
    API method that allows to get comments to photo
    """
    def POST(self):
        request_data = web.input(
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from
        photo_id = request_data.get("photo_id")

        csid_from_client = request_data.get('csid_from_client')

        if not photo_id:
            status = 400
            error_code = "photo_id cannot be empty"

        if status == 200:
            comments = db.query('''
                select profile_photo_comments.*,
                users.name, photos.*
                from profile_photo_comments
                join users
                on users.id = profile_photo_comments.user_id
                join photos
                on photos.id = users.pic
                where profile_photo_comments.photo_id = $id''',
                vars={'id': photo_id})\
                .list()
            if len(comments) > 0:
                data['comments'] = comments
            else:
                data['comments'] = []

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


class GetLikesToPhoto(BaseAPI):
    """
    API method that allows to get likes to photo
    """
    def POST(self):
        request_data = web.input(
        )

        data = {}
        status = 200
        csid_from_server = None
        error_code = ""

        # Get data from
        photo_id = request_data.get("photo_id")

        csid_from_client = request_data.get('csid_from_client')

        if not photo_id:
            status = 400
            error_code = "photo_id cannot be empty"

        if status == 200:
            likes = db.query('''
                select profile_photo_likes.*,
                users.name, photos.*
                from profile_photo_likes
                join users
                on users.id = profile_photo_likes.user_id
                join photos
                on photos.id = users.pic
                where profile_photo_likes.photo_id = $id''',
                vars={'id': photo_id})\
                .list()
            if len(likes) > 0:
                data['likes'] = likes
            else:
                data['likes'] = []

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response
