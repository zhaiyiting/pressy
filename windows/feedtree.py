import os.path as osp
import time
import pressy.qtall as qt
import pressy.utils as ut
import pressy.setting as st
import pressy.windows.feed_tree as ft

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
        self.new_folder_btn = ut.create_toolbutton(self, icon = "add_folder",
                                                   tip = "create a new folder",
                                                   triggered = self.slot_new_folder)
        self.new_folder_btn.setIconSize(qt.QSize(18,18))
        btn_layout.addWidget(self.new_folder_btn)

        # delete folder tool button
        self.delete_btn = ut.create_toolbutton(self, icon = "delete",
                                                   tip = "delete one feed or folder",
                                                   triggered = self.slot_del_feed_folder)
        self.delete_btn.setIconSize(qt.QSize(18, 18))
        btn_layout.addWidget(self.delete_btn)
        imagdir = st.icon_path
        gif = osp.join(imagdir, 'refresh.gif')
        self.movie = qt.QMovie(gif)
        qt.QObject.connect(self.movie, qt.SIGNAL("frameChanged(int)"), self.slot_refresh_icon)
        self.refresh_feed_btn.setIcon(qt.QIcon(gif))


        self.pin_btn = ut.create_toolbutton(self, icon = "pin_hold",
                                       toggled = self.slot_auto_hide)
        self.pin_btn.setIconSize(qt.QSize(18,18))
        btn_layout.addStretch()
        btn_layout.addWidget(self.pin_btn)

        self.document = document
        self.parentwin = parentwin
        self.treemodel = ft.TreeModel()
        self.treeview = qt.QTreeView(self)
        self.treeview.setModel(self.treemodel)
        self.treeview.setHeaderHidden(True)
        self.treeview.setDragDropMode(qt.QAbstractItemView.InternalMove)
        self.treemodel.add_feeds(self.document.feedlist, self.document.folder_list)
        self.treeview.expandAll()

        layout.addLayout(btn_layout)
        layout.addWidget(self.treeview)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.current_index = None

        self.connect(self.treeview, qt.SIGNAL("clicked(const QModelIndex &)"),
                     self.slotTreeItemClicked)

        before = self.treeview.mouseReleaseEvent
        def mouseReleaseEvent(e):
            if e.button() == qt.Qt.LeftButton:
                before(e)
        self.treeview.mouseReleaseEvent = mouseReleaseEvent

    def contextMenuEvent(self, event):
        """ rename or mark all read"""
        pos = event.pos()
        pos = self.treeview.mapFromParent(pos)
        index = self.treeview.indexAt(pos)
        if not index.isValid():
            a_refresh = ut.makeAction(self, "refresh all feeds", "&Refresh",
                                      self.slot_refresh_feeds, icon="feed_refresh")
            a_newfolder = ut.makeAction(self, "create a new folder", "New",
                                        self.slot_new_folder, icon="add_folder")
            m = qt.QMenu(self)
            m.addAction(a_refresh)
            m.addAction(a_newfolder)
            m.exec_(self.mapToGlobal(event.pos()))
            event.accept()
            return
        item = index.internalPointer()
        a_rename = ut.makeAction(self, "rename the feed", "&Rename",
                                 lambda: self.slot_rename_item(index), icon="rename")
        a_markall = ut.makeAction(self, "mark all read", "&Mark all read",
                                 lambda : self.slot_mark_all_read(item), icon="mark")
        a_delete = ut.makeAction(self, "delete one feed or folder", "&Delete",
                                 self.slot_del_feed_folder, icon="delete")
        m = qt.QMenu(self)
        m.addAction(a_rename)
        m.addAction(a_markall)
        m.addAction(a_delete)
        m.exec_(self.mapToGlobal(event.pos()))
        event.accept()

    def slot_mark_all_read(self, item):
        self.treemodel.mark_all_read(item)

    def slot_rename_item(self, index):
        rename_dlg = NewName(index, self)
        rename_dlg.exec_()

    def slot_del_feed_folder(self):
        current_index = self.treeview.currentIndex()
        if current_index:
            item = current_index.internalPointer()
            if not item:
                return
            item_data = item.itemData
            if isinstance(item_data, unicode):
                folder_name = item_data
                ret = qt.QMessageBox.question(
                                self, "Question - Pressy",
                                "Do you want to remove folder '%s'?"%folder_name,
                                 qt.QMessageBox.Cancel | qt.QMessageBox.Ok)
                if ret == qt.QMessageBox.Ok:
                    for child in item.childItems:
                        feed = child.itemData
                        self.document.feedlist.remove(feed)
                    folder_index = self.document.folder_list.index(folder_name)
                    self.treemodel.delete_folder(folder_name, folder_index)
                    self.document.folder_list.remove(folder_name)
            else:
                feed = current_index.internalPointer().itemData
                feed_name = feed.title
                ret = qt.QMessageBox.question(
                                self, "Question - Pressy",
                                "Do you want to remove feed '%s'?"%feed_name,
                                 qt.QMessageBox.Cancel | qt.QMessageBox.Ok)
                if ret == qt.QMessageBox.Ok:
                    self.treemodel.delete_feed(current_index)
                    self.document.feedlist.remove(feed)

    def slotTreeItemClicked(self, index):
        """ generate the link """
        item = index.internalPointer()
        self.current_index = index
        item_data = item.itemData
        if not isinstance(item_data, unicode):
            if item_data.id_:
                link = "http://localhost:5000/feed/%s"%item_data.id_
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
        self.movie.start()
        def f_signal():
            self.emit(qt.SIGNAL("update_finished"))
        self.connect(self, qt.SIGNAL("update_finished"), self.slot_refresh_finish)
        self.document.refresh_all(self.treemodel.update_feeds, f_signal)

    def slot_refresh_finish(self):
        self.movie.stop()
        self.emit(qt.SIGNAL("show_update_msg"))

    def slot_refresh_icon(self, frame):
        self.refresh_feed_btn.setIcon(qt.QIcon(self.movie.currentPixmap()))

    def slot_auto_hide(self):
        if self.pin_btn.isChecked():
            self.pin_btn.setIcon(ut.getIcon("pin_release"))
        else:
            self.pin_btn.setIcon(ut.getIcon("pin_hold"))

    def leaveEvent(self, e):
        if self.pin_btn.isChecked():
            main_win = self.parent().parent()
            main_win.holder.show()
            self.hide()
            re_size_list = [0, 10, main_win.splitter.size().width() - 15]
            main_win.splitter.setSizes(re_size_list)

    def slot_add_feed(self, feed):
        new_dlg = NewFeed(feed, self.document, self)
        rtn = new_dlg.exec_()
        self.treeview.expandAll()


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

        self.edit.setFocus()

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

