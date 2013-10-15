# -*- coding=utf-8 -*-
import sys
import os

# monkey patching for run the main inside the package
import __init__ as pressy
thisdir = os.path.dirname(os.path.abspath(__file__))
pressy.__path__ = [thisdir]
pressy.__name = "pressy"
sys.module['pressy'] = pressy

import pressy.qtall as qt

def mainwindow():
    """ setup the main window """
    form windows.mainwindow import MainWin
    MainWin.createWindow()

def main():
    app = qt.QApplication(sys.argv)
    mainwindow()
    app.exec_()

if __name__ == "__main__":
    main()
