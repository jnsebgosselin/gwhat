# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

GHWAT is free software: you can redistribute it and/or modify
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

print('Starting GWHAT...')

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QResizeEvent
from PyQt5.QtWidgets import (QApplication, QSplashScreen, QMainWindow,
                             QMessageBox, QTabWidget, QTextEdit, QSplitter,
                             QWidget, QGridLayout, QDesktopWidget, QTabBar)
import sys
app = QApplication(sys.argv)

from gwhat.widgets.splash import SplashScrn
splash = SplashScrn()

import platform
import os
import numpy as np

ft = app.font()
ft.setPointSize(11)
if platform.system() == 'Windows':
    ft.setFamily('Segoe UI')
app.setFont(ft)

from gwhat import __version__
splash.showMessage("Starting %s." % __version__)

# ---- Standard library imports

import csv
from time import ctime
from os import makedirs, path

from multiprocessing import freeze_support
import tkinter
import tkinter.filedialog
import tkinter.messagebox

# ---- Local imports

import gwhat.common.database as db
import gwhat.custom_widgets as MyQWidget
from gwhat.common.utils import save_content_to_csv
import gwhat.HydroPrint2 as HydroPrint
import gwhat.HydroCalc2 as HydroCalc
from gwhat.meteo import dwnld_weather_data
from gwhat.meteo.gapfill_weather_gui import GapFillWeatherGUI
from gwhat.meteo.dwnld_weather_data import DwnldWeatherWidget
from gwhat.widgets.tabwidget import TabWidget

from gwhat.projet.manager_projet import ProjetManager
from gwhat.projet.manager_data import DataManager
from gwhat.common import IconDB, StyleDB, QToolButtonBase
from gwhat import __version__

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

        splash.showMessage("Initializing project and data managers.")
        self.pmanager = ProjetManager(self)
        self.pmanager.currentProjetChanged.connect(self.new_project_loaded)
        self.dmanager = DataManager(pm=self.pmanager)

        # ----------------------------------------------------------- Init ----

        self.__initUI__()

        splash.showMessage("Loading last opened project.")
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

        splash.showMessage("Initializing download weather data.")
        self.tab_dwnld_data = DwnldWeatherWidget(self)
        self.tab_dwnld_data.set_workdir(self.projectdir)

        # ---- gapfill weather data ----

        splash.showMessage("Initializing gapfill weather data.")
        self.tab_fill_weather_data = GapFillWeatherGUI(self)
        self.tab_fill_weather_data.set_workdir(self.projectdir)

        # ---- hydrograph ----

        splash.showMessage("Initializing plot hydrograph.")
        self.tab_hydrograph = HydroPrint.HydroprintGUI(self.dmanager)
        splash.showMessage("Initializing analyse hydrograph.")
        self.tab_hydrocalc = HydroCalc.WLCalc(self.dmanager)

        # ---- TABS ASSEMBLY ----

        self.tab_widget = TabWidget()
        self.tab_widget.addTab(self.tab_dwnld_data, 'Download Weather')
        self.tab_widget.addTab(self.tab_fill_weather_data, 'Gap-Fill Weather')
        self.tab_widget.addTab(self.tab_hydrograph, 'Plot Hydrograph')
        self.tab_widget.addTab(self.tab_hydrocalc, 'Analyze Hydrograph')
        self.tab_widget.setCornerWidget(self.pmanager)

        self.tab_widget.currentChanged.connect(self.sync_datamanagers)

        # --------------------------------------------------- Main Console ----

        splash.showMessage("Initializing main window.")
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

        splitter.addWidget(self.tab_widget)
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
        super(WHAT, self).show()
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
        """
        Move the data manager from tab _Plot Hydrograph_ to tab
        _Analyze Hydrograph_ and vice-versa.
        """
        current = self.tab_widget.tabBar().currentIndex()
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
        self.tab_fill_weather_data.setEnabled(True)
        self.tab_hydrograph.setEnabled(True)
        self.tab_hydrocalc.setEnabled(True)

        # Update child widgets :

        # ---- dwnld_weather_data ----

        lat = self.pmanager.projet.lat
        lon = self.pmanager.projet.lon

        self.tab_dwnld_data.set_workdir(dirname)
        self.tab_dwnld_data.station_browser.lat_spinBox.setValue(lat)
        self.tab_dwnld_data.station_browser.lon_spinBox.setValue(lon)

        # ---- fill_weather_data ----

        self.tab_fill_weather_data.set_workdir(dirname)
        self.tab_fill_weather_data.load_data_dir_content()

    # =========================================================================

    def closeEvent(self, event):
        print('Closing projet')
        self.pmanager.close_projet()
        print('Closing GWHAT')
        event.accept()


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
            '..', 'Projects', 'Example', 'Example.gwt')
        self.language = 'English'
        self.fontsize_general = '14px'
        self.fontsize_console = '12px'
        self.fontsize_menubar = '12px'

        self.load_pref_file()

    def save_pref_file(self):
        print('\nSaving WHAT preferences to file...')
        fcontent = [['Project File:', os.path.relpath(self.projectfile)],
                    ['Language:', self.language],
                    ['Font-Size-General:', self.fontsize_general],
                    ['Font-Size-Console:', self.fontsize_console],
                    ['Font-Size-Menubar:', self.fontsize_menubar]]
        save_content_to_csv('WHAT.pref', fcontent)
        print('WHAT preferences saved.')

    def load_pref_file(self, circloop=False):

        # cicrcloop argument is a protection to prevent a circular loop
        # in case something goes wrong.

        try:
            with open('WHAT.pref', 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f, delimiter=','))

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


if __name__ == '__main__':                                   # pragma: no cover
    import logging

    logging.basicConfig(filename='WHAT.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s:%(message)s')
    try:
        main = WHAT()
        main.showMaximized()
        splash.finish(main)
        sys.exit(app.exec_())
    except Exception as e:
        logging.exception(str(e))
        raise e
