import datetime
import urlparse


def format_timestamp(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%B %d, %Y')

def condense_link(link):
    return urlparse.urlparse(link).netloc
