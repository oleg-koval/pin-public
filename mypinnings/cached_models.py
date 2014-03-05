all_categories = None
categories_with_thumbnails = None

def initialize(db):
    global all_categories
    all_categories = list(db.select('categories', order='id'))
    get_categories_with_thumbnails(db)

def get_categories_with_thumbnails(db):
    global categories_with_thumbnails
    results = db.select(what='categories.id, categories.name, category_register_thumbnails.image_name',
                        tables=['categories', 'category_register_thumbnails'],
                        where='categories.id = category_register_thumbnails.category_id',
                        order='categories.name')
    categories_with_thumbnails = []
    current_category = None
    for row in results:
        cat_id = row['id']
        if current_category is None or current_category['id'] != cat_id:
            current_category = {'id': cat_id, 'name': row['name'], 'thumbs': []}
            categories_with_thumbnails.append(current_category)
        thumb = {'image_name': row['image_name']}
        current_category['thumbs'].append(thumb)
