import datetime

import web

from mypinnings.admin import auth
from mypinnings import template
from mypinnings import database
    

class FixCreationDateMixin(object):
    def fix_creation_date(self, results):
        fixed = []
        for row in results:
            date_created = datetime.date.fromtimestamp(row.timestamp)
            row['creation_date'] = date_created.isoformat()
            fixed.append(row)
        return fixed


USERS_QUERY = '''
select
    users.*,
    count(distinct f1) as follower_count,
    count(distinct f2) as follow_count,
    count(distinct p1) as repin_count,
    count(distinct p2) as pin_count,
    count(distinct friends) as friend_count
from users
    left join follows f1 on f1.follow = users.id
    left join follows f2 on f2.follower = users.id
    left join friends on (friends.id1 = users.id or
                          friends.id2 = users.id)
    left join pins p1 on p1.repin = users.id
    left join pins p2 on p2.user_id = users.id
where users.is_pin_loader='t' {where}
group by users.id
order by {sort} {dir}
offset {offset} limit {limit}'''


class Results(object):
    def GET(self):
        auth.login()
        params = web.input(query='')
        query = params.query
        return template.admin.dataloaders_results(query)


class ResultsPagination(FixCreationDateMixin):
    page_size = 50

    def GET(self, allusers=None):
        auth.login()

        params = web.input(page=1, sort='users.name', dir='asc', query='')
        page = int(params.page) - 1
        sort = params.sort
        direction = params.dir
        search_query = params.query

        if search_query:
            where = """ and (
            users.email ilike '%%{query}%%' or
            users.name ilike '%%{query}%%' or
            users.about ilike '%%{query}%%')""".format(query=search_query)
        else:
            where = ''
        query = USERS_QUERY.format(where=where,
                                  sort=sort,
                                  dir=direction,
                                  offset=page * self.page_size,
                                  limit=self.page_size)
            
        db = database.get_db()
        results = db.query(query)
        results = self.fix_creation_date(results)
        return web.template.frender('t/admin/search_results.html')(results)
