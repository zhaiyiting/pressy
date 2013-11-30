import pressy.qtall as qt
import pressy.utils as ut
from pressy.document.feed import Feed

class TreeItem(object):
    def __init__(self, data, parent=None): 
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        if row > len(self.childItems) - 1:
            return
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

    #def hasChild(self, item):
    #    if item in self.childItems:
    #        return True
    #    else:
    #        return False

    def __eq__(self, other):
        other_item_data = other.itemData
        self_item_data = self.itemData
        if type(other_item_data) != type(self_item_data):
            return False
        if isinstance(self_item_data, unicode):
            if self_item_data == other_item_data:
                return True
            else:
                return False
        else:
            if self_item_data.id_ == other_item_data.id_:
                return True
            else:
                return False

class TreeModel(qt.QAbstractItemModel):

    def __init__(self, parentwin=None):
        super(TreeModel, self).__init__(parentwin)
        self.folder_item = []

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self.folder_item)
        else:
            parentItem = parent.internalPointer()
            return parentItem.childCount()

    def data(self, index, role):
        if not index.isValid():
            return qt.QVariant()
        item = index.internalPointer()
        item_data = item.itemData
        if role == qt.Qt.DisplayRole:
            if isinstance(item_data, unicode):
                return item_data
            else:
                unread_num = len([entrie for entrie in item_data.entries if not entrie.has_read])
                if unread_num:
                    return "[%d]"%unread_num + item_data.title
                else:
                    return item_data.title
        elif role == qt.Qt.FontRole:
            font = qt.QFont()
            if not isinstance(item_data, unicode):
                unread_num = len([entrie for entrie in item_data.entries if not entrie.has_read])
                if unread_num:
                    font.setBold(True)
            return font
        elif role == qt.Qt.DecorationRole:
            if isinstance(item_data, unicode):
                return ut.getIcon("folder")
            return ut.getIcon(item_data.icon)

    def index(self, row, column, parent=qt.QModelIndex()):
        if row < 0 or column != 0:
            return qt.QModelIndex()
        if not parent.isValid():
            if row > len(self.folder_item) - 1:
                return qt.QModelIndex()
            folder_item = self.folder_item[row]
            item_index = self.createIndex(row, column, folder_item)
            folder_item.index = item_index
            return item_index
        else:
            parentItem = parent.internalPointer()
            childItem = parentItem.child(row)
            if childItem:
                item_index = self.createIndex(row, column, childItem)
                childItem.index = item_index
                return item_index
            else:
                return qt.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return qt.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if not parentItem:
            return qt.QModelIndex()
        par_paritem = parentItem.parent()
        if par_paritem:
            return self.createIndex(parentItem.row(), 0, parentItem)
        else:
            row = self.folder_item.index(parentItem)
            return self.createIndex(row, 0, parentItem)

    def hasChildren(self, parent=qt.QModelIndex()):
        if not parent.isValid():
            return True
        else:
            parent_item = parent.internalPointer()
            if parent_item.childCount():
                return True
            else:
                return False

    def add_feed(self, feed):
        folder = feed.folder
        pra_index = None
        pra_item = None
        for i,it in enumerate(self.folder_item):
            item_data = it.itemData
            if item_data == folder:
                pra_index = self.index(i, 0, qt.QModelIndex())
                pra_item = it
                break
        start = pra_item.childCount()
        self.beginInsertRows(pra_index, start, start)
        new_item = TreeItem(feed, pra_item)
        pra_item.appendChild(new_item)
        self.endInsertRows()
        return True

    def add_feeds(self, feeds, folders):
        if not feeds and not folders:
            # add default folder
            self.add_folder(u"Feeds")
            return
        for folder in folders:
            self.add_folder(folder)
        for feed in feeds:
            self.add_feed(feed)
        return True

    def add_folder(self, folder_name):
        if not folder_name:
            return
        index = qt.QModelIndex()
        start = len(self.folder_item)
        self.beginInsertRows(index, start, start)
        new_item = TreeItem(folder_name)
        self.folder_item.append(new_item)
        self.endInsertRows()
        return True

    def delete_feed(self, index):
        parent = self.parent(index)
        child_item = index.internalPointer()
        parent_item = child_item.parentItem
        row = child_item.row()
        self.beginRemoveRows(parent, row, row)
        parent_item.childItems.remove(child_item)
        self.endRemoveRows()

    def delete_folder(self, folder_name, folder_index):
        parent = qt.QModelIndex()
        self.beginRemoveRows(parent, folder_index, folder_index)
        del self.folder_item[folder_index]
        self.endRemoveRows()

    def update_feeds(self, feeds):
        for feed in feeds:
            folder = feed.folder
            tree_item = TreeItem(folder)
            if tree_item in self.folder_item:
                index = self.folder_item.index(tree_item)
                parent = self.folder_item[index]
                feed_tree_item = TreeItem(feed)
                if feed_tree_item in parent.childItems:
                    feed_index = parent.childItems.index(feed_tree_item)
                    item = parent.childItems[feed_index]
                    index = item.index
                    self.emit(qt.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)

    def mark_all_read(self, item):
        feed = item.itemData
        if isinstance(feed, unicode):
            for child in item.childItems:
                feed = child.itemData
                for entrie in feed.entries:
                    entrie.has_read = True
                index = child.index
                self.emit(qt.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        else:
            for entrie in feed.entries:
                entrie.has_read = True
            index = item.index
            self.emit(qt.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)


    def supportedDropActions(self):
        return qt.Qt.MoveAction

    def flags(self, index):
        if not index.isValid():
            return qt.Qt.NoItemFlags
        return qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable | \
               qt.Qt.ItemIsDragEnabled | qt.Qt.ItemIsDropEnabled

    def mimeTypes(self):
        return ["application"]

    def mimeData(self, indexes):
        mimeData = qt.QMimeData()
        fakeData = qt.QByteArray()
        mimeData.setData("application", fakeData)

        for index in indexes:
            if not index.isValid():
                continue
            item = index.internalPointer()
            feed = item.itemData
            if isinstance(feed, unicode):
                return
            self.move_item = item
            return mimeData

    def dropMimeData(self, data, action, row, column, parent):
        if not parent.isValid():
            parent = self.index(row, column, qt.QModelIndex())
            start = 0
        else:
            start = row
            parent_item = parent.internalPointer()
            print parent_item.itemData.title()
            self.beginInsertRows(parent, start, start)
            parent_item.childItems.insert(start, self.move_item)
            self.move_item.parentItem.childItems.remove(self.move_item)
            self.move_item.parentItem = parent_item
            self.endInsertRows()
        return True


