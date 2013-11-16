import time
import pressy.qtall as qt
import pressy.utils as ut
import pressy.windows.feed_tree as ft
from modeltest import ModelTest

class FeedTree(qt.QWidget):

    def __init__(self, document, parentwin):
        super(FeedTree, self).__init__(parentwin)
        btn_layout = qt.QHBoxLayout()
        layout = qt.QVBoxLayout(self)

        self.refresh_feed_btn = ut.create_toolbutton(self, icon = "feed_refresh",
                                                triggered = self.slot_refresh_feeds)
        self.refresh_feed_btn.setIconSize(qt.QSize(18,18))
        btn_layout.addWidget(self.refresh_feed_btn)
        btn_layout.setAlignment(qt.Qt.AlignLeft)

        self.pin_btn = ut.create_toolbutton(self, icon = "pin",
                                       toggled = self.slot_auto_hide)
        self.pin_btn.setIconSize(qt.QSize(18,18))
        btn_layout.addStretch()
        btn_layout.addWidget(self.pin_btn)

        self.document = document
        self.parentwin = parentwin
        self.treemodel = ft.TreeModel()
        self.modeltest = ModelTest(self.treemodel, None)
        self.treemodel.add_root()
        self.treeview = qt.QTreeView(self)
        self.treeview.setModel(self.treemodel)
        self.treeview.setHeaderHidden(True)
        self.treeview.expandAll()
        self.treemodel.add_feeds(self.document.feedlist)

        layout.addLayout(btn_layout)
        layout.addWidget(self.treeview)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.current_index = None

        self.connect(self.treeview, qt.SIGNAL("clicked(const QModelIndex &)"),
                     self.slotTreeItemClicked)


    def slotTreeItemClicked(self, index):
        """ generate the link """
        item = index.internalPointer()
        self.current_index = index
        item_data = item.itemData
        if item_data.id_:
            link = "http://localhost:8080/feed/%s"%item_data.id_
            webview = self.parentwin.web_view
            webview.setUrl(qt.QUrl(link))

    def slotUpdateUnread(self):
        if self.current_index:
            self.treemodel.emit(qt.SIGNAL("dataChanged(QModelIndex, QModelIndex)"),\
                                self.current_index, self.current_index)
    def slot_refresh_feeds(self):
        self.movie = qt.QMovie(r"F:\pressy\windows\refresh.gif")
        qt.QObject.connect(self.movie, qt.SIGNAL("frameChanged(int)"),self.slot_refresh_icon)
        self.movie.start()
        self.document.refresh_all()

    def slot_refresh_icon(self, frame):
        self.refresh_feed_btn.setIcon(qt.QIcon(self.movie.currentPixmap()))

    def slot_auto_hide(self):
        if not self.pin_btn.isChecked():
            self.show()
            self.parent().parent().holder.hide()

    def leaveEvent(self, e):
        if self.pin_btn.isChecked():
            self.hide()
            self.parent().parent().holder.show()


