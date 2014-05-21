import datetime
import urlparse


def format_timestamp(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%B %d, %Y')

def get_dict_timestamp(ts):
    date_dict = {}
    dt = datetime.datetime.fromtimestamp(ts)
    date_dict['day'] = dt.strftime('%d')
    date_dict['month'] = dt.strftime('%b')
    date_dict['year'] = dt.strftime('%Y')
    return date_dict

def condense_link(link):
    return urlparse.urlparse(link).netloc
