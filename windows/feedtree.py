import time
import pressy.qtall as qt
import pressy.utils as ut
import pressy.windows.feed_tree as ft
from modeltest import ModelTest

class FeedTree(qt.QWidget):

    def __init__(self, document, parentwin):
        super(FeedTree, self).__init__(parentwin)
        btn_layout = qt.QHBoxLayout()
        btn_layout.setAlignment(qt.Qt.AlignLeft)
        layout = qt.QVBoxLayout(self)

        # refresh tool button
        self.refresh_feed_btn = ut.create_toolbutton(self, icon = "feed_refresh",
                                                     tip = "refresh all feeds",
                                                     triggered = self.slot_refresh_feeds)
        self.refresh_feed_btn.setIconSize(qt.QSize(18,18))
        btn_layout.addWidget(self.refresh_feed_btn)

        # new folder tool button
        self.new_folder_btn = ut.create_toolbutton(self, icon = "folder",
                                                   tip = "create a new folder",
                                                   triggered = self.slot_new_folder)
        self.new_folder_btn.setIconSize(qt.QSize(18,18))
        btn_layout.addWidget(self.new_folder_btn)

        # delete folder tool button
        self.delete_btn = ut.create_toolbutton(self, icon = "delete",
                                                   tip = "delete one feed or folder",
                                                   triggered = self.slot_del_feed_folder)
        self.delete_btn.setIconSize(qt.QSize(18,18))
        btn_layout.addWidget(self.delete_btn)


        self.pin_btn = ut.create_toolbutton(self, icon = "pin",
                                       toggled = self.slot_auto_hide)
        self.pin_btn.setIconSize(qt.QSize(18,18))
        btn_layout.addStretch()
        btn_layout.addWidget(self.pin_btn)

        self.document = document
        self.parentwin = parentwin
        self.treemodel = ft.TreeModel()
        self.modeltest = ModelTest(self.treemodel, None)
        self.treeview = qt.QTreeView(self)
        self.treeview.setModel(self.treemodel)
        self.treeview.setHeaderHidden(True)
        self.treeview.expandAll()
        self.treemodel.add_feeds(self.document.feedlist, self.document.folder_list)

        layout.addLayout(btn_layout)
        layout.addWidget(self.treeview)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.current_index = None

        self.connect(self.treeview, qt.SIGNAL("clicked(const QModelIndex &)"),
                     self.slotTreeItemClicked)

    def slot_del_feed_folder(self):
        if self.current_index:
            item = self.current_index.internalPointer()
            item_data = item.itemData
            if isinstance(item_data, unicode):
                folder_name = item_data
                for child in item.childItems:
                    feed = child.itemData
                    self.document.feedlist.remove(feed)
                folder_index = self.document.folder_list.index(folder_name)
                self.treemodel.delete_folder(folder_name, folder_index)
                self.document.folder_list.remove(folder_name)
            else:
                feed = self.current_index.internalPointer().itemData
                self.treemodel.delete_feed(self.current_index)
                self.document.feedlist.remove(feed)

    def slotTreeItemClicked(self, index):
        """ generate the link """
        item = index.internalPointer()
        self.current_index = index
        item_data = item.itemData
        if not isinstance(item_data, unicode):
            if item_data.id_:
                link = "http://localhost:8080/feed/%s"%item_data.id_
                webview = self.parentwin.web_view
                webview.setUrl(qt.QUrl(link))

    def slotUpdateUnread(self):
        if self.current_index:
            self.treemodel.emit(qt.SIGNAL("dataChanged(QModelIndex, QModelIndex)"),\
                                self.current_index, self.current_index)

    def slot_new_folder(self, feed_dlg=None):
        new_floder_dlg = NewFolder(self.document, self)
        rtn = new_floder_dlg.exec_()
        if rtn:
            self.document.folder_list.append(new_floder_dlg.folder_name)
            self.treemodel.add_folder(new_floder_dlg.folder_name)
            if feed_dlg:
                feed_dlg.combo.addItem(new_floder_dlg.folder_name)
                feed_dlg.combo.setCurrentIndex(feed_dlg.combo.count() - 1)


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

    def slot_add_feed(self, feed):
        new_dlg = NewFeed(feed, self.document, self)
        rtn = new_dlg.exec_()