class NewName(qt.QDialog):
    def __init__(self, index, parent=None):
        qt.QDialog.__init__(self, parent)
        self.index = index
        self.folder_list = parent.document.folder_list
        self.tree_model = parent.treemodel
        self.setWindowTitle("New Name")
        self.resize(250, 80)

        self.name_edit = qt.QLineEdit(self)
        self.name_edit.setPlaceholderText("new name")

        self.ok_btn = qt.QPushButton("Ok", self)
        self.cancel_btn = qt.QPushButton("Cancel", self)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn.setFocus()

        layout = qt.QVBoxLayout()
        layout.addWidget(self.name_edit)

        buttonLayout = qt.QHBoxLayout()
        spancerItem2 = qt.QSpacerItem(40, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
        buttonLayout.addItem(spancerItem2)
        buttonLayout.addWidget(self.ok_btn)
        buttonLayout.addWidget(self.cancel_btn)

        self.name_edit.setFocus()

        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def accept(self):
        name = unicode(self.name_edit.text())
        if name:
            item = self.index.internalPointer()
            item_data = item.itemData
            if isinstance(item_data, unicode):
                if not name in self.folder_list:
                    old_name = item.itemData
                    name_index = self.folder_list.index(old_name)
                    self.folder_list.remove(old_name)
                    self.folder_list.insert(name_index, name)
                    item.itemData = name
                    for child in item.childItems:
                        feed = child.itemData
                        feed.folder = name
                    self.tree_model.emit(qt.SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
                              self.index, self.index)
                else:
                    qt.QMessageBox.warning(
                        self, "Error - Pressy",
                        'The folder name "%s" has already exists'%name)
            else:
                feed = item.itemData
                feed.title = name
                self.tree_model.emit(qt.SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
                                     self.index, self.index)

            super(NewName, self).accept()


