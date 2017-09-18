# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Source: http://www.gnu.org/licenses/gpl-howto.html

# It is often said when developing interfaces that you need to fail fast,
# and iterate often. When creating a UI, you will make mistakes. Just keep
# moving forward, and remember to keep your UI out of the way.
# http://blog.teamtreehouse.com/10-user-interface-design-fundamentals

from __future__ import division, unicode_literals, print_function

print('Starting WHAT...')

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QSplashScreen, QMainWindow,
                             QMessageBox, QTabWidget, QTextEdit, QSplitter,
                             QWidget, QGridLayout, QDesktopWidget, QTabBar)
import sys

app = QApplication(sys.argv)

splash = QSplashScreen(QPixmap('ressources/splash.png'),
                       Qt.WindowStaysOnTopHint)
splash.show()

import platform
import os
import numpy as np

ft = app.font()
ft.setPointSize(11)
if platform.system() == 'Windows':
    ft.setFamily('Segoe UI')
app.setFont(ft)

splash.showMessage("Starting WHAT, please wait ...",
                   Qt.AlignBottom | Qt.AlignCenter)

# Standard library imports :

import csv
from time import ctime
from os import makedirs, path
import copy

from multiprocessing import freeze_support
import tkinter
import tkinter.filedialog
import tkinter.messagebox

# Local imports :

import common.database as db
import custom_widgets as MyQWidget
import HydroPrint2 as HydroPrint
import HydroCalc2 as HydroCalc
from meteo import dwnld_weather_data
from meteo.gapfill_weather_gui import GapFillWeatherGUI
from meteo.dwnld_weather_data import DwnldWeatherWidget

from about import AboutWhat
from projet.manager_projet import ProjetManager
from projet.manager_data import DataManager
from common import IconDB, StyleDB, QToolButtonBase
from _version import __version__

freeze_support()

# DATABASES :

headerDB = []


