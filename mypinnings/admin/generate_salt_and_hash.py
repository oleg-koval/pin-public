from mypinnings.auth import generate_salt
from mypinnings.admin.auth import salt_and_hash

if __name__ == '__main__':
    # create a password salt
    pw = 'davidfanisawesome'
    salt = generate_salt(10)
    hash = salt_and_hash(password=pw, salt=salt)
    print('salt:{} hash:{}'.format(salt, hash))


    pw = 'camilo'
    salt = generate_salt(10)
    hash = salt_and_hash(password=pw, salt=salt)
    print('salt:{} hash:{}'.format(salt, hash))
