import pressy.qtall as qt

class FeedExplorer(qt.QWebView):

    def __init__(self, document, parentwin):
        super(FeedExplorer, self).__init__(parentwin)
        self.document = document
