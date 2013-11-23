# -*- coding=utf-8 -*-
import sys
import os

try:
    import pressy
except ImportError:
    sys.path.append(
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import pressy

import pressy.qtall as qt

class ImportThread(qt.QThread):
    '''
    initial import the module
    '''
    def run(self):
        import pressy.server
        import pressy.utils
        import pressy.document

def slotMain(splash):
    """ setup the main window """
    from windows.mainwindow import MainWin
    MainWin.createWindow()
    if splash:
        splash.finish(qt.qApp.topLevelWidgets()[0])

def main():
    app = qt.QApplication(sys.argv)
    # splash
    import pressy.setting as st
    splash = qt.QSplashScreen(qt.QPixmap(os.path.join(st.icon_path, 'splash.jpg')))
    splash.show()
    thread = ImportThread()
    qt.QObject.connect( thread, qt.SIGNAL('finished()'),
                        lambda : slotMain(splash))
    thread.start()
    app.exec_()

if __name__ == "__main__":
    main()
