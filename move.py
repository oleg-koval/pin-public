import db
import urllib
import os
from PIL import Image
import traceback

db = db.connect_db()


def upload_image(url, pid):
    ext = os.path.splitext(url)[1].lower()

    urllib.urlretrieve(url, 'static/tmp/%d%s' % (pid, ext))
    if ext != '.png':
        img = Image.open('static/tmp/%d%s' % (pid, ext))
        img.save('static/tmp/%d.png' % pid)


temp_pins = list(db.select('temp_pins'))
for y in temp_pins:
    try:
        new_id = db.insert('pins', description=y.title, user_id=20, board_id=12, link=y.link, category=4)
        try:
            upload_image(y.image, new_id)
        except:
            db.delete('pins', where='id = $id', vars={'id': new_id})
        db.delete('temp_pins', where='id = $id', vars={'id': y.id})
    except:
        traceback.print_exc()
        continue
