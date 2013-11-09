from functools import partial

import me.qtall as qt
import me.widget.proj_tree as pt
import me.setting as st
import me.utils as ut
from me.dialogs.newprojdlg import NewProjDlg


class ProjTree(qt.QDockWidget):

    def __init__(self, document, parentwin):
        super(ProjTree, self).__init__("Project", parentwin)
        self.setObjectName("projtree")

        self.document = document
        self.widget = qt.QWidget()

        self.treemodel = pt.TreeModel(self)
        self.treeview = qt.QTreeView(self)
        self.treeview.setModel(self.treemodel)
        self.treeview.setHeaderHidden(True)

        # receive change in selection
        self.connect(self.treeview.selectionModel(),
                     qt.SIGNAL('selectionChanged(const QItemSelection &,'
                               'const QItemSelection &)'),
                     self.slotTreeItemsSelected)
        self.connect(self.treeview, qt.SIGNAL('clicked(const QModelIndex &)'),
                     self.slotTreeItemClicked)
        
        self.setWidget(self.treeview)

        # test for flash
        #self.flashtimer = qt.QTimer(self)
        #self.flashon = True
        #self.connect(self.flashtimer, qt.SIGNAL("timeout()"),
        #             self.slotFlashTimeout)
        #self.flashtimer.start(500)

    def slotFlashTimeout(self):
        if self.flashon:
            self.setStyleSheet('background: yellow;')
        else:
            self.setStyleSheet('')
        self.flashon = not self.flashon

    def slotTreeItemsSelected(self):
        pass

    def slotTreeItemClicked(self, index):
        item = index.internalPointer()
        # set the current active project
        self.document.proj_pool.active_proj = self.document.proj_pool.proj_list[item.proj_index]
        self.document.proj_pool.active_index = item.proj_index
        # signal to main stack widget to display item's content
        self.emit(qt.SIGNAL("item_clicked"), item.itemData)

    def slotNewProj(self, f_get_section_info, proj_type):
        """ invoke the project dialog and create one project to document
            then show it in project tree
        """
        section_info = f_get_section_info()
        new_dlg = NewProjDlg(self.parent(), proj_type, section_info, self.document)
        rtn = new_dlg.exec_()
        if rtn:
            self.treemodel.insertProj(self.document.proj_pool.active_proj,
                                      self.document.proj_pool.active_index)
            update_proj = partial(self.treemodel.updateProj,
                                  self.document.proj_pool.active_proj,
                                  self.document.proj_pool.active_index)
            self.connect(self.document.proj_pool.active_proj, qt.SIGNAL('update_proj'), update_proj)

    def contextMenuEvent(self, event):
        """ bring up context menu"""
        pos = event.pos()
        pos = self.treeview.mapFromParent(pos)
        index = self.treeview.indexAt(pos)
        if not index.isValid():
            return
        item = index.internalPointer()
        if item.itemData == "Rule Group":
            m = qt.QMenu(self)
            action_run = self.parent().actions["run.run_current_proj"]
            m.addAction(action_run)
            m.exec_(self.mapToGlobal(event.pos()))
            event.accept()

    def slotRunProject(self):
        """ run current active project"""
        # TODO: need to collect current selected rule group
        current_proj = self.document.proj_pool.active_proj
        if current_proj:
            current_proj.run()

    def slotRunAllProjects(self):
        """ run all projects """
        pass

    def slotLoadProject(self):
        pass

    def slotSaveProject(self):
        pass

    def slotLoadWsp(self):
        pass

    def slotSaveWsp(self):
        pass