class WHAT(QMainWindow):

    def __init__(self, parent=None):
        super(WHAT, self).__init__(parent)

        self.setWindowTitle(__version__)
        self.setWindowIcon(IconDB().master)

        if platform.system() == 'Windows':
            import ctypes
            myappid = 'what_application'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                myappid)

        # ---------------------------------------------------- Preferences ----

        self.whatPref = WHATPref(self)
        self.projectfile = self.whatPref.projectfile
        self.projectdir = path.dirname(self.projectfile)

        # ------------------------------------------------- Projet Manager ----

        self.pmanager = ProjetManager(self)
        self.pmanager.currentProjetChanged.connect(self.new_project_loaded)

        self.dmanager = DataManager(pm=self.pmanager)
        self.dmanager2 = DataManager(pm=self.pmanager)

        # ----------------------------------------------------------- Init ----

        self.__initUI__()

        result = self.pmanager.load_project(self.projectfile)
        if result is False:
            self.tab_dwnld_data.setEnabled(False)
            self.tab_fill_weather_data.setEnabled(False)
            self.tab_hydrograph.setEnabled(False)
            self.tab_hydrocalc.setEnabled(False)

            msgtxt = '''
                     Unable to read the project file.<br><br>
                     "%s" does not exist.<br><br> Please open an existing
                     project or create a new one.
                     ''' % self.projectfile

            btn = QMessageBox.Ok
            QMessageBox.warning(self, 'Warning', msgtxt, btn)

    def __initUI__(self):

        # ------------------------------------------------------ DATABASES ----

        # http://stackoverflow.com/questions/423379/
        # using-global-variables-in-a-function-other-
        # than-the-one-that-created-them

        global headerDB
        headerDB = db.FileHeaders()

        # ----------------------------------------------------- TAB WIDGET ----

        # ---- download weather data ----

        self.tab_dwnld_data = DwnldWeatherWidget(self)
        self.tab_dwnld_data.set_workdir(self.projectdir)

        # ---- gapfill weather data ----

        self.tab_fill_weather_data = GapFillWeatherGUI(self)
        self.tab_fill_weather_data.set_workdir(self.projectdir)

        # ---- hydrograph ----

        self.tab_hydrograph = HydroPrint.HydroprintGUI(self.dmanager)
        self.tab_hydrocalc = HydroCalc.WLCalc(self.dmanager)

        # ---- TABS ASSEMBLY ----

        self.tab_bar = TabBar(self)

        Tab_widget = QTabWidget()
        Tab_widget.setTabBar(self.tab_bar)

        Tab_widget.addTab(self.tab_dwnld_data, 'Download Weather')
        Tab_widget.addTab(self.tab_fill_weather_data, 'Gap-Fill Weather')
        Tab_widget.addTab(self.tab_hydrograph, 'Plot Hydrograph')
        Tab_widget.addTab(self.tab_hydrocalc, 'Analyze Hydrograph')
        Tab_widget.setCornerWidget(self.pmanager)

        Tab_widget.currentChanged.connect(self.sync_datamanagers)

        # --------------------------------------------------- Main Console ----

        self.main_console = QTextEdit()
        self.main_console.setReadOnly(True)
        self.main_console.setLineWrapMode(QTextEdit.NoWrap)

        style = 'Regular'
        family = StyleDB().fontfamily
        size = self.whatPref.fontsize_console
        fontSS = ('font-style: %s;'
                  'font-size: %s;'
                  'font-family: %s;'
                  ) % (style, size, family)
        self.main_console.setStyleSheet("QWidget{%s}" % fontSS)

        msg = '<font color=black>Thanks for using %s.</font>' % __version__
        self.write2console(msg)
        self.write2console('<font color=black>'
                           'Please report any bug or wishful feature at'
                           ' jean-sebastien.gosselin@ete.inrs.ca.'
                           '</font>')

        # ---- Signal Piping ----

        issuer = self.tab_dwnld_data
        issuer.ConsoleSignal.connect(self.write2console)

        issuer = self.tab_fill_weather_data
        issuer.ConsoleSignal.connect(self.write2console)

        issuer = self.tab_hydrograph
        issuer.ConsoleSignal.connect(self.write2console)

        # ------------------------------------------------ Splitter Widget ----

        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)

        splitter.addWidget(Tab_widget)
        splitter.addWidget(self.main_console)

        splitter.setCollapsible(0, True)
        splitter.setStretchFactor(0, 100)
        # Forces initially the main_console to its minimal height:
        splitter.setSizes([100, 1])

        # ------------------------------------------------------ Main Grid ----

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        mainGrid = QGridLayout(main_widget)

        mainGrid.addWidget(splitter, 0, 0)
        mainGrid.addWidget(self.tab_fill_weather_data.pbar, 1, 0)
        mainGrid.addWidget(self.tab_dwnld_data.pbar, 2, 0)

    # =========================================================================

    def show(self):
        super(WHAT, self).showMaximized()
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # =========================================================================

    def write2console(self, text):
        # This function is the bottle neck through which all messages writen
        # in the console must go through.
        textime = '<font color=black>[%s] </font>' % ctime()[4:-8]
        self.main_console.append(textime + text)

    # =========================================================================

    def sync_datamanagers(self):
        current = self.tab_bar.currentIndex()
        if current == 3:
            self.tab_hydrocalc.right_panel.addWidget(self.dmanager, 0, 0)
        elif current == 2:
            self.tab_hydrograph.right_panel.addWidget(self.dmanager, 0, 0)

    def new_project_loaded(self):

        filename = self.pmanager.projet.filename
        dirname = os.path.dirname(filename)

        # Update WHAT.pref file :

        self.whatPref.projectfile = filename
        self.whatPref.save_pref_file()

        # Update UI :

        self.tab_dwnld_data.setEnabled(True)
        self.tab_hydrograph.setEnabled(True)
        self.tab_hydrocalc.setEnabled(True)

        # Update child widgets :

        # ---- dwnld_weather_data ----

        lat = self.pmanager.projet.lat
        lon = self.pmanager.projet.lon

        self.tab_dwnld_data.set_workdir(dirname)
        self.tab_dwnld_data.search4stations.lat_spinBox.setValue(lat)
        self.tab_dwnld_data.search4stations.lon_spinBox.setValue(lon)

        # ---- fill_weather_data ----

        self.tab_fill_weather_data.set_workdir(dirname)
        self.tab_fill_weather_data.load_data_dir_content()

    # =========================================================================

    def closeEvent(self, event):
        print(event)
        print('Closing projet')
        self.pmanager.close_projet()
        print('Closing WHAT')
        event.accept()


