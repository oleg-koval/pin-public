names = [
    'MyPinnings Recommendations',
    'Bicycle & Motor Bikes',
    'Cars',
    'Collectibles (Arts & Crafts)',
    'Beauty',
    'Books',
    'Cell Phones',
    'Fashion',
    'Gadgets',
    'Jewelry',
    'Money',
    'Movies & Music',
    'Shoes',
    'Travel & Experiences',
    'Watches',
    'Wine & Champagne',
]

import db
db = db.connect_db()

names = [{'name': x} for x in names]
db.multiple_insert('categories', names)
