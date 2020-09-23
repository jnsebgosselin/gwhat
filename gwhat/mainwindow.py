# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Source: http://www.gnu.org/licenses/gpl-howto.html

# It is often said when developing interfaces that you need to fail fast,
# and iterate often. When creating a UI, you will make mistakes. Just keep
# moving forward, and remember to keep your UI out of the way.
# http://blog.teamtreehouse.com/10-user-interface-design-fundamentals

from __future__ import division, unicode_literals, print_function

print('Starting GWHAT...')

import matplotlib as mpl
mpl.use('Qt5Agg')

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QSplitter,
                             QWidget, QGridLayout, QTextBrowser)
import sys
app = QApplication(sys.argv)

from gwhat.widgets.splash import SplashScrn
splash = SplashScrn()

import platform

ft = app.font()
ft.setPointSize(11)
if platform.system() == 'Windows':
    ft.setFamily('Segoe UI')
app.setFont(ft)

from gwhat import __namever__, __appname__
splash.showMessage("Starting %s..." % __namever__)

# ---- Standard library imports
from time import ctime
import os.path as osp

from multiprocessing import freeze_support
import tkinter
import tkinter.filedialog
import tkinter.messagebox

# ---- Local imports
from gwhat.config.main import CONF
from gwhat.config.ospath import save_path_to_configs, get_path_from_configs

import gwhat.HydroPrint2 as HydroPrint
import gwhat.HydroCalc2 as HydroCalc
from gwhat.widgets.tabwidget import TabWidget
from gwhat.projet.manager_projet import ProjetManager
from gwhat.projet.manager_data import DataManager
from gwhat.common import StyleDB
from gwhat.utils import icons

freeze_support()


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setWindowTitle(__namever__)
        self.setWindowIcon(icons.get_icon('master'))

        if platform.system() == 'Windows':
            import ctypes
            myappid = 'gwhat_application'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                myappid)

        # Setup the project manager. and data managers.
        splash.showMessage("Initializing project and data managers...")
        self.pmanager = ProjetManager(self)
        self.pmanager.currentProjetChanged.connect(self.new_project_loaded)

        # Setup the data manager.
        self.dmanager = DataManager(parent=self, pm=self.pmanager)
        self.dmanager.setMaximumWidth(250)
        self.dmanager.sig_new_console_msg.connect(self.write2console)

        # Generate the GUI.
        self.__initUI__()
        splash.finish(self)

        # Load the last opened project.
        projectfile = get_path_from_configs('main', 'last_project_filepath')
        result = self.pmanager.load_project(projectfile)
        if result is False:
            self.tab_hydrograph.setEnabled(False)
            self.tab_hydrocalc.setEnabled(False)

    def __initUI__(self):
        """
        Setup the GUI of the main window.
        """
        # Setup the main console.
        splash.showMessage("Initializing main window...")
        self.main_console = QTextBrowser()
        self.main_console.setReadOnly(True)
        self.main_console.setLineWrapMode(QTextEdit.NoWrap)
        self.main_console.setOpenExternalLinks(True)

        style = 'Regular'
        family = StyleDB().fontfamily
        size = CONF.get('main', 'fontsize_console')
        fontSS = ('font-style: %s;'
                  'font-size: %s;'
                  'font-family: %s;'
                  ) % (style, size, family)
        self.main_console.setStyleSheet("QWidget{%s}" % fontSS)

        msg = '<font color=black>Thanks for using %s.</font>' % __appname__
        self.write2console(msg)
        msg = ('Please help GWHAT by reporting bugs on our '
               '<a href="https://github.com/jnsebgosselin/gwhat/issues">'
               'Issues Tracker</a>.')
        self.write2console('<font color=black>%s</font>' % msg)

        # Setup the tab plot hydrograph.
        splash.showMessage("Initializing plot hydrograph...")
        self.tab_hydrograph = HydroPrint.HydroprintGUI(self.dmanager)
        self.tab_hydrograph.ConsoleSignal.connect(self.write2console)

        # Setup the tab analyse hydrograph.
        splash.showMessage("Initializing analyse hydrograph...")
        self.tab_hydrocalc = HydroCalc.WLCalc(self.dmanager)
        self.tab_hydrocalc.sig_new_mrc.connect(
            self.tab_hydrograph.mrc_wl_changed)
        self.tab_hydrocalc.rechg_eval_widget.sig_new_gluedf.connect(
            self.tab_hydrograph.glue_wl_changed)

        # Add each tab to the tab widget.
        self.tab_widget = TabWidget()
        self.tab_widget.addTab(self.tab_hydrograph, 'Plot Hydrograph')
        self.tab_widget.addTab(self.tab_hydrocalc, 'Analyze Hydrograph')
        self.tab_widget.setCornerWidget(self.pmanager)
        self.tab_widget.currentChanged.connect(self.sync_datamanagers)
        self.sync_datamanagers()

        # Setup the splitter widget.
        splitter = QSplitter(Qt.Vertical, parent=self)
        splitter.addWidget(self.tab_widget)
        splitter.addWidget(self.main_console)

        splitter.setCollapsible(0, True)
        splitter.setStretchFactor(0, 100)
        # Forces initially the main_console to its minimal height:
        splitter.setSizes([100, 1])

        # Setup the layout of the main widget.
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        mainGrid = QGridLayout(main_widget)

        mainGrid.addWidget(splitter, 0, 0)
        mainGrid.addWidget(
            self.tab_hydrocalc.rechg_eval_widget.progressbar, 3, 0)

    def write2console(self, text):
        """
        This function is the bottle neck through which all messages writen
        in the console must go through.
        """
        textime = '<font color=black>[%s] </font>' % ctime()[4:-8]
        self.main_console.append(textime + text)

    def sync_datamanagers(self):
        """
        Move the data manager from tab _Plot Hydrograph_ to tab
        _Analyze Hydrograph_ and vice-versa.
        """
        current = self.tab_widget.tabBar().currentIndex()
        if current == 0:
            self.tab_hydrograph.right_panel.addWidget(self.dmanager, 0, 0)
        elif current == 1:
            self.tab_hydrocalc.right_panel.addWidget(self.dmanager, 0, 0)

    def new_project_loaded(self):
        """Handles when a new project is loaded in the project manager."""

        # Save the project file path in the configs.
        save_path_to_configs('main', 'last_project_filepath',
                             self.pmanager.projet.filename)

        # Update the GUI.
        self.tab_hydrograph.setEnabled(True)
        self.tab_hydrocalc.setEnabled(True)

    def closeEvent(self, event):
        """Qt method override to close the project before close the app."""
        print('Closing projet')
        self.pmanager.close()
        self.tab_hydrocalc.close()
        print('Closing GWHAT')
        event.accept()

    def show(self):
        """
        Extend Qt method.
        """
        super().show()


def except_hook(cls, exception, traceback):
    """
    Used to override the default sys except hook so that this application
    doesn't automatically exit when an unhandled exception occurs.

    See this StackOverflow answer for more details :
    https://stackoverflow.com/a/33741755/4481445
    """
    sys.__excepthook__(cls, exception, traceback)


# %% if __name__ == '__main__'

if __name__ == '__main__':
    sys.excepthook = except_hook
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