# =============================================================================
# =============================================================================


class WHATPref(object):
    """
    This class contains all the preferences relative to the WHAT interface,
    including:

    projectfile: Path of the project that was opened when last time
                 the program was closed.

    language: Language in which the GUI is displayed (not the labels
              of graphs).
    """

    def __init__(self, parent=None):  # =======================================

        self.projectfile = os.path.join(
            '..', 'Projects', 'Example', 'Example.what')
        self.language = 'English'
        self.fontsize_general = '14px'
        self.fontsize_console = '12px'
        self.fontsize_menubar = '12px'

        self.load_pref_file()

    def save_pref_file(self):  # ==============================================

        print('\nSaving WHAT preferences to file...')

        fcontent = [['Project File:', os.path.relpath(self.projectfile)],
                    ['Language:', self.language],
                    ['Font-Size-General:', self.fontsize_general],
                    ['Font-Size-Console:', self.fontsize_console],
                    ['Font-Size-Menubar:', self.fontsize_menubar]]

        with open('WHAT.pref', 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
            writer.writerows(fcontent)

        print('WHAT preferences saved.')

    def load_pref_file(self, circloop=False):  # ==============================

        # cicrcloop argument is a protection to prevent a circular loop
        # in case something goes wrong.

        try:
            with open('WHAT.pref', 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f, delimiter='\t'))

            self.projectfile = reader[0][1]
            if platform.system() == 'Linux':
                self.projectfile = self.projectfile.replace('\\', '/')

            self.language = reader[1][1]
            self.fontsize_general = reader[2][1]
            self.fontsize_console = reader[3][1]
            self.fontsize_menubar = reader[4][1]

        except Exception as e:
            print(e)

            # Default values will be kept and a new .pref file will be
            # generated :

            print(('No valid "WHAT.pref" file found. '
                   'A new one has been created from default.'))
            self.save_pref_file()

            if circloop is False:
                # Rerun method to load default file :
                self.load_pref_file(circloop=True)
            else:
                raise e


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# http://stackoverflow.com/a/20098415/4481445
# http://stackoverflow.com/a/12429054/4481445

class TabBar(QTabBar):
    def __init__(self, parent=None):
        super(TabBar, self).__init__(parent=None)

        self.aboutwhat = AboutWhat(parent=parent)

        self.__oldIndex = -1
        self.__newIndex = -1
        self.currentChanged.connect(self.storeIndex)

        self.about_btn = QToolButtonBase(IconDB().info)
        self.about_btn.setIconSize(QSize(20, 20))
        self.about_btn.setFixedSize(32, 32)
        self.about_btn.setToolTip('About WHAT...')
        self.about_btn.setParent(self)
        self.movePlusButton()  # Move to the correct location

        self.about_btn.clicked.connect(self.aboutwhat.show)

    def tabSizeHint(self, index):
        width = QTabBar.tabSizeHint(self, index).width()
        return QSize(width, 32)

    def sizeHint(self):
        sizeHint = QTabBar.sizeHint(self)
        w = sizeHint.width() + self.about_btn.size().width()
        # h = sizeHint.height()
        return QSize(w, 32)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.movePlusButton()

    def tabLayoutChange(self):
        super().tabLayoutChange()
        self.movePlusButton()

    def movePlusButton(self):
        x = 0
        for i in range(self.count()):
            x += self.tabRect(i).width()

        # Set the plus button location in a visible area
        y = self.geometry().top()
        self.about_btn.move(x, y)

    # =========================================================================

    def storeIndex(self, index):
        self.__oldIndex = copy.copy(self.__newIndex)
        self.__newIndex = index

    def previousIndex(self):
        return self.__oldIndex


# =============================================================================
# =============================================================================


if __name__ == '__main__':
    import logging

    logging.basicConfig(filename='WHAT.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s:%(message)s')
    try:
        main = WHAT()
        main.show()
        splash.finish(main)
        sys.exit(app.exec_())
    except Exception as e:
        logging.exception(str(e))
        raise e
