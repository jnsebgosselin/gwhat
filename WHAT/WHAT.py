# -*- coding: utf-8 -*-
"""
Copyright 2014-2015 Jean-Sebastien Gosselin

email: jnsebgosselin@gmail.com

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it /will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# Source: http://www.gnu.org/licenses/gpl-howto.html

software_version = 'WHAT Beta 4.1.6'
last_modification = '24/06/2015'

# It is often said when developing interfaces that you need to fail fast,
# and iterate often. When creating a UI, you will make mistakes. Just keep
# moving forward, and remember to keep your UI out of the way.

# http://blog.teamtreehouse.com/10-user-interface-design-fundamentals

#---- STANDARD LIBRARY IMPORTS ----

import csv
from copy import copy
#from urllib import urlretrieve
from sys import argv
from time import ctime, strftime, sleep
from os import getcwd, listdir, makedirs, path
from string import maketrans
import platform

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui, QtCore
from PySide.QtCore import QDate

import numpy as np
from numpy.linalg import lstsq as linalg_lstsq
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple
import xlwt
import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
#import matplotlib.pyplot as plt
#from scipy import signal
#from statsmodels.regression.quantile_regression import QuantReg

#---- PERSONAL IMPORTS ----

import database as db
import what_project

import hydroprint
from hydroprint import LatLong2Dist
import imageviewer

import meteo
import waterlvl_calc

import dwnld_weather_data
from fill_weather_data import Weather_File_Info

#---- DATABASES ----

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


################################################################################
#                                                                           
#                            @SECTION GUI                               
#                                                                          
################################################################################


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

#===============================================================================
class MainWindow(QtGui.QMainWindow):
        
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
#===============================================================================
        
        self.initUI()
        
    #---------------------------------------------------------------------------
    def initUI(self):
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
    #---------------------------------------------------------------------------
        
        #-------------------------------------------------- CLASS INSTANCES ----
        
        self.projectInfo = MyProject(self)
        self.whatPref = WHATPref(self)
        self.new_project_window = what_project.NewProject(software_version)
#        self.open_project_window = what_project.OpenProject()
        
        #------------------------------------------------------ PREFERENCES ----
                
        self.whatPref.load_pref_file()
        
        language = self.whatPref.language
        
        self.projectfile = self.whatPref.projectfile
        self.projectdir = path.dirname(self.projectfile)
        
        #-------------------------------------------------------- DATABASES ----
        
        # http://stackoverflow.com/questions/423379/
        # using-global-variables-in-a-function-other-
        # than-the-one-that-created-them
        
        global labelDB
        labelDB = db.labels(language)
        global iconDB
        iconDB = db.icons()
        global styleDB
        styleDB = db.styleUI()
        global ttipDB
        ttipDB = db.tooltips(language)
        global headerDB
        headerDB = db.headers()
        
        #------------------------------------------------ MAIN WINDOW SETUP ----

        self.setMinimumWidth(1250)
        self.setWindowTitle(software_version)
        self.setWindowIcon(iconDB.WHAT)
        self.setFont(styleDB.font1)                
                        
        #----------------------------------------------------- MAIN CONSOLE ----
        
        self.main_console = QtGui.QTextEdit()        
        self.main_console.setReadOnly(True)
        self.main_console.setLineWrapMode(QtGui.QTextEdit.LineWrapMode.NoWrap)
        self.main_console.setFont(styleDB.font_console)
        
        self.write2console(
        '''<font color=black>Thanks for using %s.</font>''' % software_version)
        self.write2console(
        '''<font color=black>Please report any bug or wishful feature to 
             Jean-S&eacute;bastien Gosselin at jnsebgosselin@gmail.com.
           </font>''')
           
        #------------------------------------------------- PROJECT MENU BAR ----
                        
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
        
        row = 0
        col = 0
        subgrid_menubar.addWidget(project_label, row, col)
        col += 1
        subgrid_menubar.addWidget(self.project_display, row, col)
        col += 1
        subgrid_menubar.addWidget(self.btn_new_project, row, col)
        
        subgrid_menubar.setSpacing(3)
        subgrid_menubar.setContentsMargins(0, 0, 0, 5) #Left, Top, Right, Bottom 
        subgrid_menubar.setColumnStretch(1, 500)
        subgrid_menubar.setRowMinimumHeight(0, 28)
        
        self.menubar_widget.setLayout(subgrid_menubar)
        
        #------------------------------------------------------- TAB WIDGET ----
           
        Tab_widget = QtGui.QTabWidget()
        
        #---- Custom TabBar Height ----
        
        # http://stackoverflow.com/questions/12428917/
        # pyqt4-set-size-of-the-tab-bar-in-qtabwidget
        
        class TabBar(QtGui.QTabBar):

           def tabSizeHint(self, index):
               width = QtGui.QTabBar.tabSizeHint(self, index).width()
               return QtCore.QSize(width, 32)
        tab_bar = TabBar()       
        Tab_widget.setTabBar(tab_bar)
        
        #---- WIDGETS ----
                
        self.tab_dwnld_data = TabDwnldData(self)
        self.tab_fill = TabFill(self)        
        self.tab_hydrograph = TabHydrograph(self)
        tab_about = TabAbout(self)
        
        #---- LAYOUT ----
        
        Tab_widget.addTab(self.tab_dwnld_data, labelDB.TAB1)        
        Tab_widget.addTab(self.tab_fill, labelDB.TAB2) 
        Tab_widget.addTab(self.tab_hydrograph, labelDB.TAB3) 
        Tab_widget.addTab(tab_about, labelDB.TAB4)
        
        Tab_widget.setCornerWidget(self.menubar_widget)
        
        #-------------------------------------------------- SPLITTER WIDGET ----
                
        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Vertical)
        
        splitter.addWidget(Tab_widget)
        splitter.addWidget(self.main_console)
        
        splitter.setCollapsible(0, True)
        splitter.setStretchFactor(0, 100)                
        splitter.setSizes([100, 1]) # Forces initially the main_console to its
                                    # minimal height.       
        
        #----------------------------------------------------- Progress Bar ----

        self.pbar = QtGui.QProgressBar()
        self.pbar.setValue(0)
        
        #-------------------------------------------------------- MAIN GRID ----
        
        main_widget = QtGui.QWidget()
        self.setCentralWidget(main_widget)        
        
        mainGrid = QtGui.QGridLayout()
        mainGrid.setSpacing(10)
        
        row = 0
        mainGrid.addWidget(splitter, row, 0)
        row += 1
        mainGrid.addWidget(self.pbar, row, 0)
        row += 1
        mainGrid.addWidget(self.tab_dwnld_data.dwnld_weather.pbar, row, 0)
        
        main_widget.setLayout(mainGrid)
        self.pbar.hide()
        self.tab_dwnld_data.dwnld_weather.pbar.hide()
        
        #----------------------------------------------------------- EVENTS ----
        
        self.btn_new_project.clicked.connect(self.show_new_project)
        self.project_display.clicked.connect(self.open_project)
        self.new_project_window.NewProjectSignal.connect(self.load_project)
#        self.open_project_window.OpenProjectSignal.connect(self.load_project) 

        #---- Console Signal Piping ----
        
        issuer = self.tab_dwnld_data.dwnld_weather
        issuer.ConsoleSignal.connect(self.write2console)  

        issuer = self.tab_dwnld_data.dwnld_weather.search4stations
        issuer.ConsoleSignal.connect(self.write2console)

        issuer =  self.tab_dwnld_data.dwnld_weather.dwnl_raw_datafiles 
        issuer.ConsoleSignal.connect(self.write2console)                                                  
        
        #---------------------------------------------------- MESSAGE BOXES ----
        
        self.msgError = QtGui.QMessageBox()
        self.msgError.setIcon(QtGui.QMessageBox.Warning)
        self.msgError.setWindowTitle('Error Message')
                   
        #------------------------------------------------------------- SHOW ----
            
        self.show()
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        #------------------------------------------------- CHECK IF PROJECT ----
        
        isProjectExists = self.check_project()
        
        if isProjectExists:

            self.load_project(self.projectfile)
            
        else:
            
            self.tab_dwnld_data.setEnabled(False)    
            self.tab_fill.setEnabled(False)     
            self.tab_hydrograph.setEnabled(False)
            
            msgtxt = '''
                     <b>Unable to read the project file.<br><br>
                     "%s" does not exist.<br><br> Please open an existing
                     project or create a new one.<b>
                     ''' % self.projectfile
            
            self.msgError.setText(msgtxt)
            self.msgError.exec_()
                
    #---------------------------------------------------------------------------  
    def write2console(self, console_text):
        '''
        This function is the bottle neck through which all messages writen in
        the console window must go through.
        '''
    #---------------------------------------------------------------------------
        
        textime = '<font color=black>[' + ctime()[4:-8] + '] </font>'
                        
        self.main_console.append(textime + console_text)
    
    #---------------------------------------------------------------------------    
    def show_new_project(self):
    #---------------------------------------------------------------------------

        #---- Center Widget to Main Window ----
        
        # Adapted from:
        # http://zetcode.com/gui/pysidetutorial/firstprograms
                        
        self.new_project_window.clear_UI()
        
        qr = self.new_project_window.frameGeometry()
        cp = self.frameGeometry().center()
        qr.moveCenter(cp)
        self.new_project_window.move(qr.topLeft())
        
        self.new_project_window.setModal(True)
        self.new_project_window.show()
        self.new_project_window.setFixedSize(self.new_project_window.size())
            
    #---------------------------------------------------------------------------
    def open_project(self):
        '''
        "open_project" is called by the event "self.project_display.clicked".
        It allows the user to open an already existing project.
        '''
    #---------------------------------------------------------------------------
        
#        qr = self.open_project_window.frameGeometry()
#        cp = self.frameGeometry().center()
#        qr.moveCenter(cp)
#        self.open_project_window.move(qr.topLeft())
#        
#        self.open_project_window.setModal(True)
#        self.open_project_window.show()
#        self.open_project_window.setFixedSize(self.open_project_window.size())
        
        #------------------------------------------- Custom File Dialog (1) ----
        
#        self.dialog = QtGui.QFileDialog()
#        print(self.dialog.sidebarUrls())
#        self.dialog.show()
        
#        self.dialog.setDirectory(directory)
#        self.dialog.setNameFilters(['*.what'])
#        self.dialog.setLabelText(QtGui.QFileDialog.FileName,'Open Project')
#        self.dialog.setOptions(QtGui.QFileDialog.ReadOnly)
#        self.dialog.setWindowTitle('Open Project')
#        self.dialog.setWindowIcon(iconDB.WHAT)
#        self.dialog.setFont(styleDB.font1)
#        self.dialog.setViewMode(QtGui.QFileDialog.List)
#        
#        self.dialog.fileSelected.connect(self.new_project_created)
#        
#        self.dialog.exec_()
       
        #----------------------------------------------------- Stock Dialog ----
       
        directory = path.abspath('../Projects')

        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                      self, 'Open Project', directory, '*.what')
                                   
        if filename:

            self.projectfile = filename                        
            self.load_project(filename)
            
    #---------------------------------------------------------------------------
    def load_project(self, filename):
        '''
        This method is called either on startup during <initUI> or when a new
        project is chosen with <open_project>.        
        '''
    #---------------------------------------------------------------------------
        
        self.projectfile = filename 
        
        print('')
        print('---- LOADING PROJECT... ----')
        print('')
        print('Loading "%s"' % path.relpath(self.projectfile))
        
        self.projectdir = path.dirname(self.projectfile)
        
        #----Update WHAT.pref file ----
            
        self.whatPref.projectfile = self.projectfile
        self.whatPref.save_pref_file()
        
        #---- Check Project ----
        
        self.check_project()
        
        #---- Load Project Info ----
        
        self.projectInfo.load_project_info(self.projectfile)
        
        #---- Update UI ----
        
        self.tab_dwnld_data.setEnabled(True)    
        self.tab_fill.setEnabled(True)     
        self.tab_hydrograph.setEnabled(True)
        
        self.project_display.setText(self.projectInfo.name)
        self.project_display.adjustSize()
                                                           
        self.tab_dwnld_data.dwnld_weather.search4stations.lat_spinBox.setValue(
                                                           self.projectInfo.lat)
                                                           
        self.tab_dwnld_data.dwnld_weather.search4stations.lon_spinBox.setValue(
                                                           self.projectInfo.lon)
        
        #---- Load Weather Station List ----

#        self.tab_dwnld_data.load_stationList()
        self.tab_dwnld_data.dwnld_weather.load_stationList()
            
        #---- Load Weather Input Files ----
        
        self.tab_fill.load_data_dir_content()
        
        # ----- RESET UI Memory Variables -----
        
        self.tab_hydrograph.meteo_dir = self.projectdir + '/Meteo/Output'
        self.tab_hydrograph.waterlvl_dir = self.projectdir + '/Water Levels'
        self.tab_hydrograph.save_fig_dir = self.projectdir
        
        #---- Update child widgets ----
        
        self.tab_dwnld_data.dwnld_weather.set_workdir(self.projectdir)
        self.tab_hydrograph.weather_avg_graph.save_fig_dir = self.projectdir
        
        print('')
        print('---- PROJECT LOADED ----')
        print('')
      
    #---------------------------------------------------------------------------
    def check_project(self):
        """
        Check if all files and folders associated with the .what file are
        presents in the project folder. If some files or folders are missing,
        the program will automatically generate new ones.
        
        If the project.what file does not exist anymore, it returns a False
        answer, which should tell the code on the UI side to deactivate the  UI.
        
        This method should be run at the start of every method that needs to
        interact with resource file of the current project.
        """
    #---------------------------------------------------------------------------
        
        print 'Checking project files and folders integrity'
        
        print self.projectfile
        if not path.exists(self.projectfile):
            print 'Project file does not exist.'
            return False
            
        #---- System project folder organization ----
       
        if not path.exists(self.projectdir + '/Meteo/Raw'):
            makedirs(self.projectdir + '/Meteo/Raw')
        if not path.exists(self.projectdir + '/Meteo/Input'):
            makedirs(self.projectdir + '/Meteo/Input')
        if not path.exists(self.projectdir + '/Meteo/Output'):
            makedirs(self.projectdir + '/Meteo/Output')
        if not path.exists(self.projectdir + '/Water Levels'):
            makedirs(self.projectdir + '/Water Levels')
            
        #---- waterlvl_manual_measurements.xls ----
        
        fname = self.projectdir + '/waterlvl_manual_measurements.xls'
        if not path.exists(fname):
            
            msg = ('No "waterlvl_manual_measurements.xls" file found. ' +
                   'A new one has been created.')
            print msg
            
            # http://stackoverflow.com/questions/13437727
            book = xlwt.Workbook(encoding="utf-8")
            sheet1 = book.add_sheet("Sheet 1")
            sheet1.write(0, 0, 'Well_ID')
            sheet1.write(0, 1, 'Time (days)')
            sheet1.write(0, 2, 'Obs. (mbgs)')
            book.save(fname)
            
        #---- weather_stations.lst ----
                
        fname = self.projectdir + '/weather_stations.lst'
        if not path.exists(fname):
            
            msg = ('No "weather_stations.lst" file found. ' +
                   'A new one has been created.')
            print msg
            
            fcontent = headerDB.weather_stations
            
            with open(fname, 'wb') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(fcontent)
        
        #---- graph_layout.lst ----
        
        filename = self.projectdir + '/graph_layout.lst'
        if not path.exists(filename):
            
            fcontent = headerDB.graph_layout
                        
            msg = ('No "graph_layout.lst" file found. ' +
                   'A new one has been created.')
            print msg

            with open(filename, 'wb') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(fcontent)
                
        return True
                    
################################################################################
        
class TabHydrograph(QtGui.QWidget):                          # @TAB HYDROGRAPH #
    
################################################################################
    
    def __init__(self, parent):
        super(TabHydrograph, self).__init__(parent)
        self.parent = parent        
        self.initUI()
    
    #===========================================================================    
    def initUI(self):
    # Layout is organized with an ensemble of grids that are assembled
    # together on 3 different levels. First level is the main grid.
    # Second level is where are the LEFT, RIGHT and TOOLBAR grids. 
    # Finally, third level is where are the SubGrids. 
    #
    #                                   MAIN GRID                                                 
    #                 --------------------------------------------                       
    #                 |               |                |         |
    #                 |   LEFT GRID   |   RIGHT GRID   | TOOLBAR |
    #                 |               |                |         |
    #                 --------------------------------------------
    #
    #===========================================================================
        
        # ----- Variables Init -----
        
        self.UpdateUI = True
        self.fwaterlvl = []
        self.waterlvl_data = hydroprint.WaterlvlData()
        self.meteo_data = meteo.MeteoObj()
        
        #----------------------------------------------- WEATHER AVG WINDOW ----
        
        self.weather_avg_graph = meteo.WeatherAvgGraph()
        projectdir = self.parent.projectdir
        self.weather_avg_graph.save_fig_dir = projectdir
        
        #---------------------------------------------------- waterlvl_calc ----
        
        self.waterlvl_calc = waterlvl_calc.WLCalc()
        self.waterlvl_calc.hide()
        
        #--------------------------------------------------- LAYOUT TOOLBAR ----

        graph_title_label = QtGui.QLabel('         ')
        self.graph_title = QtGui.QLineEdit()
        self.graph_title.setMaxLength(65)
        self.graph_title.setEnabled(False)
        self.graph_title.setText('Add A Title To The Figure Here')
        self.graph_title.setToolTip(ttipDB.addTitle)
        self.graph_status = QtGui.QCheckBox() 
                
        btn_loadConfig = QtGui.QToolButton()
        btn_loadConfig.setAutoRaise(True)
        btn_loadConfig.setIcon(iconDB.load_graph_config)
        btn_loadConfig.setToolTip(ttipDB.loadConfig)
                                  
        btn_saveConfig = QtGui.QToolButton()
        btn_saveConfig.setAutoRaise(True)
        btn_saveConfig.setIcon(iconDB.save_graph_config)
        btn_saveConfig.setToolTip(ttipDB.saveConfig)
        
        btn_bestfit_waterlvl = QtGui.QToolButton()
        btn_bestfit_waterlvl.setAutoRaise(True)
        btn_bestfit_waterlvl.setIcon(iconDB.fit_y)        
        btn_bestfit_waterlvl.setToolTip(ttipDB.fit_y)
        
        btn_bestfit_time = QtGui.QToolButton()
        btn_bestfit_time.setAutoRaise(True)
        btn_bestfit_time.setIcon(iconDB.fit_x)
        btn_bestfit_time.setToolTip(ttipDB.fit_x)
        
        btn_closest_meteo = QtGui.QToolButton()
        btn_closest_meteo.setAutoRaise(True)
        btn_closest_meteo.setIcon(iconDB.closest_meteo)
        btn_closest_meteo.setToolTip(ttipDB.closest_meteo)  
        
        btn_draw = QtGui.QToolButton()
        btn_draw.setAutoRaise(True)
        btn_draw.setIcon(iconDB.refresh2)        
        btn_draw.setToolTip(ttipDB.draw_hydrograph)
        
        btn_weather_normals = QtGui.QToolButton()
        btn_weather_normals.setAutoRaise(True)
        btn_weather_normals.setIcon(iconDB.meteo)        
        btn_weather_normals.setToolTip(ttipDB.weather_normals)
        
        self.btn_work_waterlvl = QtGui.QToolButton()
        self.btn_work_waterlvl.setAutoRaise(True)
        self.btn_work_waterlvl.setIcon(iconDB.toggleMode)        
        self.btn_work_waterlvl.setToolTip(ttipDB.work_waterlvl)

        btn_save = QtGui.QToolButton()
        btn_save.setAutoRaise(True)
        btn_save.setIcon(iconDB.save)
        btn_save.setToolTip(ttipDB.save_hydrograph)

        separator1 = QtGui.QFrame()
        separator1.setFrameStyle(styleDB.VLine)
        separator2 = QtGui.QFrame()
        separator2.setFrameStyle(styleDB.VLine)
        separator3 = QtGui.QFrame()
        separator3.setFrameStyle(styleDB.VLine)                    
                                     
        subgrid_toolbar = QtGui.QGridLayout()
        toolbar_widget = QtGui.QWidget()
        
        row = 0
        col = 0
        subgrid_toolbar.addWidget(self.btn_work_waterlvl, row, col)
        col += 1
        subgrid_toolbar.addWidget(separator3, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_save, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_draw, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_loadConfig, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_saveConfig, row, col)
        col += 1
        subgrid_toolbar.addWidget(separator1, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_bestfit_waterlvl, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_bestfit_time, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_closest_meteo, row, col)
        col += 1
        subgrid_toolbar.addWidget(separator2, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_weather_normals, row, col)
        col += 1
        subgrid_toolbar.addWidget(graph_title_label, row, col)
        subgrid_toolbar.setColumnStretch(col, 1)
        col += 1
        subgrid_toolbar.addWidget(self.graph_title, row, col)
        subgrid_toolbar.setColumnStretch(col, 4)
        col += 1
        subgrid_toolbar.addWidget(self.graph_status, row, col)
               
        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)
        
        btn_loadConfig.setIconSize(styleDB.iconSize)
        btn_saveConfig.setIconSize(styleDB.iconSize)
        btn_bestfit_waterlvl.setIconSize(styleDB.iconSize)
        btn_bestfit_time.setIconSize(styleDB.iconSize)
        btn_closest_meteo.setIconSize(styleDB.iconSize)
        btn_weather_normals.setIconSize(styleDB.iconSize)
        btn_draw.setIconSize(styleDB.iconSize)
        btn_save.setIconSize(styleDB.iconSize)
        self.btn_work_waterlvl.setIconSize(styleDB.iconSize)
        
        toolbar_widget.setLayout(subgrid_toolbar)
     
        #------------------------------------------------ Widget Data Files ----
       
        btn_waterlvl_dir = QtGui.QPushButton(' Water Level Data File')
        btn_waterlvl_dir.setIcon(iconDB.openFile)
        btn_waterlvl_dir.setIconSize(styleDB.iconSize2)
        self.well_info_widget = QtGui.QTextEdit()
        self.well_info_widget.setReadOnly(True)
        self.well_info_widget.setFixedHeight(150)
        
        btn_weather_dir = QtGui.QPushButton(' Weather Data File')
        btn_weather_dir.setIcon(iconDB.openFile)
        btn_weather_dir.setIconSize(styleDB.iconSize2)
        self.meteo_info_widget = QtGui.QTextEdit()
        self.meteo_info_widget.setReadOnly(True)
        self.meteo_info_widget.setFixedHeight(150)
        
        subgrid = QtGui.QGridLayout()
        subgrid_widget = QtGui.QWidget()
                
        subgrid.addWidget(btn_waterlvl_dir, 0, 0)
        subgrid.addWidget(self.well_info_widget, 1, 0)
        subgrid.addWidget(btn_weather_dir, 2, 0)        
        subgrid.addWidget(self.meteo_info_widget, 3, 0)
                
        subgrid.setSpacing(5)
        subgrid.setColumnMinimumWidth(0, 250)
        subgrid.setContentsMargins(0, 0, 0, 0)
        
        subgrid_widget.setLayout(subgrid)
                
        #------------------------------------------------ Widget Time Scale ----
        
        label_date_start = QtGui.QLabel('Date Min :')        
        self.date_start_widget = QtGui.QDateEdit()
        self.date_start_widget.setDisplayFormat('01 / MM / yyyy')
        self.date_start_widget.setAlignment(QtCore.Qt.AlignCenter)
        
        label_date_end = QtGui.QLabel('Date Max :')
        self.date_end_widget = QtGui.QDateEdit()
        self.date_end_widget.setDisplayFormat('01 / MM / yyyy')
        self.date_end_widget.setAlignment(QtCore.Qt.AlignCenter)
        
        widget_time_scale = QtGui.QFrame()
        widget_time_scale.setFrameStyle(0)  # styleDB.frame 
        grid_time_scale = QtGui.QGridLayout()
        
        row = 0
        grid_time_scale.addWidget(label_date_start, row, 1)
        grid_time_scale.addWidget(self.date_start_widget, row, 2)
        row +=1
        grid_time_scale.addWidget(label_date_end, row, 1)  
        grid_time_scale.addWidget(self.date_end_widget, row, 2)
        
        grid_time_scale.setVerticalSpacing(5)
        grid_time_scale.setHorizontalSpacing(10)
        grid_time_scale.setContentsMargins(10, 10, 10, 10)
        grid_time_scale.setColumnStretch(2, 100)
#        subgrid_dates.setColumnStretch(0, 100)
        
        widget_time_scale.setLayout(grid_time_scale)
        
        #----------------------------------------- Widget Water Level Scale ----
        
        label_waterlvl_scale = QtGui.QLabel('WL Scale :') 
        self.waterlvl_scale = QtGui.QDoubleSpinBox()
        self.waterlvl_scale.setSingleStep(0.05)
        self.waterlvl_scale.setMinimum(0.05)
        self.waterlvl_scale.setSuffix('  m')
        self.waterlvl_scale.setAlignment(QtCore.Qt.AlignCenter)        
        
        label_waterlvl_max = QtGui.QLabel('WL Min :') 
        self.waterlvl_max = QtGui.QDoubleSpinBox()
        self.waterlvl_max.setSingleStep(0.1)
        self.waterlvl_max.setSuffix('  m')
        self.waterlvl_max.setAlignment(QtCore.Qt.AlignCenter)
        self.waterlvl_max.setMinimum(-1000)
        self.waterlvl_max.setMaximum(1000)
        
        label_datum = QtGui.QLabel('WL Datum :')
        self.datum_widget = QtGui.QComboBox()
        self.datum_widget.addItems(['Ground Surface', 'See Level'])
        
        self.subgrid_WLScale_widget = QtGui.QFrame()
        self.subgrid_WLScale_widget.setFrameStyle(0) # styleDB.frame
        subgrid_WLScale = QtGui.QGridLayout()
        
        row = 0
        subgrid_WLScale.addWidget(label_waterlvl_scale, row, 1)        
        subgrid_WLScale.addWidget(self.waterlvl_scale, row, 2)
        row += 1
        subgrid_WLScale.addWidget(label_waterlvl_max, row, 1)        
        subgrid_WLScale.addWidget(self.waterlvl_max, row, 2)
        row += 1
        subgrid_WLScale.addWidget(label_datum, row, 1)
        subgrid_WLScale.addWidget(self.datum_widget, row, 2)
        
        subgrid_WLScale.setVerticalSpacing(5)
        subgrid_WLScale.setHorizontalSpacing(10)
        subgrid_WLScale.setContentsMargins(10, 10, 10, 10) # (L, T, R, B)
        subgrid_WLScale.setColumnStretch(2, 100)
#        subgrid_WLScale.setColumnStretch(0, 100)
        
        self.subgrid_WLScale_widget.setLayout(subgrid_WLScale)
        
        #--------------------------------------------- Widget Weather Scale ----
        
        label_Ptot_scale = QtGui.QLabel('Precip. Scale :') 
        self.Ptot_scale = QtGui.QSpinBox()
        self.Ptot_scale.setSingleStep(5)
        self.Ptot_scale.setMinimum(5)
        self.Ptot_scale.setMaximum(50)
        self.Ptot_scale.setValue(20)        
        self.Ptot_scale.setSuffix('  mm')
        self.Ptot_scale.setAlignment(QtCore.Qt.AlignCenter)
#        self.Ptot_scale.setMinimumWidth(150)
        
        widget_weather_scale = QtGui.QFrame()
        widget_weather_scale.setFrameStyle(0)
        grid_weather_scale = QtGui.QGridLayout()
        
        row = 1
        grid_weather_scale.addWidget(label_Ptot_scale, row, 1)        
        grid_weather_scale.addWidget(self.Ptot_scale, row, 2)
                
        grid_weather_scale.setVerticalSpacing(5)
        grid_weather_scale.setHorizontalSpacing(10)
        grid_weather_scale.setContentsMargins(10, 10, 10, 10) # (L, T, R, B)
        grid_weather_scale.setColumnStretch(2, 100)
#        grid_Ptot_scale.setColumnStretch(0, 100)
        grid_weather_scale.setRowStretch(row+1, 100)
        grid_weather_scale.setRowStretch(0, 100)
        
        widget_weather_scale.setLayout(grid_weather_scale)
                
        #------------------------------------------------ Scales Tab Widget ----
        
        self.tabscales = QtGui.QTabWidget()
        self.tabscales.addTab(widget_time_scale, 'Time')
        self.tabscales.addTab(self.subgrid_WLScale_widget, 'Water Level')
        self.tabscales.addTab(widget_weather_scale, 'Weather')
        
        #---- SubGrid Labels Language ----
        
        language_label = QtGui.QLabel('Label Language:')
        self.language_box = QtGui.QComboBox()
        self.language_box.setEditable(False)
        self.language_box.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.language_box.addItems(['French', 'English'])
        self.language_box.setCurrentIndex(1)
        
        self.subgrid_labLang_widget = QtGui.QFrame()
        subgrid_labLang = QtGui.QGridLayout()
        
        row = 0
        subgrid_labLang.addWidget(language_label, row, 0)        
        subgrid_labLang.addWidget(self.language_box, row, 1)
        
        subgrid_labLang.setSpacing(5)
        subgrid_labLang.setContentsMargins(5, 5, 5, 5) # (L, T, R, B)
        
        self.subgrid_labLang_widget.setLayout(subgrid_labLang)
                                
        #------------------------------------------------------ RIGHT PANEL ----
        
        grid_RIGHT = QtGui.QGridLayout()
        grid_RIGHT_widget = QtGui.QFrame()
        
        row = 0
        col = 0
        grid_RIGHT.addWidget(subgrid_widget, row, col)
        row += 1
        grid_RIGHT.addWidget(self.waterlvl_calc.widget_MRCparam, row, col)
        self.waterlvl_calc.widget_MRCparam.hide()
        grid_RIGHT.addWidget(self.tabscales, row, col)
#        grid_RIGHT.addWidget(self.subgrid_dates_widget, row, col)        
#        row += 1
#        grid_RIGHT.addWidget(self.subgrid_WLScale_widget, row, col)        
        row += 1
        grid_RIGHT.addWidget(self.subgrid_labLang_widget, row, col)
        
        grid_RIGHT_widget.setLayout(grid_RIGHT)
        grid_RIGHT.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)
        grid_RIGHT.setSpacing(15)
        grid_RIGHT.setRowStretch(row+1, 500)
        
        #------------------------------------------------ LAYOUT LEFT PANEL ----
        
        #---- SubGrid Hydrograph Frame ----
        
        self.hydrograph2display = hydroprint.Hydrograph()
        self.hydrograph_canvas = FigureCanvasQTAgg(self.hydrograph2display.fig)
        self.hydrograph_canvas.draw()        
        
        self.hydrograph_scrollarea = imageviewer.ImageViewer()
        
        grid_hydrograph_widget = QtGui.QFrame()
        grid_hydrograph =  QtGui.QGridLayout() 
        
        grid_hydrograph.addWidget(self.hydrograph_scrollarea, 0, 0)
        
        grid_hydrograph.setRowStretch(0, 500)
        grid_hydrograph.setColumnStretch(0, 500)
        grid_hydrograph.setContentsMargins(0, 0, 0, 0) # (L, T, R, B) 
        
        grid_hydrograph_widget.setLayout(grid_hydrograph)
        
        #----- ASSEMBLING SubGrids -----
                
        grid_layout = QtGui.QGridLayout()
        self.grid_layout_widget = QtGui.QFrame()
        
        row = 0
        grid_layout.addWidget(toolbar_widget, row, 0)
        row += 1
        grid_layout.addWidget(grid_hydrograph_widget, row, 0)
        
        self.grid_layout_widget.setLayout(grid_layout)
        grid_layout.setContentsMargins(0, 0, 0, 0) # Left, Top, Right, Bottom 
        grid_layout.setSpacing(5)
        grid_layout.setColumnStretch(0, 500)
#        grid_LEFT.setColumnStretch(2, 500)
        grid_layout.setRowStretch(1, 500)
#        grid_LEFT.setRowStretch(row+1, 500)
        
        #-------------------------------------------------------- MAIN GRID ----
                
        mainGrid_VLine1 = QtGui.QFrame()
        mainGrid_VLine1.setFrameStyle(styleDB.VLine)
        
        mainGrid = QtGui.QGridLayout()
        
        row = 0
        col = 0
        mainGrid.addWidget(self.grid_layout_widget, row, col)
        mainGrid.addWidget(self.waterlvl_calc, row, col)
        col += 1
        mainGrid.addWidget(mainGrid_VLine1, row, col)
        col += 1
        mainGrid.addWidget(grid_RIGHT_widget, row, col)
        
        mainGrid.setContentsMargins(10, 10, 10, 10) # Left, Top, Right, Bottom 
        mainGrid.setSpacing(15)
        mainGrid.setColumnStretch(0, 500)
        
        self.setLayout(mainGrid)
                
        #---------------------------------------------------- MESSAGE BOXES ----
                                          
        self.msgBox = QtGui.QMessageBox()
        self.msgBox.setIcon(QtGui.QMessageBox.Question)
        self.msgBox.setStandardButtons(QtGui.QMessageBox.Yes |
                                       QtGui.QMessageBox.No)
        self.msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
        self.msgBox.setWindowTitle('Save Graph Layout')
        
        self.msgError = QtGui.QMessageBox()
        self.msgError.setIcon(QtGui.QMessageBox.Warning)
        self.msgError.setWindowTitle('Error Message')
        
        #----------------------------------------------------------- EVENTS ----
        
        #----- Toolbox Layout -----
        
        btn_loadConfig.clicked.connect(self.load_graph_layout)
        btn_saveConfig.clicked.connect(self.save_config_isClicked)
        btn_bestfit_waterlvl.clicked.connect(self.best_fit_waterlvl)
        btn_bestfit_time.clicked.connect(self.best_fit_time)
        btn_closest_meteo.clicked.connect(self.select_closest_meteo_file)
        btn_draw.clicked.connect(self.draw_hydrograph)
        btn_save.clicked.connect(self.select_save_path)
        btn_weather_normals.clicked.connect(self.show_weather_averages)
        
        self.btn_work_waterlvl.clicked.connect(self.toggle_computeMode)
        
        #----- Toolbox Computation -----
        
        self.waterlvl_calc.btn_layout_mode.clicked.connect(
                                                         self.toggle_layoutMode)
        
        #----- Others -----
        
        btn_waterlvl_dir.clicked.connect(self.select_waterlvl_file)
        btn_weather_dir.clicked.connect(self.select_meteo_file)
        
        #----- Hydrograph Parameters -----
        
        self.datum_widget.currentIndexChanged.connect(self.datum_changed)
        self.language_box.currentIndexChanged.connect(self.language_changed)
        self.waterlvl_max.valueChanged.connect(self.waterlvl_scale_changed)
        self.waterlvl_scale.valueChanged.connect(self.waterlvl_scale_changed)
        self.graph_status.stateChanged.connect(self.fig_title_state_changed)
        self.graph_title.editingFinished.connect(self.fig_title_changed)
        self.Ptot_scale.valueChanged.connect(self.Ptot_scale_changed)
        
        self.date_start_widget.dateChanged.connect(self.time_scale_changed)
        self.date_end_widget.dateChanged.connect(self.time_scale_changed)
        
        #------------------------------------------------------- Init Image ----
        
        #---- Generate blank image ----
        
        size = self.hydrograph_canvas.size()
        height = size.height()
        width = size.width()
        imgbuffer = self.hydrograph_canvas.buffer_rgba()
        blank_image = QtGui.QImage(imgbuffer, width, height,
                                   QtGui.QImage.Format_RGB32)                         
        blank_image = QtGui.QImage.rgbSwapped(blank_image)
        
        #---- Display blank image ----
                
        self.hydrograph_scrollarea.load_image(blank_image)
        
    def toggle_layoutMode(self):
        
        self.waterlvl_calc.hide()        
        self.grid_layout_widget.show()
        
        #---- Right Panel Update ----
        
        self.waterlvl_calc.widget_MRCparam.hide()
        self.tabscales.show()
#        self.subgrid_dates_widget.show() 
#        self.subgrid_WLScale_widget.show()
        self.subgrid_labLang_widget.show()
        
    def toggle_computeMode(self):
        
        self.grid_layout_widget.hide()
        self.waterlvl_calc.show()
        
        #---- Right Panel Update ----
        
        self.waterlvl_calc.widget_MRCparam.show()
        self.tabscales.hide()
#        self.subgrid_dates_widget.hide()
#        self.subgrid_WLScale_widget.hide()
        self.subgrid_labLang_widget.hide()
        
    def show_weather_averages(self):
        
        filemeteo = self.hydrograph2display.fmeteo
        if not filemeteo:
            
            self.parent.write2console(
            '''<font color=red>No valid Weather Data File currently 
                 selected.</font>''')
                               
            self.emit_error_message(
            '''<b>Please select a valid Weather Data File first.</b>''')
            
            return
        
        self.weather_avg_graph.generate_graph(filemeteo)
        
        self.weather_avg_graph.show()
        self.weather_avg_graph.setFixedSize(self.weather_avg_graph.size())           
            
    def emit_error_message(self, error_text):
        
        self.msgError.setText(error_text)
        self.msgError.exec_()
    
    #===========================================================================
    def select_waterlvl_file(self):
        '''
        This method is called by <btn_waterlvl_dir.clicked.connect>. It prompts
        the user to select a valid Water Level Data file.        
        '''
    #===========================================================================
        
        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                   self, 'Select a valid water level data file', 
                                   self.waterlvl_dir, '*.xls')
        
        self.load_waterlvl(filename)
        
    #===========================================================================                          
    def load_waterlvl(self, filename):
        '''
        If "filename" exists:
        
        The (1) water level time series, (2) observation well info and the
        (3) manual measures are loaded and saved in the class instance 
        "waterlvl_data".
        
        Then the code check if there is a layout already saved for this well and
        if yes, will prompt the user if he wants to load it.
        
        Depending if there is a lyout or not, a Weather Data File will be 
        loaded and the hydrograph will be automatically plotted.
        '''
    #===========================================================================   
        
        if not filename:
            print 'Path is empty. Cannot load water level file.'
            return
            
        self.parent.check_project()
            
        self.UpdateUI = False
            
        #----- Update UI Memory Variables -----
        
        self.waterlvl_dir = path.dirname(filename)
        self.fwaterlvl = filename
        
        #----- Load Data -----
        
        self.waterlvl_data.load(filename)                        
        name_well = self.waterlvl_data.name_well
                
        #----- Load Manual Measures -----
        
        filename = self.parent.projectdir + '/waterlvl_manual_measurements.xls'        
        self.waterlvl_data.load_waterlvl_measures(filename, name_well)
        
        #----- Update Waterlvl Obj -----
        
        self.hydrograph2display.set_waterLvlObj(self.waterlvl_data)
        
        #----- Display Well Info in UI -----
        
        self.well_info_widget.setText(self.waterlvl_data.well_info)
        
        self.parent.write2console(
        '''<font color=black>Water level data set loaded successfully for
             well %s.</font>''' % name_well)
             
        #---- Update "Compute" Mode Graph ----
        
        self.draw_computeMode_waterlvl()
        
        #---- Well Layout -----

        filename = self.parent.projectdir + '/graph_layout.lst'
        isLayoutExist = self.hydrograph2display.checkLayout(name_well, filename)
                        
        if isLayoutExist == True:
            
            self.parent.write2console(
            '''<font color=black>A graph layout exists for well %s.
               </font>''' % name_well)
            
            self.msgBox.setText('<b>A graph layout already exists ' +
                                    'for well ' + name_well + '.<br><br> Do ' +
                                    'you want to load it?</b>')
            override = self.msgBox.exec_()

            if override == self.msgBox.Yes:
                self.load_graph_layout()
                return
        
        self.best_fit_waterlvl()
        self.best_fit_time()
        self.select_closest_meteo_file()
            
        #------------------------------------------------------- Enable UI -----
        
        self.UpdateUI = True
            
    def select_closest_meteo_file(self):
                
        meteo_folder = self.parent.projectdir + '/Meteo/Output'
        
        if path.exists(meteo_folder) and self.fwaterlvl:
            
            LAT1 = self.waterlvl_data.LAT
            LON1 = self.waterlvl_data.LON
            
            # Generate a list of data file paths.            
            fmeteo_paths = []
            for files in listdir(meteo_folder):
                if files.endswith(".out"):
                    fmeteo_paths.append(meteo_folder + '/' + files)
                    
            if len(fmeteo_paths) > 0:
            
                LAT2 = np.zeros(len(fmeteo_paths))
                LON2 = np.zeros(len(fmeteo_paths))
                DIST = np.zeros(len(fmeteo_paths))
                i = 0
                for fmeteo in fmeteo_paths:
            
                    reader = open(fmeteo, 'rb')
                    reader = csv.reader(reader, delimiter='\t')
                    reader = list(reader)
               
                    LAT2[i] = float(reader[2][1])
                    LON2[i] = float(reader[3][1])
                    DIST[i] = LatLong2Dist(LAT1, LON1, LAT2[i], LON2[i])
                    
                    i += 1
                    
                index = np.where(DIST == np.min(DIST))[0][0]
                          
                self.load_meteo_file(fmeteo_paths[index])
                QtCore.QCoreApplication.processEvents()
                
                self.draw_hydrograph()
    
    #===========================================================================       
    def select_meteo_file(self):
        '''
        This method is called by <btn_weather_dir.clicked.connect>. It prompts
        the user to select a valid Weather Data file.        
        '''
    #===========================================================================
         
        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                      self, 'Select a valid weather data file', 
                                      self.meteo_dir, '*.out')       
        QtCore.QCoreApplication.processEvents()
        QtCore.QCoreApplication.processEvents()
        QtCore.QCoreApplication.processEvents()
        self.load_meteo_file(filename)
    
    #===========================================================================       
    def load_meteo_file(self, filename):
    #===========================================================================
    
        if not filename:
            print 'Path is empty. Cannot load weather data file.'
            return
            
        self.meteo_dir = path.dirname(filename)
        self.hydrograph2display.fmeteo = filename
        self.hydrograph2display.finfo = filename[:-3] + 'log'
        
        self.meteo_data.load(filename)
        
        self.parent.write2console(
        '''<font color=black>Weather data set loaded successfully for
             station %s.</font>''' % self.meteo_data.station_name)
          
        self.meteo_info_widget.setText(self.meteo_data.info )
        
        if self.fwaterlvl:
            
            QtCore.QCoreApplication.processEvents()
            self.draw_hydrograph()
    
    #===========================================================================
    def update_graph_layout_parameter(self):
        '''
        This method is called either by the methods <save_graph_layout>
        or by <draw_hydrograph>. It fetches the values that are currently 
        displayed in the UI and save them in the class instance 
        <hydrograph2display> of the class <Hydrograph>.
        '''
    #===========================================================================
        
        if self.UpdateUI == False:
            return
            
        year = self.date_start_widget.date().year()
        month = self.date_start_widget.date().month()
        day = 1
        date = xldate_from_date_tuple((year, month, day),0)
        self.hydrograph2display.TIMEmin = date
        
        year = self.date_end_widget.date().year()
        month = self.date_end_widget.date().month()
        day = 1
        date = xldate_from_date_tuple((year, month, day),0)
        self.hydrograph2display.TIMEmax = date
        
        self.hydrograph2display.WLscale = self.waterlvl_scale.value()
        self.hydrograph2display.WLmin = self.waterlvl_max.value()
        
        self.hydrograph2display.RAINscale = self.Ptot_scale.value() 
        
        if self.graph_status.isChecked():
            self.hydrograph2display.title_state = 1
        else:
            self.hydrograph2display.title_state = 0
            
        self.hydrograph2display.title_text = self.graph_title.text()
        
        self.hydrograph2display.language = self.language_box.currentText()
             
    #===========================================================================        
    def load_graph_layout(self):
    #===========================================================================

        self.parent.check_project()
        
        #------------------------------------- Check if Waterlvl Data Exist ----
        
        if not self.fwaterlvl:
            
            self.parent.write2console(
            '''<font color=red>No valid water level data file currently 
                 selected. Cannot load graph layout.</font>''')
                               
            self.emit_error_message(
            '''<b>Please select a valid water level data file.</b>''')
            
            return
        
        #------------------------------------------- Check if Layout Exists ----
                
        filename = self.parent.projectdir + '/graph_layout.lst'
        name_well = self.waterlvl_data.name_well
        isLayoutExist = self.hydrograph2display.checkLayout(name_well, filename)
                    
        if isLayoutExist == False:
            
            self.parent.write2console(
            '''<font color=red>No graph layout exists for well %s.
               </font>''' % name_well)
            
            self.emit_error_message('''<b>No graph layout exists 
                                         for well %s.</b>''' % name_well)
                                             
            return
        
        #------------------------------------------------------ Load Layout ----
                    
        self.hydrograph2display.load_layout(name_well, filename)
        
        #------------------------------------------------------- Update UI -----
        
        self.UpdateUI = False
                                         
        date = self.hydrograph2display.TIMEmin
        date = xldate_as_tuple(date, 0)
        self.date_start_widget.setDate(QDate(date[0], date[1], date[2]))
        
        date = self.hydrograph2display.TIMEmax
        date = xldate_as_tuple(date, 0)
        self.date_end_widget.setDate(QDate(date[0], date[1], date[2]))
                                    
        self.waterlvl_scale.setValue(self.hydrograph2display.WLscale)
        self.waterlvl_max.setValue(self.hydrograph2display.WLmin)
        self.datum_widget.setCurrentIndex (self.hydrograph2display.WLdatum)
        
        self.Ptot_scale.setValue(self.hydrograph2display.RAINscale)
         
        if self.hydrograph2display.title_state == 1:
            self.graph_status.setCheckState(QtCore.Qt.Checked)
        else:                    
            self.graph_status.setCheckState(QtCore.Qt.Unchecked)
            
        self.graph_title.setText(self.hydrograph2display.title_text)
        
        #----- Check if Weather Data File exists -----
        
        if path.exists(self.hydrograph2display.fmeteo):
            self.meteo_data.load(self.hydrograph2display.fmeteo)
            self.meteo_info_widget.setText(self.meteo_data.info )
            self.parent.write2console(
            '''<font color=black>Graph layout loaded successfully for 
               well %s.</font>''' % name_well)
            QtCore.QCoreApplication.processEvents()
            self.draw_hydrograph()
        else:
            self.meteo_info_widget.setText('')
            self.parent.write2console(
            '''<font color=red>Unable to read the weather data file. %s
               does not exist.</font>''' % self.hydrograph2display.fmeteo)
            self.emit_error_message(
            '''<b>Unable to read the weather data file.<br><br>
               %s does not exist.<br><br> Please select another weather
               data file.<b>''' % self.hydrograph2display.fmeteo)
            self.hydrograph2display.fmeteo = []
            self.hydrograph2display.finfo = []
            
        self.UpdateUI = True
    
    #===========================================================================
    def save_config_isClicked(self):
    #===========================================================================
    
        if not self.fwaterlvl:
            
            self.parent.write2console(
            '''<font color=red>No valid water level file currently selected.
                 Cannot save graph layout.
               </font>''')
            
            self.msgError.setText(
            '''<b>Please select valid water level data file.</b>''')
            
            self.msgError.exec_()
            
            return
            
        if not self.hydrograph2display.fmeteo:
            
            self.parent.write2console(
            '''<font color=red>No valid weather data file currently selected. 
                 Cannot save graph layout.
               </font>''')
            
            self.msgError.setText(
                            '''<b>Please select valid weather data file.</b>''')
                            
            self.msgError.exec_()
            
            return
            
        #------------------------------------------- Check if Layout Exists ----
            
        filename = self.parent.projectdir + '/graph_layout.lst'
        if not path.exists(filename):
            # Force the creation of a new "graph_layout.lst" file
            self.parent.check_project()
            
        name_well = self.waterlvl_data.name_well
        isLayoutExist = self.hydrograph2display.checkLayout(name_well, filename)
        
        #------------------------------------------------------ Save Layout ----
        
        if isLayoutExist == True:
            self.msgBox.setText(
            '''<b>A graph layout already exists for well %s.<br><br> Do 
                 you want to replace it?</b>''' % name_well)
            override = self.msgBox.exec_()

            if override == self.msgBox.Yes:
                self.save_graph_layout(name_well)
                            
            elif override == self.msgBox.No:
                self.parent.write2console('''<font color=black>Graph layout 
                               not saved for well %s.</font>''' % name_well)
                
        else:            
            self.save_graph_layout(name_well)
              
    def save_graph_layout(self, name_well):
        
        self.update_graph_layout_parameter()
        filename = self.parent.projectdir + '/graph_layout.lst'
        self.hydrograph2display.save_layout(name_well, filename)
        self.parent.write2console(
        '''<font color=black>Graph layout saved successfully
             for well %s.</font>''' % name_well)
            
    def best_fit_waterlvl(self):
        
        if len(self.waterlvl_data.lvl) != 0:
            
            WLscale, WLmin = self.hydrograph2display.best_fit_waterlvl()
            
            self.waterlvl_scale.setValue(WLscale)
            self.waterlvl_max.setValue(WLmin)
            
    def best_fit_time(self):
            
        if len(self.waterlvl_data.time) != 0:
            
            TIME = self.waterlvl_data.time 
            date0, date1 = self.hydrograph2display.best_fit_time(TIME)
            
            self.date_start_widget.setDate(QDate(date0[0], date0[1], date0[2]))                                                        
            self.date_end_widget.setDate(QDate(date1[0], date1[1], date1[2]))
            
    def select_save_path(self):
       
        name_well = self.waterlvl_data.name_well
        dialog_dir = self.save_fig_dir + '/hydrograph_' + name_well
        
        dialog = QtGui.QFileDialog()
        dialog.setConfirmOverwrite(True)
        fname, ftype = dialog.getSaveFileName(
                                    caption="Save Figure", dir=dialog_dir,
                                    filter=('*.pdf;;*.svg'))
                                  
        if fname:         
            
            if fname[-4:] != ftype[1:]:
                # Add a file extension if there is none
                fname = fname + ftype[1:]
                
            self.save_fig_dir = path.dirname(fname)
            self.save_figure(fname)
            
    def save_figure(self, fname):
        
        self.hydrograph2display.generate_hydrograph(self.meteo_data)
                                       
        self.hydrograph2display.fig.savefig(fname)
        
    def draw_computeMode_waterlvl(self):
        
        self.waterlvl_calc.time = self.waterlvl_data.time
        self.waterlvl_calc.water_lvl = self.waterlvl_data.lvl
        self.waterlvl_calc.soilFilename = self.waterlvl_data.soilFilename
        
        self.waterlvl_calc.plot_water_levels() 
    
    def draw_hydrograph(self):
        
        if not self.fwaterlvl:
            console_text = ('<font color=red>Please select a valid water ' +
                            'level data file</font>')
            self.parent.write2console(console_text)
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            
            return
            
        if not self.hydrograph2display.fmeteo:
            console_text = ('<font color=red>Please select a valid ' +
                            'weather data file</font>')
            self.parent.write2console(console_text)
            self.emit_error_message(
            '''<b>Please select a valid Weather Data File first.</b>''')
            
            return
                    
        self.update_graph_layout_parameter()
        
        #----- Generate Graph -----
        
        self.hydrograph2display.generate_hydrograph(self.meteo_data)
        
        #----- Produce Figure from Graph -----
                        
        self.hydrograph_canvas.draw()

        size = self.hydrograph_canvas.size()
        width = size.width()
        height = size.height()        
        imgbuffer = self.hydrograph_canvas.buffer_rgba()
        image = QtGui.QImage(imgbuffer, width, height,
                             QtGui.QImage.Format_RGB32)                         
        image = QtGui.QImage.rgbSwapped(image)
        
        self.hydrograph_scrollarea.refresh_image(image)
    
    def language_changed(self):
        
        if self.UpdateUI == True:
            
            #---- Update Instance Variables ----
            
            self.hydrograph2display.language = self.language_box.currentText()
            
            #---- Update Graph if Exists ----
           
            if self.hydrograph2display.isHydrographExists == True:
                
                self.hydrograph2display.draw_ylabels()
                self.hydrograph2display.draw_xlabels()
        
                self.refresh_hydrograph()
                
    def Ptot_scale_changed(self):
        
        if self.UpdateUI == True:
            
            #---- Update Instance Variables ----
            
            self.hydrograph2display.RAINscale = self.Ptot_scale.value()
            
            #---- Update Graph if Exists ----
           
            if self.hydrograph2display.isHydrographExists == True:
                
                self.hydrograph2display.update_precip_scale()
                self.hydrograph2display.draw_ylabels()
            
                self.refresh_hydrograph()
                
        
    def waterlvl_scale_changed(self):
        
        if self.UpdateUI == True:
            
            #---- Update Instance Variables ----
        
            self.hydrograph2display.WLmin = self.waterlvl_max.value()
            self.hydrograph2display.WLscale = self.waterlvl_scale.value()
            
            #---- Update Graph if Exists ----
           
            if self.hydrograph2display.isHydrographExists == True:
                
                self.hydrograph2display.update_waterlvl_scale()
                self.hydrograph2display.draw_ylabels()
            
                self.refresh_hydrograph()
                
    def datum_changed(self, index):
        
        if self.UpdateUI == True:
            
            #---- Update Instance Variables ----
            
            self.hydrograph2display.WLdatum = index
            self.hydrograph2display.WLmin = (self.waterlvl_data.ALT - 
                                             self.hydrograph2display.WLmin)
          
            self.hydrograph2display.update_waterlvl_scale()            
            self.hydrograph2display.draw_waterlvl()
            self.hydrograph2display.draw_ylabels()
            
            self.refresh_hydrograph()
    
    def time_scale_changed(self):
        
        if self.UpdateUI == True:
            
            #---- Update Instance Variables ----
            
            year = self.date_start_widget.date().year()
            month = self.date_start_widget.date().month()
            day = 1
            date = xldate_from_date_tuple((year, month, day),0)
            self.hydrograph2display.TIMEmin = date
            
            year = self.date_end_widget.date().year()
            month = self.date_end_widget.date().month()
            day = 1
            date = xldate_from_date_tuple((year, month, day),0)
            self.hydrograph2display.TIMEmax = date
            
            #---- Update Graph if Exists ----
           
            if self.hydrograph2display.isHydrographExists == True:
               
                self.hydrograph2display.set_time_scale()
                self.hydrograph2display.draw_weather()
                self.hydrograph2display.draw_figure_title()
            
                self.refresh_hydrograph()
    
    def fig_title_state_changed(self):
        
        if self.graph_status.isChecked() == True:
            self.graph_title.setEnabled(True)
        else:
            self.graph_title.setEnabled(False)
        
        if self.UpdateUI == True:
           
           #---- Update Instance Variables ----
           
           if self.graph_status.isChecked():
               self.hydrograph2display.title_state = 1
               self.hydrograph2display.title_text = self.graph_title.text()
           else:
               self.hydrograph2display.title_state = 0
           
           #---- Update Graph if Exists ----
           
           if self.hydrograph2display.isHydrographExists == True:

               self.hydrograph2display.set_margins()
               self.hydrograph2display.draw_figure_title()
               self.refresh_hydrograph()
               
           else: # No hydrograph plotted yet
               pass
                
    def fig_title_changed(self):
        
        if self.UpdateUI == True :
            
            #---- Update Instance Variables ----
        
            self.hydrograph2display.title_text = self.graph_title.text()
            
            #---- Update Graph if Exists ----
            
            if self.hydrograph2display.isHydrographExists == True:
                        
                self.hydrograph2display.draw_figure_title()
                self.refresh_hydrograph()

            else: # No hydrograph plotted yet
               pass
    
    def refresh_hydrograph(self):
        
        self.hydrograph_canvas.draw()

        size = self.hydrograph_canvas.size()
        width = size.width()
        height = size.height()        
        imgbuffer = self.hydrograph_canvas.buffer_rgba()
        image = QtGui.QImage(imgbuffer, width, height,
                             QtGui.QImage.Format_RGB32)                         
        image = QtGui.QImage.rgbSwapped(image)
        
        self.hydrograph_scrollarea.refresh_image(image)
            
          
################################################################################
        
class TabDwnldData(QtGui.QWidget):                             # @TAB DOWNLOAD #

################################################################################
    
    def __init__(self, parent):
        super(TabDwnldData, self).__init__(parent)
        self.parent = parent
        self.initUI()        
        
    def initUI(self):
        
        self.dwnld_weather = dwnld_weather_data.dwnldWeather()
        self.dwnld_weather.set_workdir(self.parent.projectdir)
        
        #-------------------------------------------------------- MAIN GRID ----
        
        vLine1 = QtGui.QFrame()
        vLine1.setFrameStyle(styleDB.VLine)
        
        grid_MAIN = QtGui.QGridLayout()
        
        col = 0
        row = 0
        grid_MAIN.addWidget(self.dwnld_weather, row, col)
        
        grid_MAIN.setRowStretch(0, 500)
        
        grid_MAIN.setContentsMargins(10, 10, 10, 10) #Left, Top, Right, Bottom
        grid_MAIN.setSpacing(15)
        
        self.setLayout(grid_MAIN)
    
             
        
        
    #===========================================================================        
    def select_concatened_save_path(self):
        '''        
        This method allows the user to select a path for the file in which the 
        concatened data are going to be saved.
        
        ---- CALLED BY----
        
        (1) Event: btn_save.clicked.connect
        '''
    #===========================================================================

        if np.size(self.MergeOutput) != 0:
            StaName = self.MergeOutput[0, 1]
            YearStart = self.MergeOutput[8, 0][:4]
            YearEnd = self.MergeOutput[-1, 0][:4]
            climateID = self.MergeOutput[5, 1]
            
            # Check if the characters "/" or "\" are present in the station 
            # name and replace these characters by "-" if applicable.            
            intab = "/\\"
            outtab = "--"
            trantab = maketrans(intab, outtab)
            StaName = StaName.translate(trantab)
            
            project_dir = self.parent.projectdir
            filename = '%s (%s)_%s-%s.csv' % (StaName, climateID,
                                              YearStart, YearEnd)
            dialog_dir = project_dir + '/Meteo/Input/' + filename
                          
            fname, ftype = QtGui.QFileDialog.getSaveFileName(
                                         self, 'Save file', dialog_dir, '*.csv')
            
            if fname:                
                self.save_concatened_data(fname)    
    

###################################################################### @TAB FILL  
                                        
class TabFill(QtGui.QWidget): 

###################################################################### @TAB FILL
    
    def __init__(self, parent):
        super(TabFill, self).__init__(parent)
        self.parent = parent
        self.initUI() 
    
    #===========================================================================           
    def initUI(self):
    # Layout is organized with an ensemble of grids that are assembled
    # together on 3 different levels. First level is the main grid.
    # Second level is where are the LEFT and RIGHT grids. Finally, third
    # level is where are the SubGrids. The Left and Right grids can contain
    # any number of subgrids.
    #                              MAIN GRID                                                 
    #                 ----------------------------------                         
    #                 |               |                |
    #                 |   LEFT GRID   |   RIGHT GRID   |     
    #                 |               |                |     
    #                 ----------------------------------
    #
    #===========================================================================
        
        #--------------------------------------------------- Target Station ----
        
        #---- Widgets ----
        
        target_station_label = QtGui.QLabel('<b>%s</b>' % labelDB.fill_station)
        self.target_station = QtGui.QComboBox()
        self.target_station_info = QtGui.QTextEdit()
        self.target_station_info.setReadOnly(True)
        self.target_station_info.setMaximumHeight(110)
        
        self.btn3 = QtGui.QToolButton()
        self.btn3.setIcon(iconDB.refresh2)
        self.btn3.setAutoRaise(True)
        self.btn3.setIconSize(styleDB.iconSize2)
        
        #---- Grid ----
        
        subgrid_widget6 = (QtGui.QWidget())
                     
        subgrid6 = QtGui.QGridLayout()
                
        row = 0
        subgrid6.addWidget(target_station_label, row, 0, 1, 2)
        row = 1
        subgrid6.addWidget(self.target_station, row, 0)
        subgrid6.addWidget(self.btn3, row, 1)
        row = 2
        subgrid6.addWidget(self.target_station_info, row, 0, 1, 2)
        
        subgrid6.setSpacing(5)
        subgrid6.setColumnStretch(0, 500)
        subgrid_widget6.setLayout(subgrid6)
        subgrid6.setContentsMargins(0, 0, 0, 10) #Left, Top, Right, Bottom
        
       #----------------------------------------------------- Cutoff Values ----
        
        #---- Widgets ----
        
        Cutoff_title = QtGui.QLabel('<b>Stations Selection Criteria :</b>')
        
        Nmax_label = QtGui.QLabel('Maximum number of stations')
        self.Nmax = QtGui.QSpinBox ()
        self.Nmax.setRange(0, 99)
        self.Nmax.setSingleStep(1)
        self.Nmax.setValue(4)
        distlimit_label = QtGui.QLabel(labelDB.distlimit)
        distlimit_label.setToolTip(ttipDB.distlimit)
        self.distlimit = QtGui.QSpinBox()
        self.distlimit.setRange(-1, 9999)
        self.distlimit.setSingleStep(1)
        self.distlimit.setValue(100)
        self.distlimit.setToolTip(ttipDB.distlimit)
        altlimit_label = QtGui.QLabel(labelDB.altlimit)
        altlimit_label.setToolTip(ttipDB.altlimit)
        self.altlimit = QtGui.QSpinBox()
        self.altlimit.setRange(-1, 9999)
        self.altlimit.setSingleStep(1)
        self.altlimit.setValue(350)
        self.altlimit.setToolTip(ttipDB.altlimit)
        
        #---- Grid ----
        
        subgrid_widget2=(QtGui.QWidget())
                     
        subgrid2 = QtGui.QGridLayout()
        subgrid2.setSpacing(10)
        
        row = 0
        subgrid2.addWidget(Cutoff_title, row, 0, 1, 2)
        row += 1
        subgrid2.addWidget(Nmax_label, row, 1)
        subgrid2.addWidget(self.Nmax, row, 0)
        row += 1
        subgrid2.addWidget(distlimit_label, row, 1)
        subgrid2.addWidget(self.distlimit, row, 0)
        row += 1
        subgrid2.addWidget(altlimit_label, row, 1)
        subgrid2.addWidget(self.altlimit, row, 0)
        
        subgrid_widget2.setLayout(subgrid2)
        subgrid2.setContentsMargins(0, 10, 0, 10) #Left, Top, Right, Bottom
        subgrid2.setColumnStretch(1, 500)
         
        #------------------------------------------------- Regression Model ----
        
        #---- Widgets ----
        
        regression_model = QtGui.QFrame()
        
        regression_model_label = QtGui.QLabel(
                                    '<b>Multiple Linear Regression Model :</b>')
        regression_model_label.setAlignment(QtCore.Qt.AlignBottom)
        self.RMSE_regression = QtGui.QRadioButton('Ordinary Least Squares')
        self.RMSE_regression.setChecked(True)
        self.ABS_regression = QtGui.QRadioButton('Least Absolute Deviations')
        
        model_box =  QtGui.QVBoxLayout()
        model_box.addWidget(self.RMSE_regression)
        model_box.addWidget(self.ABS_regression)
        regression_model.setLayout(model_box)
        
        #---- Grid ----
        
        subgrid_widget3=(QtGui.QWidget())
        subgrid3 = QtGui.QGridLayout()
        
        subgrid3.setSpacing(10)
        row = 0
        subgrid3.addWidget(regression_model_label, row, 0)
        row = 1
        subgrid3.addWidget(regression_model, row, 0)
        
        subgrid3.setContentsMargins(0, 10, 0, 10) #Left, Top, Right, Bottom
        subgrid_widget3.setLayout(subgrid3)
        
        #---------------------------------------------------- Gapfill Dates ----
        
        #---- Widgets ----
        
        label_Dates_Title = QtGui.QLabel('<b>Gap Fill Data Record :</b>')
        label_From = QtGui.QLabel('From :  ')
        self.date_start_widget = QtGui.QDateEdit()
        self.date_start_widget.setDisplayFormat('dd / MM / yyyy')
        self.date_start_widget.setEnabled(False)
        label_To = QtGui.QLabel('To :  ')
        self.date_end_widget = QtGui.QDateEdit()
        self.date_end_widget.setEnabled(False)
        self.date_end_widget.setDisplayFormat('dd / MM / yyyy')
        
        #---- Grid ----
        
        subgrid_widget5 = QtGui.QWidget()                     
        subgrid5 = QtGui.QGridLayout()
                
        row = 0
        subgrid5.addWidget(label_Dates_Title, row, 0, 1, 3)
        row = 1
        subgrid5.addWidget(label_From, row, 1)
        subgrid5.addWidget(self.date_start_widget, row, 2)
        row = 2
        subgrid5.addWidget(label_To, row, 1)  
        subgrid5.addWidget(self.date_end_widget, row, 2)        
                
        subgrid5.setColumnStretch(4, 500)
        subgrid5.setColumnStretch(0, 500)
        subgrid5.setContentsMargins(0, 10, 0, 0) #Left, Top, Right, Bottom
        subgrid5.setSpacing(10)
        
        subgrid_widget5.setLayout(subgrid5)
        
        #======================================================= LEFT PANEL ====
         
        grid_leftPanel = QtGui.QGridLayout()
        LEFT_widget = QtGui.QFrame()
        LEFT_widget.setFrameStyle(styleDB.frame) 

        seprator1 = QtGui.QFrame()
        seprator1.setFrameStyle(styleDB.HLine)
        seprator2 = QtGui.QFrame()
        seprator2.setFrameStyle(styleDB.HLine)        
        seprator3 = QtGui.QFrame()
        seprator3.setFrameStyle(styleDB.HLine)
        
        row = 0 
        grid_leftPanel.addWidget(subgrid_widget6, row, 0, 1, 3) # SubGrid 6: Target Sta.
        row += 1
        grid_leftPanel.addWidget(seprator1, row, 0, 1, 3)       # Separator
        row += 1
        grid_leftPanel.addWidget(subgrid_widget2, row, 0, 1, 3) # SubGrid 2: Cutoff Values
        row += 1  
        grid_leftPanel.addWidget(seprator2, row, 0, 1, 3)       # Separator
        row += 1 
        grid_leftPanel.addWidget(subgrid_widget3, row, 0, 1, 3) # SubGrid 3: MLRM Selection
        row += 1
        grid_leftPanel.addWidget(seprator3, row, 0, 1, 3)       # Separator
        row += 1
        grid_leftPanel.addWidget(subgrid_widget5, row, 0, 1, 3) # SubGrid 5: GapFill Dates
        
        grid_leftPanel.setRowStretch(row+1, 500)
        grid_leftPanel.setContentsMargins(10, 10, 10, 10) # (L, T, R, B)
        
        LEFT_widget.setLayout(grid_leftPanel)
        
        #------------------------------------------------------ RIGHT PANEL ----
       
        self.FillTextBox = QtGui.QTextEdit()
        self.FillTextBox.setReadOnly(True)
#        self.FillTextBox.setFrameStyle(0)
        self.FillTextBox.setFrameStyle(styleDB.frame)
        
        grid_RIGHT = QtGui.QGridLayout()
        RIGHT_widget = QtGui.QFrame()
#        RIGHT_widget.setFrameStyle(styleDB.frame)
        RIGHT_widget.setFrameStyle(0)
        
        row = 0
        grid_RIGHT.addWidget(self.FillTextBox, row, 0)
        
        # Total number of columns = 3        
        
        grid_RIGHT.setRowStretch(0, 500)
        grid_RIGHT.setColumnStretch(0, 500)
        grid_RIGHT.setContentsMargins(0, 0, 0, 0) #Left, Top, Right, Bottom
                        
        RIGHT_widget.setLayout(grid_RIGHT)
        
        #---------------------------------------------------------- TOOLBAR ----
        
        self.btn_fill = QtGui.QPushButton(labelDB.btn_fill_weather)
        self.btn_fill.setIcon(iconDB.play)
        self.btn_fill.setToolTip(ttipDB.btn_fill)
        self.btn_fill.setIconSize(styleDB.iconSize2)
        
        self.btn_fill_all = QtGui.QPushButton(labelDB.btn_fill_all_weather)
        self.btn_fill_all.setToolTip(ttipDB.btn_fill_all)
        self.btn_fill_all.setIcon(iconDB.forward)
        self.btn_fill_all.setIconSize(styleDB.iconSize2)
        
        grid_toolbar = QtGui.QGridLayout()
        widget_toolbar = QtGui.QFrame()
        
        row = 0
        grid_toolbar.addWidget(self.btn_fill, row, 0)
        grid_toolbar.addWidget(self.btn_fill_all, row, 1)
        
        grid_toolbar.setSpacing(5)
        grid_toolbar.setContentsMargins(0, 0, 0, 0)
        grid_toolbar.setColumnStretch(2, 100)
        
        widget_toolbar.setLayout(grid_toolbar)
        
        #-------------------------------------------------------- MAIN GRID ----
        
        grid_MAIN = QtGui.QGridLayout()
        grid_MAIN.setSpacing(15)
        
        row = 0
        grid_MAIN.addWidget(LEFT_widget, row, 0)
        grid_MAIN.addWidget(RIGHT_widget, row, 1)
        row += 1
        grid_MAIN.addWidget(widget_toolbar, row, 0, 1, 2)
                
        grid_MAIN.setColumnStretch(1, 500)
        grid_MAIN.setRowStretch(0, 500)
#        grid_MAIN.setColumnMinimumWidth(1, 700)
        grid_MAIN.setContentsMargins(15, 15, 15, 15) #Left, Top, Right, Bottom
        self.setLayout(grid_MAIN)        
        
    #-------------------------------------------------------------- EVENTS -----
        
        self.fillworker = FillWorker(self)
        self.fillworker.ProgBarSignal.connect(self.setProgBarSignal)
        self.fillworker.ConsoleSignal.connect(self.setConsoleSignal)        
        self.fillworker.EndProcess.connect(self.fill_process_finished)
        
        self.btn3.clicked.connect(self.load_data_dir_content) # Refresh btn
        self.target_station.currentIndexChanged.connect(self.correlation_UI)
        self.btn_fill.clicked.connect(self.fill_is_clicked)
        self.btn_fill_all.clicked.connect(self.fill_all_is_clicked)
        
        self.distlimit.valueChanged.connect(self.correlation_table_display)
        self.altlimit.valueChanged.connect(self.correlation_table_display)
        self.date_start_widget.dateChanged.connect(
                                                 self.correlation_table_display)
        self.date_end_widget.dateChanged.connect(self.correlation_table_display)
        
    #-----------------------------------------------------------MESSAGE BOX-----
                                          
        self.msgBox = QtGui.QMessageBox()
        self.msgBox.setIcon(QtGui.QMessageBox.Warning)
        self.msgBox.setWindowTitle('Error Message')
        
    #--------------------------------------------------------INITIALIZATION-----
        
        self.WEATHER = Weather_File_Info() 
        self.TARGET = Target_Station_Info()
        self.FILLPARAM = GapFill_Parameters()
        self.fill_all_inProgress = False
        self.CORRFLAG = 'on'  # Correlation calculation won't be triggered by
                              # events when this is 'off'
        
    #---------------------------------------------------------------------------
        
#    def enable_dates_widgets(self, progress):
#        self.date_start_widget.setEnabled(True)
#        self.date_end_widget.setEnabled(True)
    
#    def disable_UI(self):
#        self.date_start_widget.setEnabled(False)
#        self.date_end_widget.setEnabled(False)        
            
    def setProgBarSignal(self, progress): 
        
        self.parent.pbar.setValue(progress)
        
    
    def setConsoleSignal(self, console_text):
    
        self.parent.write2console(console_text)
   
    #===========================================================================
    def load_data_dir_content(self) : # def set_comboBox_item(self):
        '''
        Initiate the loading of Weater Data Files contained in the 
        </Meteo/Input> folder and display the resulting station list in the
        Target station combo box widget.
        '''
    #===========================================================================
                
        self.FillTextBox.setText('')
        self.target_station_info.setText('')
        self.target_station.clear()
        QtGui.QApplication.processEvents()
        
        self.CORRFLAG = 'off' # Correlation calculation won't be triggered when
                              # this is s'off'
        
        input_folder = self.parent.projectdir + '/Meteo/Input'
        
        if path.exists(input_folder):            
            
            # Generate a list of data file paths.            
            Sta_path = []
            for files in listdir(input_folder):
                if files.endswith(".csv"):
                    Sta_path.append(input_folder + '/' + files)
            
            if len(Sta_path) > 0:
                self.WEATHER.load_and_format_data(Sta_path)
                self.WEATHER.generate_summary(self.parent.projectdir)
                self.set_fill_and_save_dates()
                
                self.target_station.addItems(self.WEATHER.STANAME)
                
                self.target_station.setCurrentIndex(-1)
                self.TARGET.index = -1
            else:
                'Data Directory is empty. Do nothing'
        else:
            'Data Directory path does not exists. Do nothing'
            
        self.CORRFLAG = 'on'
        
    #===========================================================================
    def set_fill_and_save_dates(self):
    # Set first and last dates of the data serie in the boxes of the
    # <Fill and Save> area.  
    #===========================================================================                                                          
        
        if len(self.WEATHER.DATE) > 0: 

            self.date_start_widget.setEnabled(True)
            self.date_end_widget.setEnabled(True)
            
            DATE = self.WEATHER.DATE
            
            DateMin = QDate(DATE[0, 0], DATE[0, 1], DATE[0, 2])
            DateMax = QDate(DATE[-1, 0], DATE[-1, 1], DATE[-1, 2])
            
            self.date_start_widget.setDate(DateMin)
            self.date_start_widget.setMinimumDate(DateMin)
            self.date_start_widget.setMaximumDate(DateMax)
                    
            self.date_end_widget.setDate(DateMax)
            self.date_end_widget.setMinimumDate(DateMin)
            self.date_end_widget.setMaximumDate(DateMax)
            
    #===========================================================================       
    def correlation_UI(self):
    # Calculate automatically the correlation coefficients when a target
    # station is selected by the user in the drop-down menu.
    #===========================================================================
        
        if self.CORRFLAG == 'on' and self.target_station.currentIndex() != -1:
            
            # Update information for the target station.
            self.TARGET.index = self.target_station.currentIndex()
            self.TARGET.name = self.WEATHER.STANAME[self.TARGET.index]
            
            # calculate correlation coefficient between data series of the
            # target station and each neighboring station for every
            # meteorological variable
            self.TARGET.CORCOEF = correlation_worker(self.WEATHER, 
                                                     self.TARGET.index)
                                                
            # Calculate horizontal distance and altitude difference between
            # the target station and each neighboring station,
            self.TARGET.HORDIST, self.TARGET.ALTDIFF = \
                              alt_and_dist_calc(self.WEATHER, self.TARGET.index)
            
            self.parent.write2console(
            '''<font color=black>
                 Correlation coefficients calculation for station %s completed
               </font>''' % (self.TARGET.name))
                                      
            self.correlation_table_display()
            
        elif self.CORRFLAG == 'off':
            'Do nothing'
    
    #===========================================================================      
    def correlation_table_display(self):
    # This method plot the table in the display area. It is separated from
    # the method <Correlation_UI> above because red numbers and statistics
    # regarding missing data for the selected time period can be updated in
    # the table when the user changes the values without having to
    # recalculate the correlation coefficient each time.
    #===========================================================================
       
        if self.CORRFLAG == 'on' and self.target_station.currentIndex() != -1:
           
            self.FILLPARAM.limitDist = int(self.distlimit.text())
            self.FILLPARAM.limitAlt = int(self.altlimit.text())
           
            y = self.date_start_widget.date().year()
            m = self.date_start_widget.date().month()
            d = self.date_start_widget.date().month()
            self.FILLPARAM.time_start = xldate_from_date_tuple((y, m, d), 0)
     
            y = self.date_end_widget.date().year()
            m = self.date_end_widget.date().month()
            d = self.date_end_widget.date().day()
            self.FILLPARAM.time_end = xldate_from_date_tuple((y, m, d), 0)
           
            table, target_info = correlation_table_generation(self.TARGET,
                                                              self.WEATHER,
                                                              self.FILLPARAM)
   
            self.FillTextBox.setText(table)
            self.target_station_info.setText(target_info)
           
        else:
            'Do nothing'
    
    #===========================================================================
    def fill_all_is_clicked(self):
    #===========================================================================        
        
        if self.fill_all_inProgress == True: # Stop the process
            
            self.fill_all_inProgress = False     

            #---- Reset UI state ----

            self.btn_fill_all.setIcon(iconDB.forward)        
            self.target_station.setEnabled(True)
            self.btn_fill.setEnabled(True)
            self.parent.menubar_widget.setEnabled(True)
            self.btn3.setEnabled(True)
            self.parent.project_display.setEnabled(True)
            self.parent.pbar.hide()
            
            QtGui.QApplication.processEvents()
            
            if self.fillworker.isRunning():
                # Pass a flag to the worker in order to force him to stop.
                self.fillworker.STOP = True
            else:
                'Do nothing. Worker is not running.'
                
            return
                
        #------------------------------------------------ CHECKS FOR ERRORS ----
       
        y = self.date_start_widget.date().year()
        m = self.date_start_widget.date().month()
        d = self.date_start_widget.date().month()
        time_start = xldate_from_date_tuple((y, m, d), 0)
 
        y = self.date_end_widget.date().year()
        m = self.date_end_widget.date().month()
        d = self.date_end_widget.date().day()
        time_end = xldate_from_date_tuple((y, m, d), 0)
        
        if len(self.WEATHER.STANAME) == 0:

            self.msgBox.setText('<b>Data directory</b> is empty.')
            self.msgBox.exec_()
            
            print 'No target station selected.'
            
            return

        if time_start > time_end:
            
            self.msgBox.setText('<b>Fill and Save Data</b> start date is ' +
                                'set to a later time than the end date.')
            self.msgBox.exec_()
            
            print 'The time period is invalid.'
            
            return
        
        #------------------------------------------------------START THREAD ----
       
        self.fill_all_inProgress = True
        
        #---- Update UI ----
        
        self.btn_fill_all.setIcon(iconDB.stop)
        self.target_station.setEnabled(False)
        self.btn_fill.setEnabled(False)
        self.parent.menubar_widget.setEnabled(False)
        self.btn3.setEnabled(False)
        self.parent.project_display.setEnabled(False)
        self.parent.pbar.show()
        
        self.CORRFLAG = 'off' 
        self.target_station.setCurrentIndex(0)
        self.TARGET.index = self.target_station.currentIndex()
        self.TARGET.name = self.WEATHER.STANAME[self.TARGET.index]
                        
        self.CORRFLAG = 'on'
        
        QtGui.QApplication.processEvents()                
        
        self.correlation_UI()
        
        #---- Pass information to the worker ----
        
        self.fillworker.project_dir = self.parent.projectdir
        
        self.fillworker.time_start = time_start
        self.fillworker.time_end = time_end                       
        
        self.fillworker.WEATHER = self.WEATHER
        self.fillworker.TARGET = self.TARGET
                                    
        self.fillworker.regression_mode = self.RMSE_regression.isChecked()
        
        self.fillworker.full_error_analysis = \
                                        self.parent.whatPref.full_error_analysis
    
        #---- Start the gapfilling procedure ----
    
        self.fillworker.start()
        
    #===========================================================================                                          
    def fill_is_clicked(self):
        """
        Method that handles the gapfilling process on the UI side for a single
        weather station.
    
        Check if there is anything wrong with the parameters defined by the user
        before starting the fill process and issue warning if anything is wrong.
        """
    #===========================================================================
        
        if self.fillworker.isRunning(): # Stop the process
            
            #---- Reset UI ----
            
            self.btn_fill.setIcon(iconDB.play)
            self.target_station.setEnabled(True)
            self.btn_fill_all.setEnabled(True)
            QtGui.QApplication.processEvents()
            self.parent.pbar.hide()
            
            # Pass a flag to the worker in order to force him to stop.
            self.fillworker.STOP = True
            
            return
            
        #------------------------------------------------- CHECK FOR ERRORS ----
            
        y = self.date_start_widget.date().year()
        m = self.date_start_widget.date().month()
        d = self.date_start_widget.date().month()
        time_start = xldate_from_date_tuple((y, m, d), 0)
 
        y = self.date_end_widget.date().year()
        m = self.date_end_widget.date().month()
        d = self.date_end_widget.date().day()
        time_end = xldate_from_date_tuple((y, m, d), 0)
        
        if self.target_station.currentIndex() == -1:

            self.msgBox.setText('No <b>Target station</b> is currently ' +
                                'selected.')
            self.msgBox.exec_()
            print 'No target station selected.'
            
            return
            
        if time_start > time_end:
            
            self.msgBox.setText('<b>Gap Fill Data Record</b> start date is ' +
                                'set to a later time than the end date.')
            self.msgBox.exec_()
            print 'The time period is invalid.'
            
            return
        
        #----------------------------------------------------- START THREAD ----
             
        #---- Update UI ----
        
        self.btn_fill.setIcon(iconDB.stop)
        self.target_station.setEnabled(False)
        self.btn_fill_all.setEnabled(False)
        self.parent.pbar.show()
        
        #---- Pass information to the worker ----
        
        self.fillworker.project_dir = self.parent.projectdir
        
        self.fillworker.time_start = time_start
        self.fillworker.time_end = time_end                       
        
        self.fillworker.WEATHER = self.WEATHER
        self.fillworker.TARGET = self.TARGET
                                    
        self.fillworker.regression_mode = self.RMSE_regression.isChecked()
        
        self.fillworker.full_error_analysis = \
                                        self.parent.whatPref.full_error_analysis
    
        #---- Start the gapfilling procedure ----
    
        self.fillworker.start()
    
    #===========================================================================       
    def fill_process_finished(self, progress):
    # <fill_process_finished> is called after a data serie has been filled
    # and saved normally.
    #===========================================================================    
       
        next_station_index = self.target_station.currentIndex() + 1
        nSTA = len(self.WEATHER.STANAME)
        
        if self.fill_all_inProgress == False:
        # Fill process completed sucessfully for the current weather station.
            self.btn_fill.setIcon(iconDB.play)
            self.target_station.setEnabled(True)
            self.btn_fill_all.setEnabled(True)
            self.parent.pbar.hide()
            
        elif self.fill_all_inProgress == True and next_station_index < nSTA:
            # Fill All process in progress, continue with next weather station.
        
            self.CORRFLAG = 'off' 
            self.target_station.setCurrentIndex(next_station_index)
            self.TARGET.index = self.target_station.currentIndex()
            self.TARGET.name = \
                        self.WEATHER.STANAME[self.target_station.currentIndex()]
            self.CORRFLAG = 'on'
            
            # Calculate correlation coefficient for the next station.
            self.correlation_UI()
            
            # Start the gapfilling procedure for the next station.
            self.fillworker.start()    
            
        elif self.fill_all_inProgress == True and next_station_index == nSTA:
            # Fill All process was completed sucessfully.
            
            self.fill_all_inProgress = False
            
            # Reset UI state
            self.btn_fill_all.setIcon(iconDB.forward)        
            self.target_station.setEnabled(True)
            self.btn_fill.setEnabled(True)
            self.parent.menubar_widget.setEnabled(True)
            self.btn3.setEnabled(True)
            self.parent.project_display.setEnabled(True)
            self.parent.pbar.hide()


##################################################################### @TAB ABOUT
     
class TabAbout(QtGui.QWidget):                                             
    
##################################################################### @TAB ABOUT
    
    
    def __init__(self, parent):
        super(TabAbout, self).__init__(parent)
        self.parent = parent
        self.initUI_About()        
        
    def initUI_About(self):
                
        #--------------------------------------------------Widgets creation-----
        
        AboutTextBox = QtGui.QTextEdit()
        AboutTextBox.setReadOnly(True)
        #AboutTextBox.setAlignment(QtCore.Qt.AlignCenter)
        
        #-------------------------------------------------Grid organization----- 
        
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        
        grid.addWidget(AboutTextBox, 0, 1)
        
        grid.setColumnStretch(0, 500)
        grid.setColumnStretch(2, 500)
        grid.setColumnMinimumWidth(1, 850)
        
        self.setLayout(grid)
        
        #------------------------------------------Variables initialization-----
        
        about_text = '''<p align="center">
                        <br><br>
                        <font size=16><b>%s</b></font>
                        <br>
                        <font size=4>
                          <i>Well Hydrograph Analysis Toolbox</i>
                        </font>
                        <br><br>
                        <b>Copyright 2014 Jean-Sebastien Gosselin</b>
                        <br><br>                         
                        Institut national de la recherche scientifique
                        <br>
                        Centre Eau Terre Environnement (INRS-ETE)
                        <br>
                        490 rue de la Couronne, Quebec, QC
                        <br>
                        jnsebgosselin@gmail.com
                        </p>
                        <p align="center" style="margin-right:150px; 
                        margin-left:150px">
                        <br><br>%s is free software: 
                        you can redistribute it and/or modify it under the terms
                        of the GNU General Public License as published by the 
                        Free Software Foundation, either version 3 of the 
                        License, or (at your option) any later version.                       
                        <br><br>
                        This program is distributed in the hope that it will be
                        useful, but WITHOUT ANY WARRANTY; without even the
                        implied warranty of MERCHANTABILITY or FITNESS FOR A
                        PARTICULAR PURPOSE. See the GNU General Public 
                        License for more details.
                        <br><br>
                        You should have received a copy of the GNU General  
                        Public License along with this program.  If not, see                    
                        http://www.gnu.org/licenses.
                        <br><br>
                        </p>
                        <p align="right" style="margin-right:150px">
                        Last modification: %s </p>''' % (software_version,
                        software_version, last_modification)
        
        AboutTextBox.setText(about_text)

       
################################################################################
#                                                                           
#                             @SECTION WORKER                             
#                                                                          
################################################################################
        
    
#===============================================================================
class Target_Station_Info():
# Class that contains all the information relative the target station, including
# correlation coefficient 2d matrix, altitude difference and horizontal
# distances arrays. The instance of this class in the code is TARGET.
#===============================================================================


    def __init__(self):        
        self.index = -1 # Target station index in the DATA matrix and STANAME
                        # array of the class WEATHER.
        
        self.name = [] # Target station name
        
        self.province = []
        self.altitude = []
        self.longitude = []
        self.latitude = []
        
        self.CORCOEF = [] # 2D matrix containing the correlation coefficients 
                          # betweein the target station and the neighboring
                          # stations for each meteorological variable.
                          # row : meteorological variables
                          # colm: weather stations
        
        self.ALTDIFF = [] # Array with altitude difference between the target
                          # station and every other station. Target station is
                          # included with a 0 value at index <index>.
        
        self.HORDIST = [] # Array with horizontal distance between the target
                          # station and every other station. Target station is
                          # included with a 0 value at index <index>
    
#===============================================================================
def alt_and_dist_calc(WEATHER, target_station_index):
# <alt_and_dist_calc> computes the horizontal distance in km and the altitude
# difference in m between the target station and each neighboring stations
#===============================================================================
   
    ALT = WEATHER.ALT
    LAT = WEATHER.LAT
    LON = WEATHER.LON

    nSTA = len(ALT) # number of stations including target
    
    HORDIST = np.zeros(nSTA) # distances of neighboring station from target
    ALTDIFF = np.zeros(nSTA) # altitude differences
    
    for i in range(nSTA): 
        HORDIST[i]  = LatLong2Dist(LAT[target_station_index], 
                                   LON[target_station_index],
                                   LAT[i], LON[i])
                                           
        ALTDIFF[i] = ALT[i] - ALT[target_station_index]
    
    HORDIST = np.round(HORDIST, 1)
    ALTDIFF = np.round(ALTDIFF, 1)
    
    return HORDIST, ALTDIFF
    
    
#===============================================================================
def correlation_worker(WEATHER, target_station_index):
# This function computes the correlation coefficients between the 
# target station and the neighboring stations for each meteorological variable.
# 
# Results are stored in a 2D matrix <CORCOEF> where:#  
#   rows :    meteorological variables
#   columns : weather stations
#===============================================================================
    DATA = WEATHER.DATA
    
    nVAR = len(DATA[0, 0, :])  # number of meteorological variables
    nSTA = len(DATA[0, :, 0])  # number of stations including target
   
    print; print 'Data import completed'
    print 'correlation coefficients computation in progress'
    
    CORCOEF = np.zeros((nVAR, nSTA)) * np.nan
    
    Ndata_limit = int(365 / 2.) # Minimum number of pair of data necessary
                                # between the target and a neighboring station
                                # to compute a correlation coefficient.

    for i in range(nVAR): 
        for j in range(nSTA):
                        
            # Rows with nan entries are removed from the data matrix.
            DATA_nonan = np.copy(DATA[:, (target_station_index, j), i])
            DATA_nonan = DATA_nonan[~np.isnan(DATA_nonan).any(axis=1)]

            # Compute how many pair of data are available for the correlation
            # coefficient calculation. For the precipitation, entries with 0
            # are not considered.
            if i in (0, 1, 2):
                Nnonan = len(DATA_nonan[:, 0])           
            else:                
                Nnonan = sum((DATA_nonan != 0).any(axis=1))
            
            # A correlation coefficient is computed between the target station
            # and the neighboring station <j> for the variable <i> if there is
            # enough data.
            if Nnonan >= Ndata_limit:
                CORCOEF[i, j] = np.corrcoef(DATA_nonan, rowvar=0)[0,1:]
            else:
                pass #Do nothing. Value will be nan by default.
        
    print 'correlation coefficients computation completed' ; print        

    return CORCOEF

#===============================================================================
def correlation_table_generation(TARGET, WEATHER, FILLPARAM): 
# This fucntion generate the output to be displayed in the <Fill Tab> display
# area after a target station has been selected by the user.
#===============================================================================                                  

    STANAME = WEATHER.STANAME
    
    FIELD2 = ['&#916;Alt.<br>(m)', 'Dist.<br>(km)', 'Tmax', 
              'Tmin', 'Tmean', 'Ptot']
        
    nSTA = len(STANAME)
    nVAR = len(WEATHER.VARNAME)
    Ndata_limit = int(365 / 2.)
    
    limitDist = FILLPARAM.limitDist
    limitAlt = FILLPARAM.limitAlt
    
#-------------------------------------------------TARGET STATION INFO TABLE-----
    
    date_start = xldate_as_tuple(FILLPARAM.time_start, 0)
    date_start = '%02d/%02d/%04d' % (WEATHER.DATE_START[TARGET.index, 2],
                                     WEATHER.DATE_START[TARGET.index, 1],
                                     WEATHER.DATE_START[TARGET.index, 0])
                                            
    date_end = xldate_as_tuple(FILLPARAM.time_end, 0)
    date_end = '%02d/%02d/%04d' % (WEATHER.DATE_END[TARGET.index, 2],
                                   WEATHER.DATE_END[TARGET.index, 1],
                                   WEATHER.DATE_END[TARGET.index, 0])
    
    FIELDS = ['Latitude', 'Longitude', 'Altitude', 'Data date start',
              'Data date end']
              
    HEADER = [WEATHER.LAT[TARGET.index],
              WEATHER.LON[TARGET.index],
              WEATHER.ALT[TARGET.index],
              date_start,
              date_end]
              
    target_info = '''<table border="0" cellpadding="1" cellspacing="0" 
                     align="left">'''
    
    for i in range(len(HEADER)):
        target_info += '<tr>' # + <td width=10></td>'
        target_info +=   '<td align="left">%s</td>' % FIELDS[i]
        target_info +=   '<td align="left">&nbsp;:&nbsp;</td>'
        target_info +=   '<td align="left">%s</td>' % HEADER[i]
        target_info += '</tr>'
        
    target_info +=  '</table>' 
    
#-------------------------------------------------------------SORT STATIONS-----
    
    # Stations best correlated with the target station are displayed toward
    # the top of the table while neighboring stations poorly correlated are
    # displayed toward the bottom.
    
    # Define a criteria for sorting the correlation quality of the stations.
    CORCOEF = TARGET.CORCOEF
    DATA = WEATHER.DATA
    TIME = WEATHER.TIME
              
    SUM_CORCOEF = np.sum(CORCOEF, axis=0) * -1 # Sort in descending order.
    index_sort = np.argsort(SUM_CORCOEF)
    
    # Reorganize the data.
    CORCOEF = CORCOEF[:, index_sort]
    DATA = DATA[:, index_sort, :]
    STANAME = STANAME[index_sort]
    
    HORDIST = TARGET.HORDIST[index_sort]
    ALTDIFF = TARGET.ALTDIFF[index_sort]
    target_station_index = np.where(TARGET.name==STANAME)[0]
    
    index_start = np.where(TIME == FILLPARAM.time_start)[0][0]
    index_end = np.where(TIME == FILLPARAM.time_end)[0][0]
              
#---------------------------------------------------------CORRELATION TABLE-----
    
    fill_date_start = xldate_as_tuple(FILLPARAM.time_start, 0)
    fill_date_start = '%02d/%02d/%04d' % (fill_date_start[2],
                                          fill_date_start[1],
                                          fill_date_start[0])
                                            
    fill_date_end = xldate_as_tuple(FILLPARAM.time_end, 0)
    fill_date_end = '%02d/%02d/%04d' % (fill_date_end[2],
                                        fill_date_end[1],
                                        fill_date_end[0])
                                        
    #----------------------------------------------------missing data table-----
                                        
    FIELDS = ['Tmax', 'Tmin', 'Tmean', 'Ptot', 'TOTAL']
    
    table = '''<font>
                 Number of missing data from <b>%s</b> to <b>%s</b> for
                 station <b>%s</b>:
               </font>
               <br>
               <table border="1" cellpadding="3" cellspacing="0" 
               align="center">
                 <tr>''' % (fill_date_start, fill_date_end, TARGET.name)
                 
    for field in FIELDS[:-1]:
        table +=  '<td width=147.5 align="center">%s</td>' % field
        
    table +=  '''</tr>
                 <tr>'''
                 
    total_nbr_data = index_end - index_start + 1
    for var in range(nVAR):                
        nbr_nan = np.isnan(
                       DATA[index_start:index_end+1, target_station_index, var])
        nbr_nan = float(np.sum(nbr_nan))
    
        nan_percent = round(nbr_nan / total_nbr_data * 100, 1)

        table += '''<td align="center">
                      %d&nbsp;&nbsp;(%0.1f %%)
                    </td>''' % (nbr_nan, nan_percent)
                    
    table +=  '''</tr>
               </table>
               <br>'''
    
    #-----------------------------------------------------correlation table-----
    
    table += '''<p>
                  Altitude difference, horizontal distance and correlation
                  coefficients for each meteorological variables, calculated
                  between station <b>%s</b> and its neighboring stations :
                </p>
                <br>
                <table border="1" cellpadding="3" cellspacing="0" 
                 align="center">                               
                  <tr> 
                    <td align="center" valign="middle" width=30 rowspan="2">
                      #
                    </td>
                    <td align="center" valign="middle" width=200 rowspan="2">
                      Neighboring Stations
                    </td>''' % TARGET.name
    
    for field in FIELD2[:2]:
        table += '''<td width=60 align="center" valign="middle" rowspan="2">
                      %s
                    </td>''' % field
                    
    table +=     '''<td 240 align="center" colspan="4">
                      Correlation Coefficients
                    </td>                    
                  <tr>'''

    for field in FIELD2[2:]:
        table += '<td width=60 align="center" rowspan="1">%s</td>' % (field)
    
    index = range(nSTA)
    index.remove(target_station_index)
    counter = 1
    for i in index:
        
        table += '''</tr>
                    <tr>
                      <td align="center" valign="middle">%02d</td>
                      <td >
                        <font size="3">%s</font>
                      </td>
                      <td align="right" valign="middle">''' % (counter,
                                                               STANAME[i])
        
        if abs(ALTDIFF[i]) >= limitAlt and limitAlt >= 0:
            table +=   '<font color="red">'
        else:
            table +=   '<font>'
            
        table +=       '''%0.1f&nbsp;&nbsp;
                        </font>
                      </td>
                      <td align="right" valign="middle">''' % ALTDIFF[i]
        
        if HORDIST[i] >= limitDist and limitDist >= 0:
            table +=   '<font color="red">'
        else :
            table +=   '<font>'
            
        table +=       '''%0.1f&nbsp;&nbsp;
                        </font>
                      </td>''' % HORDIST[i]
                      
        for value in np.round(CORCOEF[:, i], 3):
            table += '<td align="center" valign="middle">'
            if value > 0.7:
                table += '<font>%0.3f</font></td>' % (round(value, 3))                          
            else:
                table += ('<font color="red">%0.3f</font></td>') % (value)
                
        counter += 1
        
    table += '''  </tr>
                </table>
                <p>
                  Correlation coeffificients are set to <b>nan</b> for a given 
                  variable if there is less than <b>%d</b> pairs of data 
                  between the target and the neighboring station.
                </p>''' % (Ndata_limit)
             
    return table, target_info


#===============================================================================
class GapFill_Parameters():
# Class that contains all the relevant parameters for the gapfilling procedure.
# Main instance of this class in the code is <FILLPARAM>.
#===============================================================================    
    
   def __init__(self):
       
        self.time_start = 0  # Fill and Save start date.
        self.time_end = 0    # Fill and Save end date.
        self.index_start = 0 # Time index for start date
        self.index_end = 0   # Time index for end date
        
        self.regression_mode = True
        
        self.NSTAmax = 0 # Max number of neighboring station to use in the 
                         # regression model.
        self.limitDist = 0 # Cutoff limit for the horizontal distance between
                           # the target and the neighboring stations.
        self.limitAlt = 0 # Cutoff limit for the altitude difference between
                          # the target and the neighboring stations.
        
#===============================================================================
class FillWorker(QtCore.QThread):
    """
    This functions is started on the UI side when the "Fill" or "Fill All"
    button of the Tab named "Fill Data" is clicked on. It is the main routine
    that fill the missing data in the weather record.
    """
#===============================================================================
    
    ProgBarSignal = QtCore.Signal(int)
    ConsoleSignal = QtCore.Signal(str)
    EndProcess = QtCore.Signal(int)
    
    def __init__(self, parent):
        super(FillWorker, self).__init__(parent)
 
        self.parent = parent
        
        # All the following variables are updated on the UI side:
        
        self.time_start = 0
        self.time_end = 0
        self.WEATHER = []
        self.TARGET = []
        self.project_dir = getcwd()
        
        self.regression_mode = True
        # --> if True = Ordinary Least Square
        # --> if False = Least Absolute Deviations
        
        self.STOP = False # Flag used to stop the Thread on the UI side
        
        self.full_error_analysis = False 
        # A complete analysis of the estimation errors is conducted
        # if <full_error_analysis> is set to True.
        # NOTE: This option is NOT connected with the UI and is experimental.
        
    def run(self): 
        
        DATA = np.copy(self.WEATHER.DATA)
        DATE = np.copy(self.WEATHER.DATE)
        
        YEAR = DATE[:, 0]
        MONTH = DATE[:, 1]
        DAY = DATE[:, 2]
        
        TIME = np.copy(self.WEATHER.TIME)
        index_start = np.where(TIME == self.time_start)[0][0]
        index_end = np.where(TIME == self.time_end)[0][0]
        
        VARNAME = self.WEATHER.VARNAME  # Meteorological variable names.
        nVAR = len(VARNAME)  # Number of meteorological variable.
        
        #-------------------------------------------- Target Station Header ----
        
        target_station_index = self.TARGET.index
        target_station_name = self.TARGET.name
        target_station_prov = self.WEATHER.PROVINCE[target_station_index]
        target_station_lat = self.WEATHER.LAT[target_station_index]
        target_station_lat = round(target_station_lat, 2)
        target_station_lon = self.WEATHER.LON[target_station_index]
        target_station_lon = round(target_station_lon, 2)
        target_station_alt = self.WEATHER.ALT[target_station_index]
        target_station_alt = round(target_station_alt, 2)
        target_station_clim = self.WEATHER.ClimateID[target_station_index]
        
        #-----------------------------------------------------------------------
        
        STANAME = np.copy(self.WEATHER.STANAME)
        CORCOEF = np.copy(self.TARGET.CORCOEF)
        
        HORDIST = np.copy(self.TARGET.HORDIST)
        ALTDIFF = np.copy(np.abs(self.TARGET.ALTDIFF))
        
        Nbr_Sta_max_user = self.parent.Nmax.value()
        limitDist = self.parent.distlimit.value()
        limitAlt = self.parent.altlimit.value()        
                
        # Save target data serie in a new 2D matrix that will be filled during
        # the data completion process
        Y2fill = np.copy(DATA[:, target_station_index, :])
        
        if self.full_error_analysis == True:
            YpFULL = np.copy(Y2fill) * np.nan
            print; print 'A full error analysis will be performed'; print
                
        self.ConsoleSignal.emit('<font color=black>Data completion for ' +
                                'station ' + target_station_name +
                                ' started</font>')
        
        print 'Data completion for station', target_station_name, 'started'
        
        #-------------------------------------------- CHECK CUTOFF CRITERIA ----        
        
        # Remove neighboring stations that do not respect the distance
        # or altitude difference cutoffs.
        
        check_HORDIST = np.zeros(len(HORDIST)) == 0
        check_ALTDIFF = np.zeros(len(ALTDIFF)) == 0

        if limitDist > 0:
            check_HORDIST = HORDIST < limitDist
        if limitAlt > 0:
            check_ALTDIFF = ALTDIFF < limitAlt
            
        # If cutoff limits are set to a negative number, all stations are kept
        # regardless of their distance or altitude difference with the target
        # station.
        
        check_HORDIST_and_ALTDIFF = check_HORDIST * check_ALTDIFF
        index_HORDIST_and_ALTDIFF = np.where(
                                           check_HORDIST_and_ALTDIFF == True)[0]                                  
    
        STANAME = STANAME[index_HORDIST_and_ALTDIFF]
        DATA = DATA[:, index_HORDIST_and_ALTDIFF, :]
        CORCOEF = CORCOEF[:, index_HORDIST_and_ALTDIFF]
        
        # WARNING!!! : From here on, STANAME has changed. A new index must
        #              be determined.
        
        target_station_index = np.where(STANAME == self.TARGET.name)[0][0]
    
        #---------------------------- Identifies Variables With Enough Data ----
        
        # NOTE: When a station does not have enough data for a given variable,
        #       its correlation coefficient is set to nan in CORCOEF. If all
        #       the stations have a value of nan in the correlation table for
        #       a given variable, it means there is not enough data available
        #       overall to estimate and fill missing data for it.
        
        var2fill = np.sum(~np.isnan(CORCOEF[:, :]), axis=1)
        var2fill = np.where(var2fill > 1)[0]
        
        print; print 'Variatble index with enough data = ', var2fill
        
        for var in range(nVAR):
            if var not in var2fill:
            
                message = ('!Variable %d/%d won''t be filled because there ' +
                           'is not enough data!') % (var+1, nVAR)
                print message
        
        #-------------------------------------------------------- FILL LOOP ----

        FLAG_nan = False # If some missing data can't be completed because 
                         # all the neighboring stations are empty, a flag is
                         # raised and a comment is issued at the end of the 
                         # completion process.
        
        nbr_nan_total = np.isnan(Y2fill[index_start:index_end+1, var2fill])
        nbr_nan_total = np.sum(nbr_nan_total)

        if self.full_error_analysis == True:
            progress_total = np.size(Y2fill[:, var2fill])
        else:
            progress_total = nbr_nan_total
            
        fill_progress = 0
        
        # <progress_total> and <fill_progress> are used to display the task
        # progression on the UI progression bar.
        
        INFO_VAR = np.zeros(nbr_nan_total).astype('str')
        INFO_NSTA = np.zeros(nbr_nan_total).astype('float')
        INFO_RMSE = np.zeros(nbr_nan_total).astype('float')
        INFO_ROW = np.zeros(nbr_nan_total).astype('int')
        INFO_YEAR = np.zeros(nbr_nan_total).astype('int')
        INFO_MONTH = np.zeros(nbr_nan_total).astype('int')
        INFO_DAY =  np.zeros(nbr_nan_total).astype('int')
        INFO_YX = np.zeros((nbr_nan_total, len(STANAME))) * np.nan
        it_info = 0 # Number of missing data estimated iteration counter
        
        AVG_RMSE = np.zeros(nVAR).astype('float')
        AVG_NSTA = np.zeros(nVAR).astype('float')
        station_use_counter = np.zeros((nVAR, len(STANAME))).astype('int')
        
        for var in var2fill:
            
#            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#            if self.STOP == True:
#                self.ConsoleSignal.emit(                           
#                    '''<font color=red>Completion process for station %s 
#                         stopped.</font>''' % target_station_name)
#                break 
#            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            
            message = ('Data completion for variable %d/%d in progress'
                       ) % (var+1, nVAR)
            print message
            
            colm_memory = np.array([]) # Column sequence memory matrix
            RegCoeff_memory = [] # Regression coefficient memory matrix
            RMSE_memory = []
            
            # Sort station in descending correlation coefficient order.
            # Target station index should be pulled at index 0 since its
            # correlation with itself is 1.
            Sta_index = sort_stations_correlation_order(CORCOEF[var, :])
            
            # Data for this variable are stored in a 2D matrix where the raws
            # are the weather data of the current variable to fill for each
            # time frame and the columns are the weather station, arranged in
            # descending correlation order. Target station data serie should be
            # contained at j = 0.
            YX = np.copy(DATA[:, Sta_index, var])              
            
            # Find rows where data are missing between the date limits
            # that correspond to index_start and index_end
            row_nan = np.where(np.isnan(YX[:, 0]))[0]
            row_nan = row_nan[row_nan >= index_start]
            row_nan = row_nan[row_nan <= index_end]
            it_avg = 0 # counter used in the calculation of average RMSE
                       # and NSTA values.
            
            if self.full_error_analysis == True :
                row2fill = range(len(Y2fill[:, 0])) # All the data of the time 
                                                    # series will be estimated 
            else:
                row2fill = row_nan
                
                                               
            for row in row2fill:
                
                sleep(0.000001) #If no sleep, the UI becomes whacked
                
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                
                if self.STOP == True:
                    
                    print 'BREAK!!!!'
                    self.ConsoleSignal.emit(                           
                    '''<font color=red>Completion process for station %s 
                         stopped.</font>''' % target_station_name)
                    
                    self.STOP = False
                    
                    return
                    
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                  
                # Find neighboring stations with valid entries at 
                # row <row> in <YX>. Target station is stored at index 0.
                colm = np.where(~np.isnan(YX[row, 1:]))[0]                    
                
                if np.size(colm) == 0:
                    
                # Impossible to fill variable because all neighboring 
                # stations are empty.
                    
                    if self.full_error_analysis == True:
                        YpFULL[row, var] = np.nan
                    
                    if row in row_nan:
                        Y2fill[row, var] = np.nan
                        
                        FLAG_nan = True # A warning comment will be issued at
                                        # the end of the completion process.
                        
                        INFO_VAR[it_info] = VARNAME[var]
                        INFO_NSTA[it_info] = np.nan
                        INFO_RMSE[it_info] = np.nan
                        INFO_ROW[it_info] = int(row)
                        INFO_YEAR[it_info] = str(int(YEAR[row]))
                        INFO_MONTH[it_info] = str(int(MONTH[row]))
                        INFO_DAY[it_info] =  DAY[row]
                        INFO_YX[it_info, :] = np.nan  
                        
                        it_info += 1
                else:
                    
                # Neighboring stations are not empty, continue with the
                # missing data estimation procedure for this row.
                
                    # Number of station to include in the regression model.
                    NSTA = min(len(colm), Nbr_Sta_max_user)
                    
                    # Remove superflux station from <colm>.
                    colm = colm[:NSTA]
                    
                    # Add an index 0 at index 0 to include the target
                    # station and correct index of the neighboring stations
                    colm = colm + 1
                    colm = np.insert(colm, 0, 0)
                    
                    # Store values of the independent variables 
                    # (neighboring stations) for this row in a new array.
                    # An intercept term is added if Var is temperature type
                    # variable, but not if it is precipitation type.
                    if var in (0, 1, 2):
                        X_row = np.hstack((1, YX[row, colm[1:]]))
                    else:
                        X_row = YX[row, colm[1:]]
                    
                    # Elements of the <colm> array are put back to back
                    # in a single string. For example, a [2, 7, 11] array
                    # would end up as '020711'. This allow to assign a
                    # unique number ID to a column combination. Each
                    # column correspond to a unique weather station.
                    
                    colm_seq = ''
                    for i in range(len(colm)):
                        colm_seq += '%02d' % colm[i]
                    
                    # A check is made to see if the current combination
                    # of neighboring stations has been encountered
                    # previously in the routine. Regression coefficients
                    # are calculated only once for a given neighboring
                    # station combination.
                    index_memory = np.where(colm_memory == colm_seq)[0]                                   
                    
                    if len(index_memory) == 0:
                        
                    # First time this neighboring station combination
                    # is encountered in the routine, regression
                    # coefficients are then calculated.
                    
                        # The memory is activated only if the option
                        # 'full_error_analysis' is not active. Otherwise, the
                        # memory remains empty and a new MLR model is built
                        # for each value of the data series.
                        if self.full_error_analysis != True: 
                            colm_memory = np.append(colm_memory, colm_seq)
                    
                        # Columns of DATA for the variable VAR are sorted
                        # in descending correlation coefficient and the 
                        # information is stored in a 2D matrix (The data for 
                        # the target station are included at index j=0).
                        YXcolm = np.copy(YX)       
                        YXcolm = YXcolm[:, colm]
                        
                        # Force the value of the target station to a NAN value
                        # for this row. This should only have an impact when the
                        # option "full_error_analysis" is activated. This is to
                        # actually remove the data being estimated from the
                        # dataset like in should properly be done in the 
                        # jackknife procedure.
                        YXcolm[row, 0] = np.nan
                        
                        # All rows containing NAN entries are removed.
                        YXcolm = YXcolm[~np.isnan(YXcolm).any(axis=1)]
                    
                        # Rows for which precipitation of the target station
                        # and all neighboring station is 0 are removed. Only
                        # applicable for precipitation, not air temperature.
                        if var == 3:                        
                            YXcolm = YXcolm[~(YXcolm == 0).all(axis=1)]  
                                            
                        Y = YXcolm[:, 0]  # Dependant variable (target)                     
                        X = YXcolm[:, 1:] # Independant variables (neighbors)
                
                        # Add a unitary array to X for the intercept term if
                        # variable is a temperature type data.
                        if var in (0, 1, 2):
                            X = np.hstack((np.ones((len(Y), 1)), X))
                        else:
                            'Do not add an intercept term'
                    
                        if self.regression_mode == True:
                            # Ordinary Least Square regression
                            A = linalg_lstsq(X, Y)[0]
                        else:
                            # Least Absolute Deviations regression
                            A = L1LinearRegression(X, Y)
                            
                            # This section of the code is if I decide at
                            # some point to use this package instead of
                            # my own custom function.
                            
                            #model = sm.OLS(Y, X) 
                            #results = model.fit()
                            #print results.params
                            
                            #model = QuantReg(Y, X)
                            #results = model.fit(q=0.5)
                            #A = results.params
                            
                        #--------------------------------------------- RMSE ----
                        
                        # Calculate a RMSE between the estimated and
                        # measured values of the target station.
                        # RMSE with 0 value are not accounted for
                        # in the calcultation.                        
                        
                        Yp = np.dot(A, X.transpose())
                        
                        RMSE = (Y - Yp)**2          # MAE = np.abs(Y - Yp)
                        RMSE = RMSE[RMSE != 0]      # MAE = MAE[MAE!=0]
                        RMSE = np.mean(RMSE)**0.5   # MAE = np.mean(MAE)
                        
                        RegCoeff_memory.append(A)
                        RMSE_memory.append(RMSE)
                    
                    else:
                        
                    # Regression coefficients and RSME are recalled
                    # from the memory matrices.

                        A = RegCoeff_memory[index_memory]
                        RMSE = RMSE_memory[index_memory]
                                            
                    #----------------------------- MISSING VALUE ESTIMATION ----
                    
                    # Calculate missing value of Y at row <row>.
                    Y_row = np.dot(A, X_row)
                    
                    # Limit precipitation based variable to positive values.
                    # This may happens when there is one or more negative 
                    # regression coefficients in A
                    if var in (3, 4, 5):
                        Y_row = max(Y_row, 0)
                        
                    # Round the results.
                    Y_row = round(Y_row ,1)
                    
                    #---------------------------------------- STORE RESULTS ----
                  
                    if self.full_error_analysis == True:
                        YpFULL[row, var] = Y_row
                        
                    if row in row_nan:
                        Y2fill[row, var] = Y_row
                        
                        INFO_VAR[it_info] = VARNAME[var]
                        INFO_NSTA[it_info] = NSTA
                        INFO_RMSE[it_info] = RMSE
                        INFO_ROW[it_info] = int(row)
                        INFO_YEAR[it_info] = str(int(YEAR[row]))
                        INFO_MONTH[it_info] = str(int(MONTH[row]))
                        INFO_DAY[it_info] =  DAY[row]
                        
                        AVG_RMSE[var] += RMSE
                        AVG_NSTA[var] += NSTA
                        it_avg += 1
                        
                        Sta_index_row = Sta_index[colm]
                        if var in (0, 1, 2):                    
                            INFO_YX[it_info, Sta_index_row[0]] = Y_row
                            INFO_YX[it_info, Sta_index_row[1:]] = X_row[1:]
                        else:
                            INFO_YX[it_info, Sta_index_row[0]] = Y_row
                            INFO_YX[it_info, Sta_index_row[1:]] = X_row
                        
                        it_info += 1 # Total number of missing data counter    
                        
                        INFO_BOOLEAN = np.zeros(len(STANAME))
                        INFO_BOOLEAN[Sta_index_row] = 1
                        station_use_counter[var, :] += INFO_BOOLEAN
                    
                fill_progress += 1.
                self.ProgBarSignal.emit(fill_progress/progress_total * 100)
                
            #----------------- Calculate Estimation Error for this variable ----
            
            if it_avg > 0:
                AVG_RMSE[var] /= it_avg
                AVG_NSTA[var] /= it_avg
            else:
                AVG_RMSE[var] = np.nan
                AVG_NSTA[var] = np.nan
                
            print_message = ('Data completion for variable %d/%d completed'
                             ) % (var+1, nVAR)
            print print_message             

    #=================================================== WRITE DATA TO FILE ====
                    
        self.ConsoleSignal.emit('<font color=black>Data completion ' + 
                                'for station ' + target_station_name +
                                ' completed</font>')
                                
        if FLAG_nan == True:
            self.ConsoleSignal.emit(
                '<font color=red>WARNING: Some missing data were not ' +
                'completed because all neighboring station were empty ' +
                'for that period</font>')
    
        #----------------------------------------- INFO DATA POSTPROCESSING ----
        
        # Put target station name and information to the begining of the
        # STANANE array and INFO matrix.
        INFO_Yname = STANAME[target_station_index]
        INFO_Y = INFO_YX[:, target_station_index].astype('str')
                    
        INFO_Xname = np.delete(STANAME, target_station_index)
        INFO_X = np.delete(INFO_YX, target_station_index, axis=1)
        
        station_use_counter = np.delete(station_use_counter,
                                        target_station_index, axis=1)

        # Check for neighboring stations that were used for filling data
        station_use_counter_total = np.sum(station_use_counter, axis=0)
        index = np.where(station_use_counter_total > 0)[0]
        
        # Keep only stations that were used for filling data
        INFO_Xname = INFO_Xname[index]
        INFO_X = INFO_X[:, index]
        station_use_counter_total = station_use_counter_total[index]
        station_use_counter = station_use_counter[:, index]
        
        # Sort neighboring stations by importance
        index = np.argsort(station_use_counter_total * -1)
        
        INFO_Xname = INFO_Xname[index]
        INFO_X = INFO_X[:, index]
        
        station_use_counter_total = station_use_counter_total[index]
        station_use_counter = station_use_counter[:, index]
        
        # Replace nan values by ''
        INFO_X = INFO_X.astype('str')
        INFO_X[INFO_X == 'nan'] = ''
       
        #------------------------------------------------------- HEADER ----
              
        HEADER = [['Station Name', target_station_name]]
        HEADER.append(['Province', target_station_prov])
        HEADER.append(['Latitude', target_station_lat])
        HEADER.append(['Longitude', target_station_lon])
        HEADER.append(['Elevation', target_station_alt])
        HEADER.append(['Climate Identifier', target_station_clim])
        HEADER.append([])
        HEADER.append(['Created by', software_version])
        HEADER.append(['Created on', strftime("%d/%m/%Y")])
        HEADER.append([])
        
        #----------------------------------------------- LOG GENERATION ----
        
        record_date_start = '%04d/%02d/%02d' % (YEAR[index_start],
                                                MONTH[index_start],
                                                DAY[index_start]) 
                                            
        record_date_end = '%04d/%02d/%02d' % (YEAR[index_end],
                                              MONTH[index_end],
                                              DAY[index_end])
        
        INFO_total = copy(HEADER)
        
        INFO_total.append(['*** FILL PROCEDURE INFO ***'])
        
        INFO_total.append([])
        if self.regression_mode == True:
            INFO_total.append(['MLR model', 'Ordinary Least Square'])
        elif self.regression_mode == False:
            INFO_total.append(['MLR model', 'Least Absolute Deviations'])
        INFO_total.append(['Precip correction', 'Not Available'])
        INFO_total.append(['Wet days correction', 'Not Available'])
        INFO_total.append(['Max number of stations', str(Nbr_Sta_max_user)])
        INFO_total.append(['Cutoff distance (km)', str(limitDist)])
        INFO_total.append(['Cutoff altitude difference (m)', str(limitAlt)])
        INFO_total.append(['Date Start', record_date_start])
        INFO_total.append(['Date End', record_date_end])
        INFO_total.append([])
        INFO_total.append([])
                    
        INFO_total.append(['*** SUMMARY TABLE ***'])
        
        INFO_total.append([])
        INFO_total.append(['CLIMATE VARIABLE', 'TOTAL MISSING',
                           'TOTAL FILLED', '', 'AVG. NBR STA.',
                           'AVG. RMSE', ''])
        INFO_total[-1].extend(INFO_Xname)
        
        total_nbr_data = index_end - index_start + 1
        nbr_fill_total = 0
        nbr_nan_total = 0
        for var in range(nVAR):
            
            nbr_nan = np.isnan(DATA[index_start:index_end+1,
                                    target_station_index, var])
            nbr_nan = float(np.sum(nbr_nan))
            
            nbr_nan_total += nbr_nan
            
            nbr_nofill = np.isnan(Y2fill[index_start:index_end+1, var])
            nbr_nofill = np.sum(nbr_nofill)
            
            nbr_fill = nbr_nan - nbr_nofill
            
            nbr_fill_total += nbr_fill
            
            nan_percent = round(nbr_nan / total_nbr_data * 100, 1)
            if nbr_nan != 0:
                nofill_percent = round(nbr_nofill / nbr_nan * 100, 1)
                fill_percent = round(nbr_fill / nbr_nan * 100, 1)
            else:
                nofill_percent = 0
                fill_percent = 100
            
            nbr_nan = '%d (%0.1f %% of total)' % (nbr_nan, nan_percent)
 
            nbr_nofill = '%d (%0.1f %% of missing)' % (nbr_nofill,
                                                       nofill_percent)

            nbr_fill_txt = '%d (%0.1f %% of missing)' % (nbr_fill,
                                                         fill_percent)
       
            INFO_total.append([VARNAME[var], nbr_nan, nbr_fill_txt, '',
                               '%0.1f' % AVG_NSTA[var],
                               '%0.2f' % AVG_RMSE[var], ''])

            for i in range(len(station_use_counter[0, :])):
                percentage = round(
                            station_use_counter[var, i] / nbr_fill * 100, 1)
                           
                INFO_total[-1].extend([
                '%d (%0.1f %% of filled)' % (station_use_counter[var, i],
                                             percentage)])

        nbr_fill_percent = round(nbr_fill_total / nbr_nan_total * 100, 1)
        nbr_fill_total_txt = '%d (%0.1f %% of missing)' % \
                                          (nbr_fill_total, nbr_fill_percent)
        
        nan_total_percent = round(
                           nbr_nan_total / (total_nbr_data * nVAR) * 100, 1)
        nbr_nan_total = '%d (%0.1f %% of total)' % (nbr_nan_total,
                                                    nan_total_percent)
        INFO_total.append([])
        INFO_total.append(['TOTAL', nbr_nan_total, nbr_fill_total_txt, 
                          '', '---', '---', ''])
        for i in range(len(station_use_counter_total)):
                percentage = round(
                     station_use_counter_total[i] / nbr_fill_total * 100, 1)
                text2add = '%d (%0.1f %% of filled)' \
                                % (station_use_counter_total[i], percentage)
                INFO_total[-1].extend([text2add])            
        INFO_total.append([])
        INFO_total.append([])
        
        INFO_total.append(['*** DETAILED REPORT ***'])
        
        INFO_total.append([])
        INFO_total.append(['VARIABLE', 'YEAR', 'MONTH', 'DAY',
                           'NBR STA.','RMSE'])
        INFO_total[-1].extend([INFO_Yname])
        INFO_total[-1].extend(INFO_Xname)
        INFO_ROW = INFO_ROW.tolist()
        INFO_RMSE = np.round(INFO_RMSE, 2).astype('str')
        for i in range(len(INFO_Y)):
            info_row_builder = [INFO_VAR[i], INFO_YEAR[i], INFO_MONTH[i],
                                '%d' % INFO_DAY[i], '%0.0f' % INFO_NSTA[i],
                                INFO_RMSE[i], INFO_Y[i]]
            info_row_builder.extend(INFO_X[i])
            
            INFO_total.append(info_row_builder)
                
        #---------------------------------------------------- SAVE INFO ----
                                  
        YearStart = str(int(YEAR[index_start])) 
        YearEnd = str(int(YEAR[index_end]))
        
        # Check if the characters "/" or "\" are present in the station 
        # name and replace these characters by "-" if applicable.
        intab = "/\\"
        outtab = "--"
        trantab = maketrans(intab, outtab)
        target_station_name = target_station_name.translate(trantab)
        
        output_path = (self.project_dir + '/Meteo/Output/' + 
                       target_station_name + ' (' + target_station_clim +
                       ')'+ '_' + YearStart + '-' +  YearEnd + '.log')
        
        with open(output_path, 'wb') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(INFO_total)
        
        self.ConsoleSignal.emit(
            '<font color=black>Info file saved in ' + output_path +
            '</font>')
            
        #---------------------------------------------------- SAVE DATA ----
        
        DATA2SAVE = copy(HEADER)
        DATA2SAVE.append(['Year', 'Month', 'Day'])
        DATA2SAVE[-1].extend(VARNAME)
               
        ALLDATA = np.vstack((YEAR[index_start:index_end+1],
                             MONTH[index_start:index_end+1],
                             DAY[index_start:index_end+1], 
                             Y2fill[index_start:index_end+1].transpose())
                             ).transpose()
        ALLDATA.tolist() 
        for i in range(len(ALLDATA)):
            DATA2SAVE.append(ALLDATA[i])
        
        output_path = (self.project_dir + '/Meteo/Output/' + 
                       target_station_name + ' (' + target_station_clim +
                       ')'+ '_' + YearStart + '-' +  YearEnd + '.out')
        
        with open(output_path, 'wb') as f:
            writer = csv.writer(f,delimiter='\t')
            writer.writerows(DATA2SAVE)
        
        self.ConsoleSignal.emit('<font color=black>Meteo data saved in ' +
                                output_path + '</font>')
        self.ProgBarSignal.emit(0)
        
        print; print '!Data completion completed successfully!'; print 
        
        self.EndProcess.emit(1)
        self.STOP = False # Just in case. This is a precaution override.
        
        #----------------------------------- SAVE ERROR ANALYSIS REPORT ----
        
        if self.full_error_analysis == True:
            
            error_analysis_report = copy(HEADER)
            error_analysis_report.append(['Year', 'Month', 'Day'])
            error_analysis_report[-1].extend(VARNAME)
            
            ALLDATA = np.vstack((YEAR, MONTH, DAY, YpFULL.transpose()))
            ALLDATA = ALLDATA.transpose()                 
            ALLDATA.tolist() 
            for i in range(len(ALLDATA)):
                error_analysis_report.append(ALLDATA[i])
            
            output_path = (self.project_dir + '/Meteo/Output/' + 
                       target_station_name + ' (' + target_station_clim +
                       ')'+ '_' + YearStart + '-' +  YearEnd + '.err')
                           
            with open(output_path, 'wb') as f:
                writer = csv.writer(f,delimiter='\t')
                writer.writerows(error_analysis_report)
        
            #---------------------------------------- SOME CALCULATIONS ----
            
            RMSE = np.zeros(nVAR)
            ERRMAX  = np.zeros(nVAR)
            ERRSUM = np.zeros(nVAR)
            for i in range(nVAR):
                errors = YpFULL[:, i] - Y2fill[:, i]
                
                rmse = errors**2 
                rmse = rmse[rmse != 0]                  
                rmse = np.mean(rmse)**0.5
                
                errmax = np.abs(errors)
                errmax = np.max(errmax)
                
                errsum = np.sum(errors)
                
                
                RMSE[i] = rmse
                ERRMAX[i] = errmax
                ERRSUM[i] = errsum
            
            print RMSE
            print ERRMAX
            print ERRSUM
            
            DIFF = np.abs(YpFULL- Y2fill)
            index = np.where(DIFF[:, -1] == ERRMAX[-1])
            print YEAR[index], MONTH[index], DAY[index]
            
        
            # MAE = np.abs(Y - Yp)
            # MAE = MAE[MAE!=0]
            # MAE = np.mean(MAE)

#===============================================================================
def sort_stations_correlation_order(CORCOEF):
#===============================================================================
        
    # An index is associated with each value of the CORCOEF array.
    Sta_index = range(len(CORCOEF))    
    CORCOEF = np.vstack((Sta_index, CORCOEF)).transpose()
    
    # Stations for which the correlation coefficient is nan are removed.
    CORCOEF = CORCOEF[~np.isnan(CORCOEF).any(axis=1)] 
               
    # The station indexes are sorted in descending order of their
    # correlation coefficient.
    CORCOEF = CORCOEF[np.flipud(np.argsort(CORCOEF[:, 1])), :]
    
    Sta_index = np.copy(CORCOEF[:, 0].astype('int'))
    
    # Note : The target station will be pushed to the first value of
    #        the array because it has a value of 1.

    return Sta_index 

#===============================================================================    
def L1LinearRegression(X, Y): 
    """
    L1LinearRegression: Calculates L-1 multiple linear regression by IRLS
    (Iterative reweighted least squares)

    B = L1LinearRegression(Y,X)

    B = discovered linear coefficients 
    X = independent variables 
    Y = dependent variable 

    Note 1: An intercept term is NOT assumed (need to append a unit column if
            needed). 
    Note 2: a.k.a. LAD, LAE, LAR, LAV, least absolute, etc. regression 

    SOURCE:
    This function is originally from a Matlab code written by Will Dwinnell
    www.matlabdatamining.blogspot.ca/2007/10/l-1-linear-regression.html
    Last accessed on 21/07/2014
    """
#===============================================================================
 
    # Determine size of predictor data.
    n, m = np.shape(X)
    
    # Initialize with least-squares fit.
    B = linalg_lstsq(X, Y)[0]                               
    BOld = np.copy(B) 
    
    # Force divergence.
    BOld[0] += 1e-5

    # Repeat until convergence.
    while np.max(np.abs(B - BOld)) > 1e-6:
         
        BOld = np.copy(B)
        
        # Calculate new observation weights based on residuals from old 
        # coefficients. 
        weight =  np.dot(B, X.transpose()) - Y
        weight =  np.abs(weight)
        weight[weight < 1e-6] = 1e-6 # to avoid division by zero
        weight = weight**-0.5
        
        # Calculate new coefficients.
        Xb = np.tile(weight, (m, 1)).transpose() * X      
        Yb = weight * Y
        
        B = linalg_lstsq(Xb, Yb)[0]
        
    return B


#===============================================================================    
class WHATPref():
    """
    This class contains all the preferences relative to the WHAT interface,
    including:
    
    projectfile: It is a memory variable. It indicates upon launch to the 
                 program what was the project that was opened when last time the
                 program was closed.
                
    language: Language in which the GUI is displayed (not the labels of graphs).
    
    full_error_analysis: Option that enable when equal to 1 the error analysis
                         of the missing weather data routine. This option is
                         experimental, that is why it has not been added to the
                         UI yet.
    """
#===============================================================================

    
    def __init__(self, parent=None):
     
        if platform.system() == 'Windows':
            self.projectfile = '..\Projects\Example\Example.what'
        elif platform.system() == 'Linux':
            self.projectfile = '../Projects/Example/Example.what'
            
        self.language = 'English'
        
        self.full_error_analysis = 0
    
    #---------------------------------------------------------------------------
    def save_pref_file(self):
    #---------------------------------------------------------------------------
        
        projectfile = path.relpath(self.projectfile).encode('utf-8')
        
        fcontent = [['Project File:', projectfile],
                    ['Language:', self.language],
                    ['Full Error Analysis:', self.full_error_analysis]]
       
        with open('WHAT.pref', 'wb') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(fcontent)
    
    #---------------------------------------------------------------------------       
    def load_pref_file(self):
    #---------------------------------------------------------------------------
        
        if not path.exists('WHAT.pref'):
            
            # Default values will be kept and a new .pref file will be
            # generated
            
            print 'No "WHAT.pref" file found. A new one has been created.'
        
            self.save_pref_file()
        
        else:
            
            reader = open('WHAT.pref', 'rb')
            reader = csv.reader(reader, delimiter='\t')
            reader = list(reader)
            
            self.projectfile = reader[0][1].decode('utf-8')
            self.language = reader[1][1]
            
            try:
                self.full_error_analysis = int(reader[2][1])
            except:
                self.full_error_analysis = 0
            
            print 'self.full_error_analysis =', self.full_error_analysis
            print

#===============================================================================                
class MyProject():
    """
    This class contains all the info and utilities to manage the current active
    project.
    """
#===============================================================================

    
    def __init__(self, parent=None):
        
        self.name = ''
        self.lat = 0
        self.lon = 0
        
    #---------------------------------------------------------------------------
    def load_project_info(self, projectfile):
    #---------------------------------------------------------------------------
        
        print 'Loading project info'
        
        reader = open(projectfile, 'rb')
        reader = csv.reader(reader, delimiter='\t')
        reader = list(reader)
            
        self.name = reader[0][1].decode('utf-8')
        self.lat = float(reader[6][1])
        self.lon = float(reader[7][1])
        
       
################################################################################
#                                                                           
#                              MAIN FUNCTION
#                                                                          
################################################################################       

        
if __name__ == '__main__':
    
    app = QtGui.QApplication(argv)
    instance_1 = MainWindow()
#    instance_1.show()
    app.exec_()
        
    


    
    
    
    
    
