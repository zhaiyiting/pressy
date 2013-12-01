from lxml import etree
import cPickle as pickle
import urllib2
import time
import os.path as osp
import threading
import Queue
import feedparser as fp
import pressy.setting as st
import pressy.utils as ut

class Feed(object):
    ETAG_TYPE = 0  # only support etag head
    MODI_TYPE = 1  # only support modified head
    BOTH_TYPE = 2  # support both etag and modified head
    NONE_TYPE = 3  # support neither

    def __init__(self, link):
        self.link = link
        self.etag = ""
        self.modified = ""
        self.title = ""
        self.type_ = self.NONE_TYPE
        self.entries = []
        self.id_ = ""
        self.folder = u"Feeds"
        self.href = ""

    def __eq__(self, other):
        if self.id_ == other.id_:
            return True
        else:
            return False


class Entrie(object):
    def __init__(self, title, link, has_read=True):
        self.title = title
        self.link = link
        self.has_read = has_read

class Document(object):

    def __init__(self):
        self.feedlist = []
        self.icon_path = st.icon_path
        self.folder_list = []
        self.load_feeds()
        # this variable will used when user close the mainwindow
        self.update = False
        self.update_feeds = 0
        self.update_items = 0

    def add_feed(self, link, html):
        """ add the new feed to feeds list"""
        feed = Feed(link)
        feed_link = feed.link.lower()
        if not feed_link.startswith("http"):
            feed_link = "http://" + feed.link
        success = False
        if self.__check_feed(feed):
            try:
                href_feed = []
                page = etree.HTML(html.lower())
                links_node = page.xpath(u"//link[@type='application/rss+xml'][1]")
                tmp = [href_feed.extend(link.xpath(u"attribute::href")) for link in links_node]
                links_node = page.xpath(u"//link[@type='application/atom+xml'][1]")
                tmp = [href_feed.extend(link.xpath(u"attribute::href")) for link in links_node]
                for href in href_feed:
                    if not href.startswith("http"):
                        href = feed_link + href
                    feed = Feed(href)
                    if not self.__check_feed(feed):
                        success = True
                        break
            except BaseException:
                return 1
        else:
            success = True
        if not success:
            return 1
        self.feedlist.append(feed)

    def load_feeds(self):
        """ load feeds from file"""
        feeds_path = st.feeds_path
        if osp.exists(feeds_path):
            with open(feeds_path, 'rb') as f:
                try:
                    self.feedlist, self.folder_list = pickle.load(f)
                    if not self.feedlist and not self.folder_list:
                        self.folder_list.append(u"Feeds")
                    return
                except EOFError:
                    pass
        self.folder_list.append(u"Feeds")

    def save_feeds(self):
        """ save all feeds """
        feeds_path = st.feeds_path
        with open(feeds_path, 'wb') as f:
            pickle.dump((self.feedlist, self.folder_list), f, pickle.HIGHEST_PROTOCOL)

    def __check_feed(self, feed):
        res = fp.parse(feed.link)
        if hasattr(res,"status"):
            if res.status != 200: # 200 for success
                return 1
            else:
                #---------------- check the feed's type( feed's server support which header) --------------
                if hasattr(res, "etag"):
                    feed.etag = res.etag
                if hasattr(res, "modified"):
                    feed.modified = res.modified
                if not 'title' in res.feed:
                    return 1

                # support both? check again (need to confirm the request header does work!)
                if feed.etag and feed.modified:
                    res_ag = fp.parse(feed.link, etag=feed.etag, modified=feed.modified)
                    if hasattr(res_ag, "status"):
                        if res_ag.status == 304:  # it should be 304, if the header was accepted by server
                            feed.type_ = Feed.BOTH_TYPE
                elif feed.etag:
                    res_ag = fp.parse(feed.link, etag=feed.etag)
                    if hasattr(res_ag, "status"):
                        if res_ag.status == 304:
                            feed.type_ = Feed.ETAG_TYPE
                elif feed.modified:
                    res_ag = fp.parse(feed.link, modified=feed.modified)
                    if hasattr(res_ag, "status"):
                        if res_ag.status == 304:
                            feed.type_ = Feed.MODI_TYPE
            #------------------- initial the feed info -------------------------
            feed.title = res.feed.title
            feed.id_ = "%d"%time.time()
            for i, entrie in enumerate(res.entries):
                title = entrie.title
                link = entrie.link
                entr = Entrie(title, link)
                if i < 5:
                    entr.has_read = False
                feed.entries.append(entr)
            # try to get the feed's icon
            f = res.feed
            if hasattr(f, "link"):
                link = f.link
                feed.href = link
                icon_link = "http://www.google.com/s2/favicons?domain=%s"%(link)
                try:
                    icon = urllib2.urlopen(icon_link).read()
                    icon_name = "icon_%s"%feed.id_
                    path = osp.join(self.icon_path, icon_name+'.png') 
                    if icon.find("html") != -1:
                        feed.icon = "default"
                    else:
                        with open(path, 'wb') as f:
                            f.write(icon)
                        feed.icon = icon_name
                except BaseException:
                    feed.icon = None
            else:
                feed.href = feed.link
                feed.icon = "default"
        else:
            return 1

    def refresh_all(self, f_update_feedtree, f_signal):
        """ refresh all feeds"""
        self.queue = Queue.Queue()
        self.slow_queue = Queue.Queue()
        self.update_queue = Queue.Queue()
        self.update_num = Queue.Queue()
        self.f_update_tree = f_update_feedtree
        self.f_signal = f_signal
        self.update_feeds = 0
        self.update_items = 0
        # for thread safe
        feed_list = self.feedlist[:]
        for feed in feed_list:
            if feed.type_ != Feed.NONE_TYPE:
                self.queue.put(feed)
            else:
                self.slow_queue.put(feed)
        self.update_thread = threading.Thread(target = self.refresh)
        self.update_thread.start()

    def get_update_list(self):
        self.update_list = []
        while not self.update_queue.empty():
            self.update_list.append(self.update_queue.get())

    def get_update_item_num(self):
        update_list = []
        while not self.update_num.empty():
            update_list.append(self.update_num.get())
        return sum(update_list)

    def refresh(self):
        """ refresh all feeds"""
        thread_list = []
        thread_num = 5
        for i in range(thread_num):
            thread = threading.Thread(target = self._refresh_etag_modify)
            thread_list.append(thread)
        for thread in thread_list:
            thread.start()
        for thread in thread_list:
            thread.join()

        self.update = True
        self.get_update_list()
        self.f_update_tree(self.update_list)
        self.update = False

        self.update_feeds += len(self.update_list)

        thread_list = []
        for i in range(thread_num):
            thread = threading.Thread(target = self._refresh_none)
            thread_list.append(thread)
        for thread in thread_list:
            thread.start()
        for thread in thread_list:
            thread.join()

        self.update = True
        self.get_update_list()
        self.f_update_tree(self.update_list)
        self.update = False

        self.update_feeds += len(self.update_list)
        self.update_items += self.get_update_item_num()

        self.f_signal()

    def _refresh_etag_modify(self):
        """ refresh the feed which has etag or modify head"""
        while 1:
            if self.queue.empty():
                break
            feed = self.queue.get()
            if feed.type_ == Feed.BOTH_TYPE:
                re = fp.parse(feed.link, etag=feed.etag, modified=feed.modified)
            elif feed.type_ == Feed.MODI_TYPE:
                re = fp.parse(feed.link, modified=feed.modified)
            elif feed.type_ == Feed.ETAG_TYPE:
                re = fp.parse(feed.link, etag=feed.etag)
            if hasattr(re, "status"):
                if re.status == 200:
                    self.__add_new_entrie(re, feed)
                    
    def _refresh_none(self):
        """ refresh the feed which has no head """
        while 1:
            if self.slow_queue.empty():
                break
            feed = self.slow_queue.get()
            re = fp.parse(feed.link)
            if hasattr(re, "status"):
                if re.status == 200:
                    self.__add_new_entrie(re, feed)

    def __add_new_entrie(self, re, feed):
        new_entrie_list = []
        old_first_entrie_link = feed.entries[0].link
        for entrie in re.entries:
            link = entrie.link
            if link != old_first_entrie_link:
                title = entrie.title
                entr = Entrie(title, link)
                entr.has_read = False
                new_entrie_list.append(entr)
            else:
                break
        if new_entrie_list:
            self.update_queue.put(feed)
        feed.entries = new_entrie_list + feed.entries
        self.update_num.put(len(new_entrie_list))
        if feed.type_ == Feed.BOTH_TYPE:
            feed.etag = re.etag
            feed.modified = re.modified
        elif feed.type_ == Feed.MODI_TYPE:
            feed.modified = re.modified
        elif feed.type_ == Feed.ETAG_TYPE:
            feed.etag = re.etag

