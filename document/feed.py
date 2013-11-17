import feedparser as fp
import cPickle as pickle
import urllib2
import time
import os.path as osp
import threading
import Queue
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

    def __eq__(self, other):
        if self.id_ == other.id_:
            return True
        else:
            return False


class Entrie(object):
    def __init__(self, title, link, has_read=False):
        self.title = title
        self.link = link
        self.has_read = has_read


class Document(object):

    def __init__(self):
        self.feedlist = []
        self.icon_path = osp.join(st.common['app_path'],'windows','icons')
        self.folder_list = []
        self.load_feeds()

    def add_feed(self, link):
        """ add the new feed to feeds list"""
        feed = Feed(link)
        if self.__check_feed(feed):
            return 1
        self.feedlist.append(feed)

    def load_feeds(self):
        """ load feeds from file"""
        feeds_path = st.feeds_path
        if osp.exists(feeds_path):
            with open(feeds_path, 'rb') as f:
                try:
                    self.feedlist = pickle.load(f)
                    if not self.feedlist:
                        self.folder_list.append(u"Feeds")
                    return
                except EOFError:
                    pass
        self.folder_list.append(u"Feeds")

    def save_feeds(self):
        """ save all feeds """
        feeds_path = st.feeds_path
        with open(feeds_path, 'wb') as f:
            pickle.dump(self.feedlist, f, pickle.HIGHEST_PROTOCOL)

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
            for entrie in res.entries:
                title = entrie.title
                link = entrie.link
                entr = Entrie(title, link)
                feed.entries.append(entr)
            # try to get the feed's icon
            f = res.feed
            if hasattr(f, "link"):
                link = f.link
                icon_link = "http://www.google.com/s2/favicons?domain=%s"%(link)
                #try:
                icon = urllib2.urlopen(icon_link).read()
                icon_name = "icon_%s"%feed.id_
                path = osp.join(self.icon_path, icon_name+'.png') 
                if icon.find("html") != -1:
                    feed.icon = "default"
                else:
                    with open(path, 'wb') as f:
                        f.write(icon)
                    feed.icon = icon_name
                #except BaseException:
                #    feed.icon = None
            else:
                feed.icon = "default"
        else:
            return 1

    def refresh_all(self):
        """ refresh all feeds"""
        self.queue = Queue.Queue()
        self.slow_queue = Queue.Queue()
        for feed in self.feedlist:
            if feed.type_ != Feed.NONE_TYPE:
                self.queue.put(feed)
            else:
                self.slow_queue.put(feed)
        update_thread = threading.Thread(target = self.refresh)
        update_thread.start()

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

        thread_list = []
        for i in range(thread_num):
            thread = threading.Thread(target = self._refresh_none)
            thread_list.append(thread)
        for thread in thread_list:
            thread.start()
        for thread in thread_list:
            thread.join()

    def _refresh_etag_modify(self):
        """ refresh the feed which has etag or modify head"""
        while 1:
            if self.queue.empty():
                break
            print "up quick"
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
            print "up slow"
            feed = self.slow_queue.get()
            re = fp.parse(feed.link)
            if hasattr(re, "status"):
                if re.status == 200:
                    self.__add_new_entrie(re, feed)

    def __add_new_entrie(self, re, feed):
        new_entrie_list = []
        old_first_entrie_title = feed.entries[0].title
        for entrie in re.entries:
            title = entrie.title
            if title != old_first_entrie_title:
                link = entrie.link
                entr = Entrie(title, link)
                new_entrie_list.append(entr)
            else:
                break
        feed.entries = new_entrie_list + feed.entries
        if feed.type_ == Feed.BOTH_TYPE:
            feed.etag = re.etag
            feed.modified = re.modified
        elif feed.type_ == Feed.MODI_TYPE:
            feed.modified = re.modified
        elif feed.type_ == Feed.ETAG_TYPE:
            feed.etag = re.etag

if __name__ == "__main__":
    core = Core()
    #core.add_feed("http://coolshell.cn/feed")
    #core.add_feed("http://www.ruanyifeng.com/blog/atom.xml")
    core.add_feed("http://www.yinwang.org/atom.xml")
    print core.feedlist[-1].type_
    print core.feedlist[-1].icon
    print core.feedlist[-1].title


