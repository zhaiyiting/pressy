import threading

import pressy.qtall as qt
import pressy.utils as ut

from pressy.windows.feedtree import FeedTree
from pressy.windows.explorer import FeedExplorer
from pressy.document.feed import Document
from pressy.server import run_server

class MainWin(qt.QMainWindow):

    windows = []
    @classmethod
    def createWindow(cls):
        win = cls()
        win.show()
        cls.windows.append(win)

    def __init__(self):
        super(MainWin, self).__init__()
        self.document = Document()

        self.setup()
        self.make_toolbar()
        
        self.make_connection()

        self.setWindowTitle("Pressy")
        self.progress_bar = qt.QProgressBar(self.statusBar())
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        policy = qt.QSizePolicy(qt.QSizePolicy.Fixed,
                                qt.QSizePolicy.Fixed)
        def sizeHint():
            return qt.QSize(200, 18)
        self.progress_bar.sizeHint = sizeHint
        self.progress_bar.setSizePolicy(policy)

        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()
        self.setWindowIcon(ut.getIcon("main"))

        self.run_ser()

    def make_toolbar(self):
        a = ut.makeAction
        self.actions = {
                'feed.add':
                a(self, "add a feed", "&Add a feed",
                  self.slot_add_feed,
                  icon = "feed_add", key = None), 
                'feed.refresh':
                a(self, "refresh feeds", "&Fresh feeds",
                  self.slot_refresh_feeds,
                  icon = "feed_refresh", key = None),
                }

        # create toolbar
        web_toolBar = qt.QToolBar("web toolbar", self)
        web_toolBar.addAction(self.web_view.pageAction(qt.QtWebKit.QWebPage.Back))
        web_toolBar.addAction(self.web_view.pageAction(qt.QtWebKit.QWebPage.Forward))
        web_toolBar.addAction(self.web_view.pageAction(qt.QtWebKit.QWebPage.Reload))
        web_toolBar.addAction(self.web_view.pageAction(qt.QtWebKit.QWebPage.Stop))

        self.add_new_edit = qt.QLineEdit(web_toolBar)
        web_toolBar.insertWidget(None, self.add_new_edit)
        ut.addToolbarActions(web_toolBar, self.actions, ('feed.add',))
        self.addToolBar(qt.Qt.TopToolBarArea, web_toolBar)

    def setup(self):
        self.splitter = qt.QSplitter(self)
        self.feed_tree = FeedTree(self.document, self)
        self.splitter.addWidget(self.feed_tree)

        self.web_view = FeedExplorer(self.document, self)

        self.holder = qt.QWidget(self)
        policy = qt.QSizePolicy(qt.QSizePolicy.Fixed,
                                qt.QSizePolicy.Expanding)
        def sizeHint():
            return qt.QSize(10, 500)

        def enterEvent(e):
            self.holder.hide()
            self.feed_tree.show()
        self.holder.sizeHint = sizeHint
        self.holder.enterEvent = enterEvent
        self.holder.hide()
        self.splitter.addWidget(self.holder)

        self.splitter.addWidget(self.web_view)

        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(2, 3)
        self.setCentralWidget(self.splitter)


        self.web_view.titleChanged.connect(self.adjustTitle)
        self.web_view.loadProgress.connect(self.setProgress)
        self.web_view.loadFinished.connect(self.finishLoading)

    def make_connection(self):
        self.connect(self, qt.SIGNAL("add_feed"), self.feed_tree.treemodel.add_feed)


    def slot_add_feed(self):
        """ read the feed link from line edit and add it to document"""
        feed_link = unicode(self.add_new_edit.text())
        if self.document.add_feed(feed_link):
            qt.QMessageBox.warning(
                    self, "Error - Pressy",
                    "Can't parse this feed \n%s"%feed_link)
        else:
            self.emit(qt.SIGNAL("add_feed"), self.document.feedlist[-1])

    def slot_refresh_feeds(self):
        self.document.refresh_all()

    def setProgress(self, p ):
        """ set the page loading progress"""
        if self.progress_bar.isHidden():
            self.progress_bar.show()
        self.web_view.progress = p
        self.progress_bar.setValue(p)

    def finishLoading(self):
        self.web_view.progress = 100
        self.progress_bar.setValue(self.web_view.progress)
        self.progress_bar.hide()

    def adjustTitle(self):
        self.setWindowTitle("Pressy - " + self.web_view.title())

    def run_ser(self):
        """ run the bottle server"""
        thread = threading.Thread(target=run_server, args=(self.document,))
        thread.setDaemon(True)
        thread.start()

    def closeEvent(self, e):
        """ save feeds before close window"""
        self.document.save_feeds()
        e.accept()
