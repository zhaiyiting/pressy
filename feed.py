import feedparser as fp
import urllib2

class Feed(object):
    ETAG_TYPE = 0  # only support etag head
    MODI_TYPE = 1  # only support modified head
    BOTH_TYPE = 2  # support both etag and modified head
    NONE_TYPE = 3  # support neither

    def __init__(self, link):
        self.link = link
        self.etag = ""
        self.modified = ""
        self.type_ = self.NONE_TYPE


class Core(object):

    def __init__(self):
        self.feedlist = []

    def add_feed(self, link):
        """ add the new feed to feeds list"""
        feed = Feed(link)
        self.__check_feed(feed)
        self.feedlist.append(feed)

    def load_feeds(self):
        pass

    def save_feeds(self):
        pass

    def __check_feed(self, feed):
        res = fp.parse(feed.link)
        if hasattr(res,"status"):
            if res.status != 200: # 200 for success
                return False
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
            feed.entries = res.entries
            # try to get the feed's icon
            if hasattr(res, "feed"):
                f = res.feed
                if hasattr(f, "link"):
                    link = f.link
                    icon_link = "http://www.google.comn/s2/favicons?domain=%s"%(link)
                    try:
                        feed.icon = urllib2.urlopen(icon_link).read()
                        if feed.icon.find("html") != -1:
                            feed.icon = None
                    except BaseException:
                        feed.icon = None
            else:
                feed.icon = None
        else:
            return False



if __name__ == "__main__":
    core = Core()
    #core.add_feed("http://coolshell.cn/feed")
    #core.add_feed("http://www.ruanyifeng.com/blog/atom.xml")
    core.add_feed("http://www.yinwang.org/atom.xml")
    print core.feedlist[-1].type_
    print core.feedlist[-1].icon
    print core.feedlist[-1].title


