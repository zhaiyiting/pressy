from flask import Flask
from flask import render_template, redirect, url_for
app = Flask(__name__)
#from bottle import run, get, redirect, view, static_file

global doc
def run_server(document):
    global doc
    doc = document
    app.run(host='localhost', port=5000)

def get_feed(id_):
    global doc
    feed_list = doc.feedlist
    for feed in doc.feedlist:
        if feed.id_ == id_:
            return feed

@app.route('/feed/<id_>')
def feed_page(id_):
    feed = get_feed(id_)
    return render_template('feed_template.html', feed=feed)

@app.route('/entries/<id_>/<index>')
def entrie_page(id_, index):
    feed = get_feed(id_)
    entrie = feed.entries[int(index)]
    entrie.has_read = True
    link = entrie.link
    return redirect(link)
