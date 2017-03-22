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

# Third party imports :

from PySide import QtGui, QtCore

# Local imports :

import database as db
import custom_widgets as MyQWidget
import what_project
import HydroPrint
import dwnld_weather_data
from gapfill_weather_gui import GapFillWeatherGUI
from about_WHAT import AboutWhat

import tkinter
import tkinter.filedialog
import tkinter.messagebox

freeze_support()

# DATABASES :

labelDB = []
iconDB = []
styleDB = []
ttipDB = []
headerDB = []

# The code is segmented in two main sections: the GUI section and the
# WORKER sections.
#
# The GUI is written with the toolbox Qt using the PySide binding.
#
# The WORKER section handles all the calculations and data manipulations of
# the program.

###############################################################################
#
#                            @SECTION GUI
#
###############################################################################

# The GUI is composed of a Tab area, a console terminal, and a
# progress bar. The Tab area is where the user interacts with the
# program. It is divided in four tabs:
#
#      (1) the "Download Data" tab,
#      (2) the "Fill Data" tab,
#      (3) The "Hydrograph" tab
#      (4) The "About" tab.
#
# The "Download Data" tab handles the downloading of raw data files
# from http://climate.weather.gc.ca/ and the formating and concatenation
# of these raw data files into a single file.
#
# The "Fill Data" tab handles the missing data completion process.
#
# The "Hydrograph" tab is where it is possible to plot the well hydrograph
# along with the meteorological data.
#
# The "About" tabs handles Copyright, Licensing and external links information
#
# The console terminal and the progress bar are shared by all the tabs of the
# Tab area and are only used to give information to the user about the
# state and activities of the main program.


