import random

from mypinnings import database


DIGITS = '1234567890'
LETTERS = 'abcdefghijklmnopqrstuvwxwzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def generate_external_id():
    id = _new_external_id()
    while _already_exists(id):
        id = _new_external_id()
    return id


def _new_external_id():
    digits = random.sample(DIGITS, 6)
    letters = random.sample(LETTERS, 3)
    digits_and_letters = []
    digits_and_letters.extend(digits)
    digits_and_letters.extend(letters)
    random.shuffle(digits_and_letters)
    return ''.join(digits_and_letters)


def _already_exists(id):
    db = database.get_db()
    results = db.where('pins', external_id=id)
    for _ in results:
        return True
    return False