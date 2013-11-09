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

    #def __eq__(self, other):
    #    if other.parentItem == self.parentItem and \
    #        other.itemData == self.itemData and \
    #        other.proj_index == self.proj_index:
    #        return True
    #    else:
    #        return False

class TreeModel(qt.QAbstractItemModel):

    def __init__(self, parentwin=None):
        super(TreeModel, self).__init__(parentwin)
        root_fake_feed = Feed("")
        root_fake_feed.title = "Feeds"
        root_fake_feed.icon = "root_folder"
        self.root = TreeItem(root_fake_feed)

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        if not parent.isValid():
            return 1
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()

    def flags(self, index):
        if not index.isValid():
            return qt.Qt.NoItemFlags
        return qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable

    def data(self, index, role):
        if not index.isValid():
            return None
        item = index.internalPointer()
        item_data = item.itemData
        if role == qt.Qt.DisplayRole:
            unread_num = len([entrie for entrie in item_data.entries if not entrie.has_read])
            if unread_num:
                return "[%d]"%unread_num + item_data.title
            else:
                return item_data.title
        elif role == qt.Qt.FontRole:
            font = qt.QFont()
            unread_num = len([entrie for entrie in item_data.entries if not entrie.has_read])
            if unread_num:
                font.setBold(True)
            return font
        elif role == qt.Qt.DecorationRole:
            return ut.getIcon(item_data.icon) 

    def index(self, row, column, parent=qt.QModelIndex()):
        if not parent.isValid():
            parent_item = self.root
            item_index = self.createIndex(row, column, parent_item)
            parent_item.index = item_index
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

        return self.createIndex(parentItem.row(), 0, parentItem)

    def add_feed(self, feed):
        root_index = self.root.index
        start = self.root.childCount()
        new_item = TreeItem(feed, self.root)
        self.beginInsertRows(root_index, start, start+1)
        self.root.appendChild(new_item)
        self.endInsertRows()
        self.emit(qt.SIGNAL("layoutChanged()"))
        return True

    def add_feeds(self, feeds):
        if not feeds:
            return
        #root_index = self.root.index
        root_index = self.index(0, 0) 
        start = self.root.childCount()
        self.beginInsertRows(root_index, start, start+len(feeds))
        for feed in feeds:
            new_item = TreeItem(feed, self.root)
            self.root.appendChild(new_item)
        self.endInsertRows()
        self.emit(qt.SIGNAL("layoutChanged()"))
        return True