class WHAT(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(WHAT, self).__init__(parent)

        self.__initUI__()

    def __initUI__(self):  # ==================================================
        """
        A generic widget is first set as the central widget of the
        MainWindow. Then, a QGridLayout is applied to this central
        widget. Two widgets are then added to the central widget's grid:
        (1) a Qsplitter widget on top and (2) a QProgressBar on the
        bottom.

        Two additional widgets are then added to the Qsplitter widget:
        (1) a QTabWidget and (2) a QTextEdit widget that is the console
        terminal that was discussed above.

        The QTabWidget is composed of four tabs. Each
        tab is defined within its own class that are child classes of the
        MainWindow class. The layout of each tab is handled with a
        QGridLayout.
        """

        # -------------------------------------------------- CLASS INSTANCES --

        self.projectInfo = MyProject(self)
        self.whatPref = WHATPref(self)
        # self.open_project_window = what_project.OpenProject()

        # ------------------------------------------------------ PREFERENCES --

        self.whatPref.load_pref_file()

        language = self.whatPref.language

        self.projectfile = self.whatPref.projectfile
        self.projectdir = path.dirname(self.projectfile)

        style = 'Regular'
        size = self.whatPref.fontsize_general

        family = db.styleUI().fontfamily

#        fontSS = ('font-style: %s;'
#                  'font-size: %s;'
#                  'font-family: %s;'
#                  ) % (style, size, family)
#
#        self.setStyleSheet("QWidget{%s}" % fontSS)

        # -------------------------------------------------------- DATABASES --

        # http://stackoverflow.com/questions/423379/
        # using-global-variables-in-a-function-other-
        # than-the-one-that-created-them

        global labelDB
        labelDB = db.labels(language)
        global iconDB
        iconDB = db.Icons()
        global styleDB
        styleDB = db.styleUI()
        global ttipDB
        ttipDB = db.Tooltips(language)
        global headerDB
        headerDB = db.FileHeaders()

        # ------------------------------------------------ MAIN WINDOW SETUP --

        self.setWindowTitle(db.software_version)
        self.setWindowIcon(QtGui.QIcon(os.path.join('Icons', 'WHAT.png')))

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

        # ------------------------------------------------- PROJECT MENU BAR --

        project_label = QtGui.QLabel('Project :')
        project_label.setAlignment(QtCore.Qt.AlignCenter)

        self.project_display = QtGui.QPushButton()
        self.project_display.setFocusPolicy(QtCore.Qt.NoFocus)
        self.project_display.setFont(styleDB.font_menubar)
        self.project_display.setMinimumWidth(100)

        self.btn_new_project = QtGui.QToolButton()
        self.btn_new_project.setAutoRaise(True)
        self.btn_new_project.setIcon(iconDB.new_project)
        self.btn_new_project.setToolTip(ttipDB.new_project)
        self.btn_new_project.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_new_project.setIconSize(styleDB.iconSize2)

        self.menubar_widget = QtGui.QWidget()
        subgrid_menubar = QtGui.QGridLayout()

        row, col = 0, 0
        subgrid_menubar.addWidget(project_label, row, col)
        col += 1
        subgrid_menubar.addWidget(self.project_display, row, col)
        col += 1
        subgrid_menubar.addWidget(self.btn_new_project, row, col)

        subgrid_menubar.setSpacing(3)
        subgrid_menubar.setContentsMargins(0, 0, 0, 5)  # (L,T,R,B)
        subgrid_menubar.setColumnStretch(1, 500)
        subgrid_menubar.setRowMinimumHeight(0, 28)

        self.menubar_widget.setLayout(subgrid_menubar)

        size = self.whatPref.fontsize_menubar
        fontSS = ('font-style: %s;'
                  'font-size: %s;'
                  'font-family: %s;'
                  ) % (style, size, family)
        self.menubar_widget.setStyleSheet("QWidget{%s}" % fontSS)

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

        # -- TABS ASSEMBLY --

        Tab_widget.addTab(self.tab_dwnld_data, labelDB.TAB1)
        Tab_widget.addTab(self.tab_fill_weather_data, labelDB.TAB2)
        Tab_widget.addTab(self.tab_hydrograph, labelDB.TAB3)
        Tab_widget.addTab(tab_about, labelDB.TAB4)

        Tab_widget.setCornerWidget(self.menubar_widget)

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
        mainGrid.addWidget(splitter, row, 0)
        row += 1
        mainGrid.addWidget(self.tab_fill_weather_data.pbar, row, 0)
        row += 1
        mainGrid.addWidget(self.tab_dwnld_data.pbar, row, 0)

        mainGrid.setSpacing(10)
        main_widget.setLayout(mainGrid)

        # ----------------------------------------------------------- EVENTS --

        self.btn_new_project.clicked.connect(self.show_new_project)
        self.project_display.clicked.connect(self.open_project)
#        self.open_project_window.OpenProjectSignal.connect(self.load_project)

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

        if self.check_project():
            self.load_project(self.projectfile)
        else:
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

    def show(self):  # ========================================================

        # Silently show so that the geometry of the Main window is defined :

        self.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)
        super(WHAT, self).show()
        self.hide()
        self.setAttribute(QtCore.Qt.WA_DontShowOnScreen, False)

        # Move main window to the center of the screen and show main window :

        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        super(WHAT, self).show()

    def write2console(self, console_text):  # =================================

        '''
        This function is the bottle neck through which all messages writen
        in the console must go through.
        '''

        textime = '<font color=black>[%s] </font>' % ctime()[4:-8]
        self.main_console.append(textime + console_text)

    # =========================================================================

    def show_new_project(self):
        new_project_window = what_project.NewProject(self)
        new_project_window.NewProjectSignal.connect(self.load_project)
        new_project_window.show()

    def open_project(self):
        # "open_project" is called by the event "self.project_display.clicked".
        # It allows the user to open an already existing project.

        directory = os.path.abspath(os.path.join('..', 'Projects'))
        filename, _ = QtGui.QFileDialog.getOpenFileName(
            self, 'Open Project', directory, '*.what')

        if filename:
            self.projectfile = filename
            self.load_project(filename)

    def load_project(self, filename):
        # This method is called either on startup during <initUI> or when
        # a new project is chosen with <open_project>.

        self.projectfile = filename
        print('\n-------------------------------')
        print('LOADING PROJECT...')
        print('-------------------------------\n')
        print('Loading "%s"' % os.path.relpath(self.projectfile))

        self.projectdir = os.path.dirname(self.projectfile)

        # ----Update WHAT.pref file ----

        self.whatPref.projectfile = self.projectfile
        self.whatPref.save_pref_file()

        # ---- Check Project ----

        self.check_project()

        # ---- Load Project Info ----

        self.projectInfo.load_project_info(self.projectfile)

        # ---- Update UI ----

        self.tab_dwnld_data.setEnabled(True)
        self.tab_fill_weather_data.setEnabled(True)
        self.tab_hydrograph.setEnabled(True)

        self.project_display.setText(self.projectInfo.name)
        self.project_display.adjustSize()

        # ------------------------------------------- Update child widgets ----

        # ---- dwnld_weather_data ----

        self.tab_dwnld_data.set_workdir(self.projectdir)
        self.tab_dwnld_data.search4stations.lat_spinBox.setValue(
            self.projectInfo.lat)

        self.tab_dwnld_data.search4stations.lon_spinBox.setValue(
            self.projectInfo.lon)

        # ---- fill_weather_data ----

        self.tab_fill_weather_data.set_workdir(self.projectdir)
        self.tab_fill_weather_data.load_data_dir_content()

        # ---- hydrograph ----

        self.tab_hydrograph.set_workdir(self.projectdir)

        print('')
        print('---- PROJECT LOADED ----')
        print('')

    def check_project(self):
        # Check if all files and folders associated with the .what file are
        # presents in the project folder. If some files or folders are missing,
        # the program will automatically generate new ones.

        # If the project.what file does not exist anymore, it returns a False
        # answer, which should tell the code on the UI side to deactivate
        # the UI.

        # This method should be run at the start of every method that needs to
        # interact with resource file of the current project.

        print('Checking project files and folders integrity for :')
        print(self.projectfile)

        if not path.exists(self.projectfile):
            print('Project file does not exist.')
            return False

        # ---- System project folder organization ----

        folders = [os.path.join(self.projectdir, 'Meteo', 'Raw'),
                   os.path.join(self.projectdir, 'Meteo', 'Input'),
                   os.path.join(self.projectdir, 'Meteo', 'Output'),
                   os.path.join(self.projectdir, 'Water Levels')]

        for f in folders:
            if not path.exists(f):
                makedirs(f)

        return True

    # =========================================================================

    def closeEvent(self, event):
        event.accept()


# =============================================================================


class WHATPref():
    """
    This class contains all the preferences relative to the WHAT interface,
    including:

    projectfile: It is a memory variable. It indicates upon launch to the
                 program what was the project that was opened when last time
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


class MyProject():
    """
    This class contains all the info and utilities to manage the current
    active project.
    """

    def __init__(self, parent=None):  # =======================================

        self.name = ''
        self.author = ''
        self.lat = 0
        self.lon = 0

    def load_project_info(self, projectfile):  # ==============================

        print('-------------------------------')
        print('Loading project info :')

        with open(projectfile, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f, delimiter='\t'))

        self.name = reader[0][1]
        self.author = reader[1][1]
        self.lat = float(reader[6][1])
        self.lon = float(reader[7][1])

        print('  - Project name : %s' % self.name)
        print('  - Author : %s' % self.author)
        print('  - Lat. : %0.2f' % self.lat)
        print('  - Lon. : %0.2f' % self.lon)
        print('Project info loaded.')
        print('-------------------------------')

# =============================================================================

if __name__ == '__main__':

#    app = QtGui.QApplication(sys.argv)
#    print('Starting WHAT...')
#    instance_1 = MainWindow()
#    sys.exit(app.exec_())

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
