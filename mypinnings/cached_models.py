all_categories = None


def initialize(db):
    global all_categories
    all_categories = list(db.select('categories', order='id',
                                    where='parent is null'))
    
    
def get_categories_with_children(db):
    results = db.query('''
        select cat.id, cat.name, sub.id as subcategory_id, sub.name as subcatetory_name, sub.is_default_sub_category
        from categories cat
            left join categories sub on cat.id = sub.parent
        order by cat.id, sub.is_default_sub_category, sub.name
        ''')
    categories = []
    current_category = None
    for row in results:
        if not current_category or current_category['id'] != row.id:
            current_category = {'id': row.id,
                                'name': row.name,
                                'subcategories': []}
            categories.append(current_category)
        if row.subcategory_id:
            subcat = {'id': row.subcategory_id,
                      'name': row.subcatetory_name,
                      'id_default_sub_category': row.is_default_sub_category}
            current_category['subcategories'].append(subcat)
    return categories
