from bottle import run, get, redirect, view

global doc
def run_server(document):
    global doc
    doc = document
    run(host='localhost', port=8080)

def get_feed(id_):
    global doc
    feed_list = doc.feedlist
    for feed in doc.feedlist:
        if feed.id_ == id_:
            return feed

@get('/feed/<id_>')
@view('feed_template')
def feed_page(id_):
    feed = get_feed(id_)
    return dict(feed = feed)

@get('/entries/<id_>/<index>')
def entrie_page(id_, index):
    feed = get_feed(id_)
    entrie = feed.entries[int(index)]
    entrie.has_read = True
    link = entrie.link
    redirect(link)
    


