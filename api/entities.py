from mypinnings.database import connect_db
from api.utils import photo_id_to_url

db = connect_db()


class UserProfile(object):
    """
    Object responsible for obtaining user related information and data.
    """
    fields = ['id', 'name', 'about', 'city', 'country', 'hometown',
              'about', 'email', 'pic', 'website', 'facebook',
              'twitter', 'getlist_privacy_level', 'private', 'bg',
              'bgx', 'bgy', 'show_views', 'views', 'username', 'zip',
              'linkedin', 'gplus', 'activation', 'is_pin_loader', 'bg_resized_url']

    @staticmethod
    def prepare_fields():
        """
        Appends users. to each field, for inner sql queries
        """
        user_fields = ", ".join(["users.%s" %(field)
                                 for field in UserProfile.fields])
        return user_fields

    @staticmethod
    def format_birthday(user, response):
        """
        Composes birthday response, returning year, day and month
        as separate response fields
        """
        if user.get('birthday'):
            response['birthday_year'] = user['birthday'].year
            response['birthday_day'] = user['birthday'].day
            response['birthday_month'] = user['birthday'].month
        return response

    @staticmethod
    def query_user(profile="", user_id=0):
        """
        Returns all profile fields specified by fields section
        """
        query = db.select('users', vars={'username': profile,
                              'id': user_id},
                              where="username=$username or id=$id")
        if len(query) > 0:
            user = query.list()[0]
            user['pic'] = photo_id_to_url(user['pic'])
        else:
            return False
        response = {field: user.get(field) for field in UserProfile.fields}
        response = UserProfile.format_birthday(user, response)
        return response

    @staticmethod
    def query_following(profile_owner, current_user):
        """
        A bit complex query which returns all users whom current user is following
        """
        vars = {'id': profile_owner, 'user_id': current_user}
        query = '''
        select %s, f2.follow <> 0 is_following from users
        join      follows f1 on f1.follow = users.id
        left join follows f2 on f2.follow = users.id and f2.follower = $user_id
        where f1.follower = $id; ''' % (UserProfile.prepare_fields())

        results = db.query(query, vars=vars).list()

        return results

    @staticmethod
    def query_followed_by(profile_owner, current_user):
        """
        A bit complex query which returns all users who
        are following the current user
        """
        vars = {'id': profile_owner, 'user_id': current_user}
        query = '''
        select %s, f2.follower <> 0 is_following from users
        join follows f1 on f1.follower = users.id
        left join follows f2 on f2.follow = users.id and f2.follower = $user_id
        where f1.follow = $id;''' % (UserProfile.prepare_fields())

        results = db.query(query, vars=vars).list()
        return results
