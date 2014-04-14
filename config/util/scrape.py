import requests
from bs4 import BeautifulSoup
import pprint
import multiprocessing
import multiprocessing.pool
import Queue

def get_soup(url):
    r = requests.get(url)
    return BeautifulSoup(r.text)


def get_post(div):
    global seen_categories

    try:
        title = div.find('h2').find('a').string

        link = div.find('span', **{'class': 'button'})
        link = link.find('a', target='_blank')['href']

        image = div.find('img', **{'class': 'size-full'})['src']
        
        description = div.find('div', **{'class': 'post-content'}).get_text()

        return {'title': title, 'link': link, 'image': image,
                'description': description}
    except:
        return None


def fetch_posts(url, queue, lock):
    lock.acquire()
    print url
    lock.release()

    soup = get_soup(url)
    divs = soup.find_all('div', **{'class': 'type-post'})
    for div in divs:
        post = get_post(div)
        if post:
            queue.put(post)


def get_queue_contents(queue):
    def get_queue():
        try:
            return queue.get_nowait()
        except:
            return None
    return [x for x in iter(get_queue, None)]
                

if __name__ == '__main__':
    urls = ['http://www.holycool.net/page/%d' % x for x in range(1, 128)]
    queue = Queue.Queue()
    lock = multiprocessing.Lock()
    pool = multiprocessing.pool.ThreadPool(60)

    for url in urls:
        pool.apply_async(fetch_posts, args=(url, queue, lock))
    pool.close()
    pool.join()

    posts = get_queue_contents(queue)
    with open('scraped.txt', 'w') as f:
        f.write(str(posts))
