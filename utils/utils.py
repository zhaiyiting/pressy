import os.path as osp
import pressy.setting as st
import pressy.qtall as qt

_iconcache = {}
imagdir = osp.join(st.common['app_path'],'windows','icons') 
def getIcon(icon):
    '''Return a cached QIconSet for the filename in the icons directory'''
    if icon not in _iconcache:
        svg = osp.join(imagdir, icon+'.svg')
        if osp.exists(svg):
            filename = svg
        else:
            filename = osp.join(imagdir,icon+'.png')

        _iconcache[icon] = qt.QIcon(filename)
    return _iconcache[icon]

def makeAction(parent,descr,menutext,slot,icon=None,key=None,
               checkable=False):
    '''A quick way to set up an QAction object.'''
    a = qt.QAction(parent)
    a.setText(menutext)
    a.setStatusTip(descr)
    #a.setToolTip(text)
    if slot:
        parent.connect(a, qt.SIGNAL('triggered()'),slot)
    if icon:
        a.setIcon(getIcon(icon))
    if key:
        a.setShortcut(qt.QKeySequence(key))
    if checkable:
        a.setCheckable(True)
    return a

def addToolbarActions(toolbar, actions, which):
    """Add actions listed in "which" from dict "actions" to toolbar "toolbar".
    """
    for w in which:
        toolbar.addAction(actions[w])

def constructMenus(rootobject, menuout, menutree, actions):
    """Add menus to the output dict from the tree, listing actions
    from actions.

    rootobject: QMenu or QMenuBar to add menus to
    menuout: dict to store menus
    menutree: tree structure to create menus from
    actions: dict of actions to assign to menu items
    """

    for menuid, menutext, actlist in menutree:
        # make a new menu if necessary
        if menuid not in menuout:
            menu = rootobject.addMenu(menutext)
            menuout[menuid] = menu
        else:
            menu = menuout[menuid]

        # add actions to the menu
        for action in actlist:
            if hasattr(action, '__iter__'):
                # recurse for submenus
                constructMenus(menu, menuout, [action], actions)
            elif action == '':
                # blank means separator
                menu.addSeparator()
            else:
                # normal action
                menu.addAction(actions[action])

def create_toolbutton(parent, text = None, shortcut = None,
                      icon = None, tip = None, toggled = None,
                      triggered = None, autoraise = True,
                      text_beside_icon = False):
    ''' create as toolbutton '''
    button = qt.QToolButton(parent)
    if text is not None:
        button.setText(text)
    if icon is not None:
        icon = getIcon(icon)
        button.setIcon(icon)
    if text is not None or tip is not None:
        button.setToolTip(text if tip is None else tip)
    if text_beside_icon:
        button.setToolButtonStyle(qt.Qt.ToolButtonTextBesideIcon)
    button.setAutoRaise(autoraise)
    if triggered is not None:
        qt.QObject.connect(button,qt.SIGNAL('clicked()'), triggered)
    if toggled is not None:
        qt.QObject.connect(button,qt.SIGNAL('toggled(bool)'), toggled)
        button.setCheckable(True)
    if shortcut is not None:
        button.setShortcut(shortcut)
    return button