class NewFolder(qt.QDialog):

    def __init__(self, document, parent = None):
        super(NewFolder, self).__init__(parent)
        self.document = document
        self.setup()
        self.setWindowTitle("New Folder")
        self.resize(250,60)

    def setup(self):
        hlayout_u = qt.QHBoxLayout()
        self.label = qt.QLabel("Folder Name", self)
        self.edit = qt.QLineEdit(self)
        self.label.setBuddy(self.edit)
        hlayout_u.addWidget(self.label)
        hlayout_u.addWidget(self.edit)

        hlayout_d = qt.QHBoxLayout()
        def sizeHint():
            return qt.QSize(70, 20)
        ok_button = qt.QPushButton("OK")
        cancel_button = qt.QPushButton("Cancel")
        ok_button.sizeHint = sizeHint
        cancel_button.sizeHint = sizeHint
        policy = qt.QSizePolicy(qt.QSizePolicy.Fixed,
                                qt.QSizePolicy.Fixed)
        ok_button.setSizePolicy(policy)
        cancel_button.setSizePolicy(policy)
        hlayout_d.addStretch()
        hlayout_d.addWidget(ok_button)
        hlayout_d.addWidget(cancel_button)

        vlayout = qt.QVBoxLayout(self)
        vlayout.addLayout(hlayout_u)
        vlayout.addLayout(hlayout_d)

        self.connect(ok_button, qt.SIGNAL("clicked()"), self.accept)
        self.connect(cancel_button, qt.SIGNAL("clicked()"), self.reject)

        self.setLayout(vlayout)

    def accept(self):
        self.folder_name = unicode(self.edit.text())
        if self.folder_name in self.document.folder_list:
            qt.QMessageBox.warning(self, "Eoor - Pressy",
                                   'The folder "%s" is already exists'%self.folder_name)
        else:
            super(NewFolder, self).accept()

class NewFeed(qt.QDialog):

    def __init__(self, feed, document, parent=None):
        super(NewFeed, self).__init__(parent)
        self.feed = feed
        self.new_folder = parent.slot_new_folder
        self.add_feed = parent.treemodel.add_feed
        self.document = document
        self.setup()
        self.setWindowTitle("New Feed")
        self.resize(310, 85)

    def setup(self):
        hlayout_u = qt.QHBoxLayout()
        self.label = qt.QLabel("Feed Name", self)
        self.edit = qt.QLineEdit(self)
        self.label.setBuddy(self.edit)
        self.edit.setText(self.feed.title)
        hlayout_u.addWidget(self.label)
        hlayout_u.addWidget(self.edit)

        hlayout_m = qt.QHBoxLayout()
        self.label = qt.QLabel("Feed Folder", self)
        self.combo = qt.QComboBox(self)
        policy = qt.QSizePolicy(qt.QSizePolicy.Expanding,
                                qt.QSizePolicy.Fixed)
        self.combo.setSizePolicy(policy)
        for folder in self.document.folder_list:
            self.combo.addItem(folder)
        self.combo.setCurrentIndex(0)
        self.label.setBuddy(self.combo)
        hlayout_m.addWidget(self.label)
        hlayout_m.addWidget(self.combo)

        hlayout_d = qt.QHBoxLayout()
        def sizeHint():
            return qt.QSize(70, 20)
        ok_button = qt.QPushButton("OK")
        cancel_button = qt.QPushButton("Cancel")
        new_button = qt.QPushButton("New Folder")
        ok_button.sizeHint = sizeHint
        cancel_button.sizeHint = sizeHint
        new_button.sizeHint = sizeHint
        policy = qt.QSizePolicy(qt.QSizePolicy.Fixed,
                                qt.QSizePolicy.Fixed)
        ok_button.setSizePolicy(policy)
        cancel_button.setSizePolicy(policy)
        new_button.setSizePolicy(policy)
        hlayout_d.addWidget(new_button)
        hlayout_d.addStretch()
        hlayout_d.addWidget(ok_button)
        hlayout_d.addWidget(cancel_button)

        vlayout = qt.QVBoxLayout(self)
        vlayout.addLayout(hlayout_u)
        vlayout.addLayout(hlayout_m)
        vlayout.addLayout(hlayout_d)

        self.connect(ok_button, qt.SIGNAL("clicked()"), self.accept)
        self.connect(cancel_button, qt.SIGNAL("clicked()"), self.reject)
        self.connect(new_button, qt.SIGNAL("clicked()"), lambda:self.new_folder(self))

        self.setLayout(vlayout)

    def accept(self):
        self.feed.title = unicode(self.edit.text())
        self.feed.folder = unicode(self.combo.currentText())
        self.add_feed(self.feed)
        super(NewFeed, self).accept()

    def reject(self):
        del self.document.feedlist[-1]
        super(NewFeed, self).reject()


