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

from __future__ import division, unicode_literals

# Standard library imports :

import platform
import csv
import os
from time import ctime
from os import makedirs, path

from multiprocessing import freeze_support
import tkinter
import tkinter.filedialog
import tkinter.messagebox

# Third party imports :

from PySide import QtGui, QtCore

# Local imports :

import database as db
import custom_widgets as MyQWidget
import HydroPrint
import dwnld_weather_data
from gapfill_weather_gui import GapFillWeatherGUI
from about_WHAT import AboutWhat
from projet import ProjetManager
from icons import IconDB

freeze_support()

# DATABASES :

labelDB = []
styleDB = []
ttipDB = []
headerDB = []


class WHAT(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(WHAT, self).__init__(parent)

        self.whatPref = WHATPref(self)
        self.pmanager = ProjetManager(self)

        self.__initUI__()

    def __initUI__(self):

        # ------------------------------------------------------ PREFERENCES --

        self.whatPref.load_pref_file()

        language = self.whatPref.language

        self.projectfile = self.whatPref.projectfile
        self.projectdir = path.dirname(self.projectfile)

        style = 'Regular'
        size = self.whatPref.fontsize_general

        family = db.styleUI().fontfamily

        # -------------------------------------------------------- DATABASES --

        # http://stackoverflow.com/questions/423379/
        # using-global-variables-in-a-function-other-
        # than-the-one-that-created-them

        global labelDB
        labelDB = db.labels(language)
        global styleDB
        styleDB = db.styleUI()
        global ttipDB
        ttipDB = db.Tooltips(language)
        global headerDB
        headerDB = db.FileHeaders()

        # ------------------------------------------------ MAIN WINDOW SETUP --

        self.setWindowTitle(db.software_version)
        self.setWindowIcon(IconDB().master)

#        self.setMinimumWidth(1250)
#        self.setFont(styleDB.font1)

        if platform.system() == 'Windows':
            import ctypes
            myappid = 'what_application'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                myappid)

        # ----------------------------------------------------- MAIN CONSOLE --

        self.main_console = QtGui.QTextEdit()
        self.main_console.setReadOnly(True)
        self.main_console.setLineWrapMode(QtGui.QTextEdit.LineWrapMode.NoWrap)

        size = self.whatPref.fontsize_console
        fontSS = ('font-style: %s;'
                  'font-size: %s;'
                  'font-family: %s;'
                  ) % (style, size, family)
        self.main_console.setStyleSheet("QWidget{%s}" % fontSS)

        self.write2console('''<font color=black>Thanks for using %s.
            </font>''' % db.software_version)
        self.write2console('''<font color=black>
            Please report any bug or wishful feature to
            Jean-S&eacute;bastien Gosselin at jnsebgosselin@gmail.com.
            </font>''')

        # ------------------------------------------------------- TAB WIDGET --

        Tab_widget = QtGui.QTabWidget()

        # ---- Custom TabBar Height ----

        # http://stackoverflow.com/questions/12428917/
        # pyqt4-set-size-of-the-tab-bar-in-qtabwidget

        class TabBar(QtGui.QTabBar):
            def tabSizeHint(self, index):
                width = QtGui.QTabBar.tabSizeHint(self, index).width()
                return QtCore.QSize(width, 32)

        tab_bar = TabBar()
        Tab_widget.setTabBar(tab_bar)

        # ---- download weather data ----

        self.tab_dwnld_data = dwnld_weather_data.dwnldWeather(self)
        self.tab_dwnld_data.set_workdir(self.projectdir)

        # ---- gapfill weather data ----

        self.tab_fill_weather_data = GapFillWeatherGUI(self)
        self.tab_fill_weather_data.set_workdir(self.projectdir)

        # ---- hydrograph ----

        self.tab_hydrograph = HydroPrint.HydroprintGUI(self)
        self.tab_hydrograph.set_workdir(self.projectdir)

        # ---- about ----

        tab_about = AboutWhat(self)

        # ---- TABS ASSEMBLY ----

        Tab_widget.addTab(self.tab_dwnld_data, labelDB.TAB1)
        Tab_widget.addTab(self.tab_fill_weather_data, labelDB.TAB2)
        Tab_widget.addTab(self.tab_hydrograph, labelDB.TAB3)
        Tab_widget.addTab(tab_about, labelDB.TAB4)

        Tab_widget.setCornerWidget(self.pmanager)

        # -------------------------------------------------- SPLITTER WIDGET --

        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Vertical)

        splitter.addWidget(Tab_widget)
        splitter.addWidget(self.main_console)

        splitter.setCollapsible(0, True)
        splitter.setStretchFactor(0, 100)
        # Forces initially the main_console to its minimal height:
        splitter.setSizes([100, 1])

        # -------------------------------------------------------- MAIN GRID --

        main_widget = QtGui.QWidget()
        self.setCentralWidget(main_widget)

        mainGrid = QtGui.QGridLayout()

        row = 0
        mainGrid.addWidget(splitter, 0, 0)
        mainGrid.addWidget(self.tab_fill_weather_data.pbar, 1, 0)
        mainGrid.addWidget(self.tab_dwnld_data.pbar, 2, 0)

        mainGrid.setSpacing(10)
        main_widget.setLayout(mainGrid)

        # ----------------------------------------------------------- EVENTS --

        self.pmanager.currentProjetChanged.connect(self.new_project_loaded)

        # -- Console Signal Piping --

        issuer = self.tab_dwnld_data
        issuer.ConsoleSignal.connect(self.write2console)

        issuer = self.tab_fill_weather_data
        issuer.ConsoleSignal.connect(self.write2console)

        issuer = self.tab_hydrograph
        issuer.ConsoleSignal.connect(self.write2console)

        # ---------------------------------------------------- MESSAGE BOXES --

        self.msgError = MyQWidget.MyQErrorMessageBox()

        # ------------------------------------------------- CHECK IF PROJECT --

        success = self.pmanager.load_project(self.projectfile)
        if success is False:
            self.tab_dwnld_data.setEnabled(False)
            self.tab_fill_weather_data.setEnabled(False)
            self.tab_hydrograph.setEnabled(False)

            msgtxt = '''
                     <b>Unable to read the project file.<br><br>
                     "%s" does not exist.<br><br> Please open an existing
                     project or create a new one.<b>
                     ''' % self.projectfile

            self.msgError.setText(msgtxt)
            self.msgError.exec_()

    # =========================================================================

    def show(self):

        # Silently show :

        self.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)
        super(WHAT, self).show()

        # place main window when not maximize and hide window :

        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        super(WHAT, self).close()
        self.setAttribute(QtCore.Qt.WA_DontShowOnScreen, False)

        # Show :

        super(WHAT, self).show()

    # =========================================================================

    def write2console(self, text):
        # This function is the bottle neck through which all messages writen
        # in the console must go through.
        textime = '<font color=black>[%s] </font>' % ctime()[4:-8]
        self.main_console.append(textime + text)

    # =========================================================================

    def new_project_loaded(self):

        filename = self.pmanager.filename
        dirname = self.pmanager.dirname

        # ---- Update WHAT.pref file ----

        self.whatPref.projectfile = filename
        self.whatPref.save_pref_file()

        # ---- Update UI ----

        self.tab_dwnld_data.setEnabled(True)
        self.tab_fill_weather_data.setEnabled(True)
        self.tab_hydrograph.setEnabled(True)

        # ------------------------------------------- Update child widgets ----

        # ---- dwnld_weather_data ----

        lat = self.pmanager.currentProjet().lat
        lon = self.pmanager.currentProjet().lon

        self.tab_dwnld_data.set_workdir(dirname)
        self.tab_dwnld_data.search4stations.lat_spinBox.setValue(lat)
        self.tab_dwnld_data.search4stations.lon_spinBox.setValue(lon)

        # ---- fill_weather_data ----

        self.tab_fill_weather_data.set_workdir(dirname)
        self.tab_fill_weather_data.load_data_dir_content()

        # ---- hydrograph ----

        self.tab_hydrograph.set_workdir(dirname)

    # =========================================================================

    def closeEvent(self, event):
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


# =============================================================================
# =============================================================================


if __name__ == '__main__':

    import sys
    import logging

    logging.basicConfig(filename='WHAT.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s:%(message)s')
    try:
        app = QtGui.QApplication(sys.argv)
        print('Starting WHAT...')
        main = WHAT()
        main.show()

        ft = app.font()
        ft.setFamily('Segoe UI')
        ft.setPointSize(11)
        app.setFont(ft)

        sys.exit(app.exec_())
    except Exception as e:
        logging.exception(str(e))
        raise e
