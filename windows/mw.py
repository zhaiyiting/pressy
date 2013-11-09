from functools import partial

import me.qtall as qt
import me.utils as ut

from me.windows.libtree import LibTree
from me.windows.projtree import ProjTree
from me.windows.logdock import LogDock
from me.windows.reporttree import ReportTree
from me.windows.stack import StackWidget

from me.dialogs.newprojdlg import NewProjDlg
from me.document.document import Document
from me.document.document import ProjectType


class MainWin(qt.QMainWindow):

    windows = []
    @classmethod
    def createWindow(cls):
        win = cls()
        win.showMaximized()
        cls.windows.append(win)

    def __init__(self,parent = None):
        super(MainWin,self).__init__(parent)
        self.document = Document()
        # status bar
        self.statusBar = qt.QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.setup()
        self.setWindowTitle("Model Explorer")
        self.setWindowIcon(ut.getIcon('me'))
        # toolbar and menubar
        self.__makeTbMenu()
        self.defineViewMenu()

        # add connection
        self.__add_connection()

    def __makeTbMenu(self):
        ''' add toolbar and menu '''
        a= ut.makeAction
        self.actions = {
                'project.new':
                    a(self, 'new QA project', '&New QA project',
                      partial(self.proj_dock.slotNewProj,
                              self.lib_dock.get_section_info,
                              ProjectType.SINGLE_PROJECT),
                      icon='new_qa_proj', key=None),
                'project.new_corner':
                    a(self, 'new corner project', '&New corner project',
                      partial(self.proj_dock.slotNewProj,
                              self.lib_dock.get_section_info,
                              ProjectType.CORNER_PROJECT),
                      icon='new_corner_proj', key=None),
                'project.new_compare':
                    a(self, 'new compare project', '&New compare project',
                      partial(self.proj_dock.slotNewProj,
                              self.lib_dock.get_section_info,
                              ProjectType.COMPARE_PROJECT),
                      icon='new_cmp_proj', key=None),
                'project.load':
                    a(self, 'load project', '&Load project',
                      self.proj_dock.slotLoadProject,
                      icon='load_proj', key=None),
                'project.save':
                    a(self, 'save project', 'Save project',
                      self.proj_dock.slotSaveProject,
                      icon='save_proj', key=None),
                'project.load_wsp':
                    a(self, 'load workspace', '&Load workspace',
                      self.proj_dock.slotLoadWsp,
                      icon=None, key=None),
                'project.save_wsp':
                    a(self, 'save workspace', '&Save workspace',
                      self.proj_dock.slotSaveWsp,
                      icon=None, key=None),

                'library.load':
                    a(self, "load library", '&Load library',
                      self.lib_dock.slotLoadLib,
                      icon="load_lib", key=None),
                'library.check':
                    a(self, "check library", "&Check library",
                      self.lib_dock.slotCheckLibrary,
                      icon=None, key=None),

                'run.run_current_proj':
                    a(self, "run project", "&Run project",
                      self.proj_dock.slotRunProject,
                      icon="run_proj", key=None),
                'run.run_all_proj':
                    a(self, "run all projects", "&Run all projects",
                      self.proj_dock.slotRunAllProjects,
                      icon="run_all_proj", key=None),

                'view.proj_tree':
                    a(self, 'show or hide project tree window', 'Project tree window',
                      None, checkable=True),
                'view.lib_tree':
                    a(self, 'show or hide library tree window', 'Library tree window',
                      None, checkable=True),
                'view.log_dock':
                    a(self, 'show or hide log window', 'Log window',
                      None, checkable=True),
                'view.repo_tree':
                    a(self, 'show or hide report tree window', 'Report tree window',
                      None, checkable=True)
                }

        # create library toolbar
        lib_tb = qt.QToolBar("library toolbar", self)
        lib_tb.setObjectName('library_toolbat')
        self.addToolBar(qt.Qt.TopToolBarArea, lib_tb)
        ut.addToolbarActions(lib_tb, self.actions, ('library.load',))

        # create project toolbar
        project_tb = qt.QToolBar('project toolbar', self)
        project_tb.setObjectName('project_toolbar')
        self.addToolBar(qt.Qt.TopToolBarArea, project_tb)
        ut.addToolbarActions(project_tb, self.actions, ('project.load', 'project.save'))

        # create run toolbar
        run_tb = qt.QToolBar('run toolbar', self)
        run_tb.setObjectName('run_toolbar')
        self.addToolBar(qt.Qt.TopToolBarArea, run_tb)
        ut.addToolbarActions(run_tb, self.actions, ('run.run_current_proj', 'run.run_all_proj'))

        # menu structure
        library_menu = ['library.load', 'library.check']
        proj_menu = [
                'project.new', 'project.load', 
                ['project.projrecent', 'Load Recent',[]],
                '',
                'project.save',
                '',
                'project.load_wsp', 'project.save_wsp']
        view_menu = [
                'view.proj_tree', 'view.lib_tree',
                'view.log_dock', 'view.repo_tree']

        run_menu = ['run.run_current_proj', 'run.run_all_proj']

        menus = [
            ['library', 'Library', library_menu],
            ['project', 'Project', proj_menu],
            ['view', 'View', view_menu],
            ['run', 'Run', run_menu]
            ]
        self.menus = {}
        ut.constructMenus(self.menuBar(), self.menus, menus, self.actions)

    def defineViewMenu(self):
        #FIXME: change the dockwindow status if it closed by click "X" not only through the menu
        view_menu = [
                'view.proj_tree', 'view.lib_tree',
                'view.log_dock', 'view.repo_tree']
        windict = {'view.proj_tree':self.proj_dock,
                'view.lib_tree':self.lib_dock,
                'view.log_dock':self.log_dock,
                'view.repo_tree':self.repo_dock}

        def setVis(win):
            def f():
                win.setVisible(not win.isVisible())
            return f

        for item in view_menu:
            action = self.actions[item]
            if item == 'view.repo_tree':
                action.setChecked(False)
            else:
                action.setChecked(True)
            win = windict[item]
            f = setVis(windict[item])
            action.connect(action, qt.SIGNAL('triggered()'), f)

    def setup(self):
        # report tree
        self.repo_dock = ReportTree(self.document, self)
        self.addDockWidget(qt.Qt.RightDockWidgetArea, self.repo_dock)
        # log window
        self.log_dock = LogDock(self.document, self)
        self.addDockWidget(qt.Qt.BottomDockWidgetArea, self.log_dock)
        # library tree
        self.lib_dock = LibTree(self.document, self)
        self.addDockWidget(qt.Qt.LeftDockWidgetArea, self.lib_dock)
        # project tree
        self.proj_dock = ProjTree(self.document, self)
        self.addDockWidget(qt.Qt.LeftDockWidgetArea, self.proj_dock)
        #main stack widget
        self.stack_widget = StackWidget(self.document, self)
        self.setCentralWidget(self.stack_widget)

        self.tabifyDockWidget(self.lib_dock, self.proj_dock)
        self.lib_dock.raise_()
        self.repo_dock.close()

    def __add_connection(self):
        """add connections between these dockwindows and central stack widget"""
        self.connect(self.proj_dock,qt.SIGNAL('item_clicked'), self.stack_widget.slotDisplay)
