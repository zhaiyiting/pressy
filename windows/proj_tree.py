import os.path as osp
import me.qtall as qt
import me.utils as ut
from me.document.document import ProjectType as pt


class TreeItem(object):
    def __init__(self, data, proj_index, parent=None, checkable=False):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.proj_index = proj_index
        if checkable:
            self.checked = True

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

    def hasChild(self, item):
        if item in self.childItems:
            return True
        else:
            return False

    def __eq__(self, other):
        if other.parentItem == self.parentItem and \
            other.itemData == self.itemData and \
            other.proj_index == self.proj_index:
            return True
        else:
            return False


class TreeModel(qt.QAbstractItemModel):
    qa_index = 0
    corner_index = 1
    compare_index = 2
    def __init__(self, parentwin=None, rootitem_list=[]):
        super(TreeModel, self).__init__(parentwin)
        self.rootitem_list = rootitem_list

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == qt.Qt.DisplayRole:
            return item.itemData
        elif role == qt.Qt.DecorationRole:
            item_data = item.itemData
            if item_data == 'Setup Group':
                return ut.getIcon('setup_group')
            elif item_data == 'Rule Group':
                return ut.getIcon('rule_group')

            item_parent = item.parent()
            if item_parent:
                parent_data = item_parent.itemData
                if parent_data == 'Setup Group':
                    return ut.getIcon('setup_item')
                elif parent_data == 'Rule Group':
                    return ut.getIcon('rule_item')
                elif parent_data in ['QA', 'Corner', 'Compare']:
                    return ut.getIcon("project_item")
            else:
                return None

        elif role == qt.Qt.CheckStateRole:
            if hasattr(item, "checked"):
                if item.checked:
                    return qt.QVariant(qt.Qt.Checked)
                else:
                    return qt.QVariant(qt.Qt.Unchecked)
            else:
                return qt.QVariant()

    def setData(self, index, value, role):
        if role == qt.Qt.CheckStateRole:
            item = index.internalPointer()
            if item:
                if value == qt.Qt.Checked:
                    item.checked = True
                else:
                    item.checked = False
                self.emit(qt.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
            childCount = item.childCount()
            for i in range(childCount):
                child_index = self.index(i, 0, index)
                self.setData(child_index, value, role)
        return True

    def flags(self, index):
        if not index.isValid():
            return qt.Qt.NoItemFlags
        item = index.internalPointer()
        if hasattr(item, "checked"):
            return qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable | qt.Qt.ItemIsUserCheckable
        else:
            return qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable | qt.Qt.ItemIsEditable | qt.Qt.ItemIsDragEnabled | qt.Qt.ItemIsDropEnabled

    def index(self, row, column, parent=qt.QModelIndex()):
        if not self.rootitem_list:
            return qt.QModelIndex()
        if not parent.isValid():
            parent_item = self.rootitem_list[row]
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

    def rowCount(self, parent):
        if not parent.isValid():
            return 1
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def insertProj(self, proj, proj_index):
        parent = qt.QModelIndex()
        proj_name = proj.proj_name
        proj_dic = proj.tree
        proj_type = proj.proj_type
        # current root item name list
        root_name_list = [root.data for root in self.rootitem_list]
        lib_name = "&".join(proj.section_info.keys())
        if lib_name in root_name_list:
            index = root_name_list.index(lib_name)
            root = self.root_item[index]
            root_index = self.index(0, 0, parent)
            if proj_type == pt.SINGLE_PROJECT:
                parent = self.index(self.qa_index, 0, root_index)
            elif proj_type == pt.CORNER_PROJECT:
                parent = self.index(self.corner_index, 0, root_index)
            elif proj_type == pt.COMPARE_PROJECT:
                parent = self.index(self.compare_index, 0, root_index)
            parent_item = parent.internalPointer()
            child_num = parent_item.childCount()
            start = child_num
            end = child_num + 1
            self.beginInsertRows(parent, start, end)
            self.__new_proj(root, proj_name, proj_dic, proj_index, proj_type)
            self.endInsertRows()
        else:
            if self.rootitem_list:
                start = len(self.rootItem_list)
                end = start + 1
            else:
                start = 0
                end = 1
            root = TreeItem(lib_name, proj_index)
            qa_item = TreeItem("QA", 0, root)
            corner_item = TreeItem("Corner", 0, root)
            compare_item = TreeItem("Compare", 0, root)
            root.appendChild(qa_item)
            root.appendChild(corner_item)
            root.appendChild(compare_item)
            self.rootitem_list.append(root)
            self.beginInsertRows(parent, start, end)
            self.__new_proj(root, proj_name, proj_dic, proj_index, proj_type)
            self.endInsertRows()
        return True

    def updateProj(self, proj, proj_index, start, num):
        """update the project tree when insert new rule group"""
        proj_dic = proj.tree
        proj_type = proj.proj_type
        root_item = self.rootitem_list[proj_index]
        parent = qt.QModelIndex()
        if proj_type == pt.SINGLE_PROJECT:
            root = root_item.child(self.qa_index)
        elif proj_type == pt.CORNER_PROJECT:
            root = root_item.child(self.corner_index)
        elif proj_type == pt.COMPARE_PROJECT:
            root = root_item.child(self.compare_index)
        item = TreeItem(proj.name, proj_index, root)
        if root.hasChild(item):
            index = root.childItems.index(item)
            parent_item = root.child(index)
            parent = parent_item.index
        start = parent_item.childCount()
        self.beginInsertRows(parent, start, start + num)
        self._traverse_proj_dict(root, proj_dic, proj_index)
        self.endInsertRows()
        #self.emit(qt.SIGNAL("layoutChanged()"))
        return True

    def __new_proj(self, root_item, proj_name, proj_dic, proj_index, proj_type):
        if proj_type == pt.SINGLE_PROJECT:
            root = root_item.child(0)
        elif proj_type == pt.CORNER_PROJECT:
            root = root_item.child(1)
        elif proj_type == pt.COMPARE_PROJECT:
            root = root_item.child(2)
        proj_root = TreeItem(proj_name, proj_index, root)
        self._traverse_proj_dict(proj_root, proj_dic, proj_index)
        root.appendChild(proj_root)

    def _traverse_proj_dict(self, root, dic, proj_index, checkable=False):
        """ to construct the root item of one project tree"""
        if not dic:
            return
        for name in dic:
            # all sub item of rule group are checkable
            tree_item = TreeItem(name, proj_index, root, checkable)
            if name == "Rule Group":
                checkable = True
            if not root.hasChild(tree_item):
                root.appendChild(tree_item)
            else:
                tree_item = root.childItems[root.childItems.index(tree_item)]
            self._traverse_proj_dict(tree_item,dic[name],proj_index, checkable)
        return root

