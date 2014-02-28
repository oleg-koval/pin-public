from mypinnings.database import get_db


all_categories = list(get_db().select('categories', order='id'))