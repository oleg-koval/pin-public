all_categories = None


def initialize(db):
    global all_categories
    all_categories = list(db.select('categories', order='id',
                                    where='parent is null'))