import web
import re
from settings import BING
from base64 import encodestring
from base import BaseAPI
from json import loads, dumps
from urllib2 import urlopen, Request

auth = BING['customer_id'] + ':' + BING['account_key']
auth = encodestring(auth).replace('\n', '')
auth = 'Basic ' + auth


class Image(BaseAPI):
    def GET(self):
        params = web.input()
        web.header('Content-Type', 'application/json')
        if not params.q:
            return '[]'
        query = re.sub(r"[ \t\"'#&%=]+", '+', params.q)
        offset = int(params.offset) if 'offset' in params else 0
        a = []
        google_offset = 64

        if offset < google_offset:
            count = google_offset - offset
            if count > 8:
                count = 8
            r = urlopen('http://ajax.googleapis.com/ajax/services/' +
                       'search/images?v=1.0&q=%s&rsz=%s&start=%s'
                       % (query, count, offset))
            r = r.read()
            r = loads(r)
            for img in r[u'responseData'][u'results']:
                a.append({
                    'thumb': img[u'tbUrl'],
                    'url':   img[u'originalContextUrl'],
                    'title': img[u'titleNoFormatting'],
                    'desc':  img[u'contentNoFormatting'],
                })
        else:
            offset -= google_offset
            request = Request(
                'https://api.datamarket.azure.com/Data.ashx/Bing/' +
                'Search/Composite?Sources=%27image%27&Query=%27' + query +
                '%27&$format=json&$top=48&$skip=' + str(offset))
            request.add_header('Authorization', auth)
            r = urlopen(request)
            r = r.read()
            r = loads(r)
            for img in r[u'd'][u'results'][0][u'Image']:
                a.append({
                    'thumb': img[u'Thumbnail'][u'MediaUrl'],
                    'url':   img[u'SourceUrl'],
                    'title': img[u'Title'],
                    'desc':  None,
                })

        return dumps(a)
