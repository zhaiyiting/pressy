import feedparser as fp

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


def Core(object):

    def __init__(self):
        pass

    def add_feed(self, link):
        """ add the new feed to feeds list"""
        feed = Feed(link)

    def load_feeds(self):
        pass

    def __check_feed(self, feed):
        res = fp.parse(feed.link)
        if __hasattr(res,"status"):
            if res.status != 200: # 200 for success
                return False
            else:
                #---------------- check the feed's type( feed's server support which header) --------------
                if __hasattr(res, "etag"):
                    feed.etag = res.etag
                if __hasattr(res, "modified"):
                    feed.modified = res.modified

                # support both? check again (need to confirm the request header does work!)
                if feed.etag and feed.modified:
                    res_ag = fp.parse(feed.link, etag=feed.etag, modified=feed.modified)
                    if __hasattr(res_ag, "status"):
                        if res.status == 304:  # it should be 304, if the header was accepted by server
                            feed.type_ = Feed.BOTH_TYPE
                elif feed.etag:
                    res_ag = fp.parse(feed.link, etag=feed.etag)
                    if __hasattr(res_ag, "status"):
                        if res.status == 304:
                            feed.type_ = Feed.ETAG_TYPE
                elif feed.modified:
                    res_ag = fp.parse(feed.link, modified=feed.modified)
                    if __hasattr(res_ag, "status"):
                        if res.status == 304:
                            feed.type_ = Feed.MODI_TYPE
            #------------------- initial the feed info -------------------------
            pass
        else:
            return False

    def __hasattr(obj, attr):
        try:
            hasattr(obj, attr)
            return True
        except AttributeError:
            return False

