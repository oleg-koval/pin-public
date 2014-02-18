from db import connect_db

db = connect_db()

if __name__ == '__main__':
    pins = db.select('pins')
    for pin in pins:
        try:
            open('static/tmp/%d.png' % pin.id)
            print 'exists'
        except:
            db.delete('pins', where='id = $id', vars={'id': pin.id})
