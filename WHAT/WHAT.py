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

# It is often said when developing interfaces that you need to fail fast,
# and iterate often. When creating a UI, you will make mistakes. Just keep
# moving forward, and remember to keep your UI out of the way.

# http://blog.teamtreehouse.com/10-user-interface-design-fundamentals

#---- STANDARD LIBRARY IMPORTS ----

import platform
import csv
#from urllib import urlretrieve
import sys
from time import ctime
from os import listdir, makedirs, path

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui, QtCore
from PySide.QtCore import QDate

import numpy as np
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
import MyQWidget
import what_project

import hydroprint2 as hydroprint
import imageviewer2 as imageviewer

import meteo
import waterlvl_calc

import dwnld_weather_data
import fill_weather_data

from about_WHAT import AboutWhat

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
        
    def initUI(self): #=========================================================
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
        
        #-------------------------------------------------- CLASS INSTANCES ----
        
        self.projectInfo = MyProject(self)
        self.whatPref = WHATPref(self)
        self.new_project_window = what_project.NewProject(db.software_version)
#        self.open_project_window = what_project.OpenProject()
        
        #------------------------------------------------------ PREFERENCES ----
                
        self.whatPref.load_pref_file()
        
        language = self.whatPref.language
        
        self.projectfile = self.whatPref.projectfile
        self.projectdir = path.dirname(self.projectfile)
        
        style = 'Regular'
        size = self.whatPref.fontsize_general
        
        family = db.styleUI().fontfamily
        
        fontSS = ( "font-style: %s;" % style +
                    "font-size: %s;"  % size  +
                    "font-family: %s;" % family)
                    
        self.setStyleSheet("QWidget{%s}" % fontSS)
                                    
        #-------------------------------------------------------- DATABASES ----
        
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
        
        #---------------------------------------------- MAIN WINDOW SETUP ----

#        self.setMinimumWidth(1250)
        self.setWindowTitle(db.software_version)
        self.setWindowIcon(iconDB.WHAT)
#        self.setFont(styleDB.font1)                
                        
        #--------------------------------------------------- MAIN CONSOLE ----
        
        self.main_console = QtGui.QTextEdit()        
        self.main_console.setReadOnly(True)
        self.main_console.setLineWrapMode(QtGui.QTextEdit.LineWrapMode.NoWrap)
#        self.main_console.setFont(styleDB.font_console)
        
        size = self.whatPref.fontsize_console
        fontSS = ( "font-style: %s;" % style +
                    "font-size: %s;"  % size  +
                    "font-family: %s;" % family)
        self.main_console.setStyleSheet("QWidget{%s}" % fontSS)
        
        self.write2console('''<font color=black>Thanks for using %s.
        </font>''' % db.software_version)
        self.write2console(
        '''<font color=black>Please report any bug or wishful feature to 
             Jean-S&eacute;bastien Gosselin at jnsebgosselin@gmail.com.
           </font>''')
           
        #----------------------------------------------- PROJECT MENU BAR ----
                        
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
        subgrid_menubar.setContentsMargins(0, 0, 0, 5) # [L, T, R, B] 
        subgrid_menubar.setColumnStretch(1, 500)
        subgrid_menubar.setRowMinimumHeight(0, 28)
        
        self.menubar_widget.setLayout(subgrid_menubar)
        
        size = self.whatPref.fontsize_menubar
        fontSS = ( "font-style: %s;" % style +
                    "font-size: %s;"  % size  +
                    "font-family: %s;" % family)
        self.menubar_widget.setStyleSheet("QWidget{%s}" % fontSS)
        
        #----------------------------------------------------- TAB WIDGET ----
           
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
        
        #---- download weather data ----
        
        self.tab_dwnld_data = dwnld_weather_data.dwnldWeather(self)
        self.tab_dwnld_data.set_workdir(self.projectdir)
        
        #---- gapfill weather data ----
        
        self.tab_fill_weather_data = fill_weather_data.GapFillWeather(self)
        self.tab_fill_weather_data.set_workdir(self.projectdir)
        
        #---- hydrograph ----
                
        self.tab_hydrograph = TabHydrograph(self)
        
        #---- about ----
        
        tab_about = AboutWhat(self)
        
        #---- TABS ASSEMBLY ----
        
        Tab_widget.addTab(self.tab_dwnld_data, labelDB.TAB1)        
        Tab_widget.addTab(self.tab_fill_weather_data, labelDB.TAB2) 
        Tab_widget.addTab(self.tab_hydrograph, labelDB.TAB3) 
        Tab_widget.addTab(tab_about, labelDB.TAB4)
        
        Tab_widget.setCornerWidget(self.menubar_widget)
        
        #------------------------------------------------ SPLITTER WIDGET ----
                
        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Vertical)
        
        splitter.addWidget(Tab_widget)
        splitter.addWidget(self.main_console)
        
        splitter.setCollapsible(0, True)
        splitter.setStretchFactor(0, 100)                
        splitter.setSizes([100, 1]) # Forces initially the main_console to its
                                    # minimal height.       
       
        #------------------------------------------------------ MAIN GRID ----
        
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
        
        #--------------------------------------------------------- EVENTS ----
        
        self.btn_new_project.clicked.connect(self.show_new_project)
        self.project_display.clicked.connect(self.open_project)
        self.new_project_window.NewProjectSignal.connect(self.load_project)
#        self.open_project_window.OpenProjectSignal.connect(self.load_project) 

        #---- Console Signal Piping ----
        
        issuer = self.tab_dwnld_data
        issuer.ConsoleSignal.connect(self.write2console)  

        issuer = self.tab_dwnld_data.search4stations
        issuer.ConsoleSignal.connect(self.write2console)

        issuer =  self.tab_dwnld_data.dwnl_raw_datafiles 
        issuer.ConsoleSignal.connect(self.write2console)  

        issuer = self.tab_fill_weather_data
        issuer.ConsoleSignal.connect(self.write2console)

        issuer = self.tab_fill_weather_data.fillworker
        issuer.ConsoleSignal.connect(self.write2console)                                                
        
        #-------------------------------------------------- MESSAGE BOXES ----
       
        self.msgError = MyQWidget.MyQErrorMessageBox()
                   
        #----------------------------------------------------------- SHOW ----
            
        self.show()
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        #----------------------------------------------- CHECK IF PROJECT ----
        
        isProjectExists = self.check_project()
        
        if isProjectExists:

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
                
      
    def write2console(self, console_text): #==================================
        
        '''
        This function is the bottle neck through which all messages writen
        in the console must go through.
        '''
            
        textime = '<font color=black>[' + ctime()[4:-8] + '] </font>'
                        
        self.main_console.append(textime + console_text)
    
        
    def show_new_project(self): #=============================================
    
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
            
    
    def open_project(self): #=================================================
        
        '''
        "open_project" is called by the event "self.project_display.clicked".
        It allows the user to open an already existing project.
        '''
        
#        qr = self.open_project_window.frameGeometry()
#        cp = self.frameGeometry().center()
#        qr.moveCenter(cp)
#        self.open_project_window.move(qr.topLeft())
#        
#        self.open_project_window.setModal(True)
#        self.open_project_window.show()
#        self.open_project_window.setFixedSize(self.open_project_window.size())
        
        #----------------------------------------- Custom File Dialog (1) ----
        
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
            
    #-------------------------------------------------------------------------
    def load_project(self, filename):
        '''
        This method is called either on startup during <initUI> or when a new
        project is chosen with <open_project>.        
        '''
    #-------------------------------------------------------------------------
        
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
        self.tab_fill_weather_data.setEnabled(True)     
        self.tab_hydrograph.setEnabled(True)
        
        self.project_display.setText(self.projectInfo.name)
        self.project_display.adjustSize()
            
        #---- Load Weather Input Files ----
        
        self.tab_fill_weather_data.load_data_dir_content()
        
        # ----- RESET UI Memory Variables -----
        
        self.tab_hydrograph.meteo_dir = self.projectdir + '/Meteo/Output'
        self.tab_hydrograph.waterlvl_dir = self.projectdir + '/Water Levels'
        self.tab_hydrograph.save_fig_dir = self.projectdir
        
        #--------------------------------------------- Update child widgets ----
        
        #---- dwnld_weather_data ----
        
        self.tab_dwnld_data.set_workdir(self.projectdir)
        self.tab_dwnld_data.search4stations.lat_spinBox.setValue(
                                                           self.projectInfo.lat)
                                                           
        self.tab_dwnld_data.search4stations.lon_spinBox.setValue(
                                                           self.projectInfo.lon)
                                                           
        #---- fill_weather_data ----
                                                           
        self.tab_fill_weather_data.set_workdir(self.projectdir)
        
        #---- hydrograph ----
        
        self.tab_hydrograph.weather_avg_graph.save_fig_dir = self.projectdir
        
        print('')
        print('---- PROJECT LOADED ----')
        print('')
      
    #-------------------------------------------------------------------------
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
    #-------------------------------------------------------------------------
        
        print('Checking project files and folders integrity')
        
        print(self.projectfile)
        if not path.exists(self.projectfile):
            print('Project file does not exist.')
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
            print(msg)
            
            # http://stackoverflow.com/questions/13437727
            book = xlwt.Workbook(encoding="utf-8")
            sheet1 = book.add_sheet("Sheet 1")
            sheet1.write(0, 0, 'Well_ID')
            sheet1.write(0, 1, 'Time (days)')
            sheet1.write(0, 2, 'Obs. (mbgs)')
            book.save(fname)
        
        #---- graph_layout.lst ----
        
        filename = self.projectdir + '/graph_layout.lst'
        if not path.exists(filename):
            
            fcontent = headerDB.graph_layout
                        
            msg = ('No "graph_layout.lst" file found. ' +
                   'A new one has been created.')
            print(msg)

            with open(filename, 'wb') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(fcontent)
                
        return True
    
    def closeEvent(self,event): 
        event.accept()
        
#=============================================================================
        
class PageSetupWin(QtGui.QWidget):                             # PageSetupWin #

#=============================================================================
            
            newPageSetupSent = QtCore.Signal(bool)
            
            def __init__(self, parent=None):
                super(PageSetupWin, self).__init__(parent)
                
                self.setWindowTitle('Page Setup')
                self.setWindowFlags(QtCore.Qt.Window)
                
                #---- Default Values ----
                
                self.pageSize = (11., 8.5)
                
                #---- Toolbar ----
                
                toolbar_widget = QtGui.QWidget()
                
                btn_apply = QtGui.QPushButton('Apply')
                btn_apply.clicked.connect(self.btn_apply_isClicked)
                btn_cancel = QtGui.QPushButton('Cancel')
                btn_cancel.clicked.connect(self.close)
                
                toolbar_layout = QtGui.QGridLayout()
                toolbar_layout.addWidget(btn_apply, 0, 0)
                toolbar_layout.addWidget(btn_cancel, 0, 1)
                
                toolbar_widget.setLayout(toolbar_layout)
                
                #---- Figure Size ----
                
                figSize_widget =  QtGui.QWidget()
                
                self.fwidth = QtGui.QDoubleSpinBox()
                self.fwidth.setSingleStep(0.05)
                self.fwidth.setMinimum(5.)
                self.fwidth.setValue(self.pageSize[0])
                self.fwidth.setSuffix('  in')
                self.fwidth.setAlignment(QtCore.Qt.AlignCenter)
                
                figSize_layout = QtGui.QGridLayout()
                figSize_layout.addWidget(QtGui.QLabel('Figure Size:'), 0, 0)
                figSize_layout.addWidget(self.fwidth, 0, 1)                
                figSize_layout.addWidget(QtGui.QLabel('x'), 0, 2)
                figSize_layout.addWidget(QtGui.QLabel('8.5 in'), 0, 3)
                
                figSize_widget.setLayout(figSize_layout)
                
                #---- Main Layout ----
                
                main_layout = QtGui.QGridLayout()
                main_layout.addWidget(figSize_widget, 0, 0)
                main_layout.addWidget(toolbar_widget, 1, 0)
                
                self.setLayout(main_layout)
                
            def btn_apply_isClicked(self): #==================================
                
                self.pageSize = (self.fwidth.value(), 8.5)                
                self.newPageSetupSent.emit(True)
            
            def closeEvent(self, event): #====================================
                super(PageSetupWin, self).closeEvent(event)

                #---- Refresh UI ----
                
                # If cancel or X is clicked, the parameters will be reset to
                # the values they had the last time "Accept" button was
                # clicked.
                
                self.fwidth.setValue(self.pageSize[0])
                
            def show(self): #=================================================
                super(PageSetupWin, self).show()
                self.activateWindow()
                self.raise_()
                
                qr = self.frameGeometry()
                if self.parentWidget():
                    parent = self.parentWidget()
                    
                    wp = parent.frameGeometry().width()
                    hp = parent.frameGeometry().height()
                    cp = parent.mapToGlobal(QtCore.QPoint(wp/2., hp/2.))
                else:
                    cp = QtGui.QDesktopWidget().availableGeometry().center()
                    
                qr.moveCenter(cp)                    
                self.move(qr.topLeft())           
                self.setFixedSize(self.size())
                
                    
#=============================================================================
        
class TabHydrograph(QtGui.QWidget):                        # @TAB HYDROGRAPH #
    
#=============================================================================
    
    def __init__(self, parent):
        super(TabHydrograph, self).__init__(parent)
        self.parent = parent        
        self.initUI()
    
        
    def initUI(self): #=======================================================
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
    #=========================================================================
       
        #------------------------------------------------------- DATABASE ----
       
        styleDB = db.styleUI()
    
        #------------------------------------------------- Variables Init ----
        
        self.UpdateUI = True
        self.fwaterlvl = []
        self.waterlvl_data = hydroprint.WaterlvlData()
        self.meteo_data = meteo.MeteoObj()
        
        #--------------------------------------------- WEATHER AVG WINDOW ----
        
        self.weather_avg_graph = meteo.WeatherAvgGraph()
        projectdir = self.parent.projectdir
        self.weather_avg_graph.save_fig_dir = projectdir
        
        #-------------------------------------------------- waterlvl_calc ----
        
        self.waterlvl_calc = waterlvl_calc.WLCalc()
        self.waterlvl_calc.hide()
        
        #-------------------------------------------- Widget : Page Setup ----
               
        self.page_setup_win = PageSetupWin(self)        
        self.page_setup_win.newPageSetupSent.connect(self.layout_changed)
        
        #-------------------------------------------------------- TOOLBAR ----
        
        #---- Graph Title Section ----
        
        graph_title_widget = QtGui.QWidget()
        
        self.graph_title = QtGui.QLineEdit()
        self.graph_title.setMaxLength(65)
        self.graph_title.setEnabled(False)
        self.graph_title.setText('Add A Title To The Figure Here')
        self.graph_title.setToolTip(ttipDB.addTitle)
        self.graph_status = QtGui.QCheckBox() 
        
        graph_title_layout = QtGui.QGridLayout()
        graph_title_layout.addWidget(QtGui.QLabel('         '), 0, 0)
        graph_title_layout.addWidget(self.graph_title, 0, 1)
        graph_title_layout.addWidget(self.graph_status, 0, 2)
        graph_title_layout.setColumnStretch(1, 100)
        
        graph_title_widget.setLayout(graph_title_layout)        
        
        #---- Toolbar Buttons ----
        
        btn_loadConfig = QtGui.QToolButton()
        btn_loadConfig.setAutoRaise(True)
        btn_loadConfig.setIcon(iconDB.load_graph_config)
        btn_loadConfig.setToolTip(ttipDB.loadConfig)
        btn_loadConfig.setIconSize(styleDB.iconSize)        
                                  
        btn_saveConfig = QtGui.QToolButton()
        btn_saveConfig.setAutoRaise(True)
        btn_saveConfig.setIcon(iconDB.save_graph_config)
        btn_saveConfig.setToolTip(ttipDB.saveConfig)
        btn_saveConfig.setIconSize(styleDB.iconSize)
        
        btn_bestfit_waterlvl = QtGui.QToolButton()
        btn_bestfit_waterlvl.setAutoRaise(True)
        btn_bestfit_waterlvl.setIcon(iconDB.fit_y)        
        btn_bestfit_waterlvl.setToolTip(ttipDB.fit_y)
        btn_bestfit_waterlvl.setIconSize(styleDB.iconSize)
        
        btn_bestfit_time = QtGui.QToolButton()
        btn_bestfit_time.setAutoRaise(True)
        btn_bestfit_time.setIcon(iconDB.fit_x)
        btn_bestfit_time.setToolTip(ttipDB.fit_x)
        btn_bestfit_time.setIconSize(styleDB.iconSize)
        
        btn_closest_meteo = QtGui.QToolButton()
        btn_closest_meteo.setAutoRaise(True)
        btn_closest_meteo.setIcon(iconDB.closest_meteo)
        btn_closest_meteo.setToolTip(ttipDB.closest_meteo)
        btn_closest_meteo.setIconSize(styleDB.iconSize)
        
        btn_draw = QtGui.QToolButton()
        btn_draw.setAutoRaise(True)
        btn_draw.setIcon(iconDB.refresh)        
        btn_draw.setToolTip(ttipDB.draw_hydrograph)
        btn_draw.setIconSize(styleDB.iconSize)
        
        btn_weather_normals = QtGui.QToolButton()
        btn_weather_normals.setAutoRaise(True)
        btn_weather_normals.setIcon(iconDB.meteo)        
        btn_weather_normals.setToolTip(ttipDB.weather_normals)
        btn_weather_normals.setIconSize(styleDB.iconSize)
        
        self.btn_work_waterlvl = QtGui.QToolButton()
        self.btn_work_waterlvl.setAutoRaise(True)
        self.btn_work_waterlvl.setIcon(iconDB.toggleMode)        
        self.btn_work_waterlvl.setToolTip(ttipDB.work_waterlvl)
        self.btn_work_waterlvl.setIconSize(styleDB.iconSize)

        btn_save = QtGui.QToolButton()
        btn_save.setAutoRaise(True)
        btn_save.setIcon(iconDB.save)
        btn_save.setToolTip(ttipDB.save_hydrograph)
        btn_save.setIconSize(styleDB.iconSize)
        
        btn_page_setup = QtGui.QToolButton()
        btn_page_setup.setAutoRaise(True)
        btn_page_setup.setIcon(iconDB.page_setup)
        btn_page_setup.setToolTip(ttipDB.btn_page_setup)
        btn_page_setup.setIconSize(styleDB.iconSize)
        btn_page_setup.clicked.connect(self.page_setup_win.show)
        
        class VertSep(QtGui.QFrame):
            def __init__(self, parent=None):
                super(VertSep, self).__init__(parent)
                self.setFrameStyle(styleDB.VLine)
        
        #---- Layout ----
        
        btn_list = [self.btn_work_waterlvl, VertSep(), btn_save, btn_draw,
                    btn_loadConfig, btn_saveConfig, VertSep(), 
                    btn_bestfit_waterlvl, btn_bestfit_time, btn_closest_meteo,
                    VertSep(), btn_weather_normals, btn_page_setup,
                    graph_title_widget]
        
        subgrid_toolbar = QtGui.QGridLayout()
        toolbar_widget = QtGui.QWidget()
           
        row = 0; col=0
        for btn in btn_list:
            subgrid_toolbar.addWidget(btn, row, col)
            col += 1
                       
        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)
        
        toolbar_widget.setLayout(subgrid_toolbar)
        
        #---------------------------------------------- Widget Data Files ----
       
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
#        subgrid.setColumnMinimumWidth(0, 200)
        subgrid.setContentsMargins(0, 0, 0, 0)
        
        subgrid_widget.setLayout(subgrid)
        
        #---------------------------------------------- Scales Tab Widget ----
                
        #----  Tab Time Scale ----
        
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
        
        #---- Tab Water Level Scale ----
        
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
        
        #---- Tab Weather Scale ----
        
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
                
        #---- ASSEMBLING TABS ----
        
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
                
        #----------------------------------------------------- LEFT PANEL ----
        
        #---- SubGrid Hydrograph Frame ----
        
        self.hydrograph = hydroprint.Hydrograph()
#        self.hydrograph_canvas = FigureCanvasQTAgg(self.hydrograph)
#        self.hydrograph_canvas.draw()        
        
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
        
        grid_layout.setContentsMargins(0, 0, 0, 0) # Left, Top, Right, Bottom 
        grid_layout.setSpacing(5)
        grid_layout.setColumnStretch(0, 500)
        grid_layout.setRowStretch(1, 500)
        
        self.grid_layout_widget.setLayout(grid_layout)
        
        #---------------------------------------------------- RIGHT PANEL ----
        
        grid_RIGHT = QtGui.QGridLayout()
        grid_RIGHT_widget = QtGui.QFrame()
        
        row = 0
        col = 0
        grid_RIGHT.addWidget(subgrid_widget, row, col)
        row += 1
        grid_RIGHT.addWidget(self.waterlvl_calc.widget_MRCparam, row, col)
        self.waterlvl_calc.widget_MRCparam.hide()
        grid_RIGHT.addWidget(self.tabscales, row, col)     
        row += 1
        grid_RIGHT.addWidget(self.subgrid_labLang_widget, row, col)
        
        grid_RIGHT_widget.setLayout(grid_RIGHT)
        grid_RIGHT.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)
        grid_RIGHT.setSpacing(15)
        grid_RIGHT.setRowStretch(row+1, 500)
        
        #------------------------------------------------------ MAIN GRID ----
                
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
                
        #-------------------------------------------------- MESSAGE BOXES ----
                                          
        self.msgBox = QtGui.QMessageBox()
        self.msgBox.setIcon(QtGui.QMessageBox.Question)
        self.msgBox.setStandardButtons(QtGui.QMessageBox.Yes |
                                       QtGui.QMessageBox.No)
        self.msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
        self.msgBox.setWindowTitle('Save Graph Layout')
        self.msgBox.setWindowIcon(iconDB.WHAT)
        
                
        self.msgError = MyQWidget.MyQErrorMessageBox()
        
        #--------------------------------------------------------- EVENTS ----
        
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
        
        #----- Hydrograph Layout -----
        
        self.datum_widget.currentIndexChanged.connect(self.layout_changed)
        self.language_box.currentIndexChanged.connect(self.layout_changed)
        self.waterlvl_max.valueChanged.connect(self.layout_changed)
        self.waterlvl_scale.valueChanged.connect(self.layout_changed)
        self.Ptot_scale.valueChanged.connect(self.layout_changed)
        self.date_start_widget.dateChanged.connect(self.layout_changed)
        self.graph_status.stateChanged.connect(self.layout_changed)
        self.graph_title.editingFinished.connect(self.layout_changed)        
        self.date_start_widget.dateChanged.connect(self.layout_changed)
        self.date_end_widget.dateChanged.connect(self.layout_changed)
        
#        self.datum_widget.currentIndexChanged.connect(self.datum_changed)
#        self.language_box.currentIndexChanged.connect(self.language_changed)
#        self.waterlvl_max.valueChanged.connect(self.waterlvl_scale_changed)
#        self.waterlvl_scale.valueChanged.connect(self.waterlvl_scale_changed)
#        self.Ptot_scale.valueChanged.connect(self.Ptot_scale_changed)
#        self.graph_status.stateChanged.connect(self.fig_title_state_changed)
#        self.graph_title.editingFinished.connect(self.fig_title_changed)        
#        self.date_start_widget.dateChanged.connect(self.time_scale_changed)
#        self.date_end_widget.dateChanged.connect(self.time_scale_changed)
        
        #----------------------------------------------------- Init Image ----
        
        self.hydrograph_scrollarea.load_image(self.hydrograph)
            
    def toggle_layoutMode(self): #============================================
        
        self.waterlvl_calc.hide()        
        self.grid_layout_widget.show()
        
        #---- Right Panel Update ----
        
        self.waterlvl_calc.widget_MRCparam.hide()
        self.tabscales.show()
#        self.subgrid_dates_widget.show() 
#        self.subgrid_WLScale_widget.show()
        self.subgrid_labLang_widget.show()
        
    def toggle_computeMode(self): #===========================================
        
        self.grid_layout_widget.hide()
        self.waterlvl_calc.show()
        
        #---- Right Panel Update ----
        
        self.waterlvl_calc.widget_MRCparam.show()
        self.tabscales.hide()
#        self.subgrid_dates_widget.hide()
#        self.subgrid_WLScale_widget.hide()
        self.subgrid_labLang_widget.hide()
        
    def show_weather_averages(self): #========================================
        
        filemeteo = self.hydrograph.fmeteo
        if not filemeteo:
            
            self.parent.write2console(
            '''<font color=red>No valid Weather Data File currently 
                 selected.</font>''')
                               
            self.emit_error_message(
            '''<b>Please select a valid Weather Data File first.</b>''')
            
            return
        
        self.weather_avg_graph.generate_graph(filemeteo)
        
        #---- SHOW ----
        
        # Force the window to show in the center of the WHAT window.
        
        self.weather_avg_graph.show()
                                
        qr = self.weather_avg_graph.frameGeometry()
           
        wp = self.frameGeometry().width()
        hp = self.frameGeometry().height()
        cp = self.mapToGlobal(QtCore.QPoint(wp/2., hp/2.))
            
        qr.moveCenter(cp)
        self.weather_avg_graph.move(qr.topLeft())
        
        self.weather_avg_graph.setFixedSize(self.weather_avg_graph.size())           
            
    def emit_error_message(self, error_text): #===============================
        
        self.msgError.setText(error_text)
        self.msgError.exec_()
    
    
    def select_waterlvl_file(self): #=========================================
        
        '''
        This method is called by <btn_waterlvl_dir> is clicked. It prompts
        the user to select a valid Water Level Data file.        
        '''
    
        
        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                  self, 'Select a valid water level data file', 
                                  self.waterlvl_dir, '*.xls')
        
        self.load_waterlvl(filename)
        
                              
    def load_waterlvl(self, filename): #======================================
        
        '''
        If "filename" exists:
        
        The (1) water level time series, (2) observation well info and the
        (3) manual measures are loaded and saved in the class instance 
        "waterlvl_data".
        
        Then the code check if there is a layout already saved for this well
        and if yes, will prompt the user if he wants to load it.
        
        Depending if there is a lyout or not, a Weather Data File will be 
        loaded and the hydrograph will be automatically plotted.
        '''
        
        
        if not filename:
            print('Path is empty. Cannot load water level file.')
            return
            
        self.parent.check_project()
            
        self.UpdateUI = False
            
        #----- Update UI Memory Variables -----
        
        self.waterlvl_dir = path.dirname(filename)
        self.fwaterlvl = filename
        
        #----- Load Data -----
        
        state = self.waterlvl_data.load(filename)
        if state == False:
            msg = ('WARNING: Waterlvl data file "%s" is not formatted ' +
                   ' correctly.') % path.basename(filename)
            print(msg)
            
            self.parent.write2console('''<font color=red>%s''' % msg)
            return False
            
        name_well = self.waterlvl_data.name_well
                
        #----- Load Manual Measures -----
        
        filename = self.parent.projectdir + '/waterlvl_manual_measurements.xls'        
        self.waterlvl_data.load_waterlvl_measures(filename, name_well)
        
        #----- Update Waterlvl Obj -----
        
        self.hydrograph.set_waterLvlObj(self.waterlvl_data)
        
        #----- Display Well Info in UI -----
        
        self.well_info_widget.setText(self.waterlvl_data.well_info)
        
        self.parent.write2console(
        '''<font color=black>Water level data set loaded successfully for
             well %s.</font>''' % name_well)
             
        #---- Update "Compute" Mode Graph ----
        
        self.draw_computeMode_waterlvl()
        
        #---- Well Layout -----

        filename = self.parent.projectdir + '/graph_layout.lst'
        isLayoutExist = self.hydrograph.checkLayout(name_well, filename)
                        
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
            
        #----------------------------------------------------- Enable UI -----
        
        self.UpdateUI = True
            
    def select_closest_meteo_file(self): #====================================
                
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
                    
                    with open(fmeteo, 'rb') as f:
                        reader = list(csv.reader(f, delimiter='\t'))
               
                    LAT2[i] = float(reader[2][1])
                    LON2[i] = float(reader[3][1])
                    DIST[i] = hydroprint.LatLong2Dist(LAT1, LON1, LAT2[i], 
                                                      LON2[i])
                    
                    i += 1
                    
                index = np.where(DIST == np.min(DIST))[0][0]
                          
                self.load_meteo_file(fmeteo_paths[index])
                QtCore.QCoreApplication.processEvents()
                
                self.draw_hydrograph()
    
           
    def select_meteo_file(self): #============================================
       
        '''
        This method is called by <btn_weather_dir.clicked.connect>. It prompts
        the user to select a valid Weather Data file.        
        '''
    
         
        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                      self, 'Select a valid weather data file', 
                                      self.meteo_dir, '*.out')       

        QtCore.QCoreApplication.processEvents()
        QtCore.QCoreApplication.processEvents()
        QtCore.QCoreApplication.processEvents()
        
        self.load_meteo_file(filename)
    
           
    def load_meteo_file(self, filename): #====================================
        
        if not filename:
            print('Path is empty. Cannot load weather data file.')
            return
            
        self.meteo_dir = path.dirname(filename)
        self.hydrograph.fmeteo = filename
        self.hydrograph.finfo = filename[:-3] + 'log'
        
        self.meteo_data.load_and_format(filename)
        self.meteo_info_widget.setText(self.meteo_data.INFO)        
        self.parent.write2console(
        '''<font color=black>Weather data set loaded successfully for
             station %s.</font>''' % self.meteo_data.STA)
        
        if self.fwaterlvl:
            
            QtCore.QCoreApplication.processEvents()
            self.draw_hydrograph()
    
    
    def update_graph_layout_parameter(self): #================================
    
        '''
        This method is called either by the methods <save_graph_layout>
        or by <draw_hydrograph>. It fetches the values that are currently 
        displayed in the UI and save them in the class instance 
        <hydrograph> of the class <Hydrograph>.
        '''    
        
        if self.UpdateUI == False:
            return
        
        #---- dates ----
        year = self.date_start_widget.date().year()
        month = self.date_start_widget.date().month()
        day = 1
        date = xldate_from_date_tuple((year, month, day),0)
        self.hydrograph.TIMEmin = date
        
        year = self.date_end_widget.date().year()
        month = self.date_end_widget.date().month()
        day = 1
        date = xldate_from_date_tuple((year, month, day),0)
        self.hydrograph.TIMEmax = date
        
        #---- scales ----
        
        self.hydrograph.WLscale = self.waterlvl_scale.value()
        self.hydrograph.WLmin = self.waterlvl_max.value()        
        self.hydrograph.RAINscale = self.Ptot_scale.value() 
        
        #---- graph title ----
        
        if self.graph_status.isChecked():
            self.hydrograph.title_state = 1
        else:
            self.hydrograph.title_state = 0            
        self.hydrograph.title_text = self.graph_title.text()
        
        #---- label language ----
        
        self.hydrograph.language = self.language_box.currentText()
        
        #---- figure size ----
        
        fwidth = self.page_setup_win.pageSize[0]
        self.hydrograph.set_fig_size(fwidth, 8.5)
             
            
    def load_graph_layout(self): #============================================
    

        self.parent.check_project()
        
        #----------------------------------- Check if Waterlvl Data Exist ----
        
        if not self.fwaterlvl:
            
            self.parent.write2console(
            '''<font color=red>No valid water level data file currently 
                 selected. Cannot load graph layout.</font>''')
                               
            self.emit_error_message(
            '''<b>Please select a valid water level data file.</b>''')
            
            return
        
        #----------------------------------------- Check if Layout Exists ----
                
        filename = self.parent.projectdir + '/graph_layout.lst'
        name_well = self.waterlvl_data.name_well
        isLayoutExist = self.hydrograph.checkLayout(name_well, filename)
                    
        if isLayoutExist == False:
            
            self.parent.write2console(
            '''<font color=red>No graph layout exists for well %s.
               </font>''' % name_well)
            
            self.emit_error_message('''<b>No graph layout exists 
                                         for well %s.</b>''' % name_well)
                                             
            return
        
        #---------------------------------------------------- Load Layout ----
                    
        self.hydrograph.load_layout(name_well, filename)
        
        #----------------------------------------------------- Update UI -----
        
        self.UpdateUI = False
                                         
        date = self.hydrograph.TIMEmin
        date = xldate_as_tuple(date, 0)
        self.date_start_widget.setDate(QDate(date[0], date[1], date[2]))
        
        date = self.hydrograph.TIMEmax
        date = xldate_as_tuple(date, 0)
        self.date_end_widget.setDate(QDate(date[0], date[1], date[2]))
                                    
        self.waterlvl_scale.setValue(self.hydrograph.WLscale)
        self.waterlvl_max.setValue(self.hydrograph.WLmin)
        self.datum_widget.setCurrentIndex (self.hydrograph.WLdatum)
        
        self.Ptot_scale.setValue(self.hydrograph.RAINscale)
         
        if self.hydrograph.title_state == 1:
            self.graph_status.setCheckState(QtCore.Qt.Checked)
        else:                    
            self.graph_status.setCheckState(QtCore.Qt.Unchecked)
            
        self.graph_title.setText(self.hydrograph.title_text)
        
        #----- Check if Weather Data File exists -----
        
        if path.exists(self.hydrograph.fmeteo):
            self.meteo_data.load_and_format(self.hydrograph.fmeteo)
            INFO = self.meteo_data.build_HTML_table()
            self.meteo_info_widget.setText(INFO)
            self.parent.write2console(
            '''<font color=black>Graph layout loaded successfully for 
               well %s.</font>''' % name_well)
               
            QtCore.QCoreApplication.processEvents()
            
            self.draw_hydrograph()
        else:
            self.meteo_info_widget.setText('')
            self.parent.write2console(
            '''<font color=red>Unable to read the weather data file. %s
               does not exist.</font>''' % self.hydrograph.fmeteo)
            self.emit_error_message(
            '''<b>Unable to read the weather data file.<br><br>
               %s does not exist.<br><br> Please select another weather
               data file.<b>''' % self.hydrograph.fmeteo)
            self.hydrograph.fmeteo = []
            self.hydrograph.finfo = []
            
        self.UpdateUI = True    
    
    def save_config_isClicked(self): #========================================
        
        if not self.fwaterlvl:
            
            self.parent.write2console(
            '''<font color=red>No valid water level file currently selected.
                 Cannot save graph layout.
               </font>''')
            
            self.msgError.setText(
            '''<b>Please select valid water level data file.</b>''')
            
            self.msgError.exec_()
            
            return
            
        if not self.hydrograph.fmeteo:
            
            self.parent.write2console(
            '''<font color=red>No valid weather data file currently selected. 
                 Cannot save graph layout.
               </font>''')
            
            self.msgError.setText(
                            '''<b>Please select valid weather data file.</b>''')
                            
            self.msgError.exec_()
            
            return
            
        #----------------------------------------- Check if Layout Exists ----
            
        filename = self.parent.projectdir + '/graph_layout.lst'
        if not path.exists(filename):
            # Force the creation of a new "graph_layout.lst" file
            self.parent.check_project()
            
        name_well = self.waterlvl_data.name_well
        isLayoutExist = self.hydrograph.checkLayout(name_well, filename)
        
        #---------------------------------------------------- Save Layout ----
        
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
              
    def save_graph_layout(self, name_well): #=================================
        
        self.update_graph_layout_parameter()
        filename = self.parent.projectdir + '/graph_layout.lst'
        self.hydrograph.save_layout(name_well, filename)
        self.parent.write2console(
        '''<font color=black>Graph layout saved successfully
             for well %s.</font>''' % name_well)
            
    def best_fit_waterlvl(self): #============================================
        
        if len(self.waterlvl_data.lvl) != 0:
            
            WLscale, WLmin = self.hydrograph.best_fit_waterlvl()
            
            self.waterlvl_scale.setValue(WLscale)
            self.waterlvl_max.setValue(WLmin)
            
    def best_fit_time(self): #================================================
            
        if len(self.waterlvl_data.time) != 0:
            
            TIME = self.waterlvl_data.time 
            date0, date1 = self.hydrograph.best_fit_time(TIME)
            
            self.date_start_widget.setDate(QDate(date0[0], date0[1], date0[2]))                                                        
            self.date_end_widget.setDate(QDate(date1[0], date1[1], date1[2]))
            
    def select_save_path(self): #=============================================
       
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
            
    def save_figure(self, fname): #===========================================
        
        self.hydrograph.generate_hydrograph(self.meteo_data)
                                       
        self.hydrograph.savefig(fname)
        
    def draw_computeMode_waterlvl(self): #====================================
        
        self.waterlvl_calc.time = self.waterlvl_data.time
        self.waterlvl_calc.water_lvl = self.waterlvl_data.lvl
        self.waterlvl_calc.soilFilename = self.waterlvl_data.soilFilename
        
        self.waterlvl_calc.plot_water_levels() 
    
    def draw_hydrograph(self): #==============================================
        
        if not self.fwaterlvl:
            console_text = ('<font color=red>Please select a valid water ' +
                            'level data file</font>')
            self.parent.write2console(console_text)
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            
            return
            
        if not self.hydrograph.fmeteo:
            console_text = ('<font color=red>Please select a valid ' +
                            'weather data file</font>')
            self.parent.write2console(console_text)
            self.emit_error_message(
            '''<b>Please select a valid Weather Data File first.</b>''')
            
            return
                    
        self.update_graph_layout_parameter()
        
        #----- Generate and Display Graph -----
        
        self.hydrograph.generate_hydrograph(self.meteo_data)
        self.hydrograph_scrollarea.load_image(self.hydrograph)
        
    def layout_changed(self):
        sender = self.sender()
        
        if self.UpdateUI == False:
            return
        
        if sender == self.language_box:
            self.hydrograph.language = self.language_box.currentText()
            if self.hydrograph.isHydrographExists:
                self.hydrograph.draw_ylabels()
                self.hydrograph.draw_xlabels()
                
        elif sender == self.waterlvl_max or sender == self.waterlvl_scale:                  
            self.hydrograph.WLmin = self.waterlvl_max.value()
            self.hydrograph.WLscale = self.waterlvl_scale.value()            
            if self.hydrograph.isHydrographExists:
                self.hydrograph.update_waterlvl_scale()
                self.hydrograph.draw_ylabels() 
                
        elif sender == self.Ptot_scale:
            self.hydrograph.RAINscale = self.Ptot_scale.value()
            if self.hydrograph.isHydrographExists:             
                self.hydrograph.update_precip_scale()
                self.hydrograph.draw_ylabels()
                
        elif sender == self.datum_widget:
            self.hydrograph.WLdatum = self.datum_widget.currentIndex()
            self.hydrograph.WLmin = (self.waterlvl_data.ALT - 
                                     self.hydrograph.WLmin)
            if self.hydrograph.isHydrographExists: 
                self.hydrograph.update_waterlvl_scale()            
                self.hydrograph.draw_waterlvl()
                self.hydrograph.draw_ylabels()
                
        elif sender in [self.date_start_widget, self.date_end_widget]:            
            year = self.date_start_widget.date().year()
            month = self.date_start_widget.date().month()
            day = 1
            date = xldate_from_date_tuple((year, month, day), 0)
            self.hydrograph.TIMEmin = date
            
            year = self.date_end_widget.date().year()
            month = self.date_end_widget.date().month()
            day = 1
            date = xldate_from_date_tuple((year, month, day),0)
            self.hydrograph.TIMEmax = date
            
            if self.hydrograph.isHydrographExists:               
                self.hydrograph.set_time_scale()
                self.hydrograph.draw_weather()
                self.hydrograph.draw_figure_title()
                
        elif sender == self.graph_title:
                
            #---- Update Instance Variables ----
            
            self.hydrograph.title_text = self.graph_title.text()
                
            #---- Update Graph if Exists ----
                
            if self.hydrograph.isHydrographExists:                            
                self.hydrograph.draw_figure_title()
        
        elif sender == self.graph_status:        
            self.graph_title.setEnabled(self.graph_status.isChecked())
           
            if self.graph_status.isChecked():
                self.hydrograph.title_state = 1
                self.hydrograph.title_text = self.graph_title.text()
            else:
                self.hydrograph.title_state = 0
           
            if self.hydrograph.isHydrographExists == True:
                self.hydrograph.set_margins()
                self.hydrograph.draw_figure_title()
                
        elif sender == self.page_setup_win:
            fwidth = self.page_setup_win.pageSize[0]
            self.hydrograph.set_fig_size(fwidth, 8.5)
                
        self.refresh_hydrograph()
    
#    def language_changed(self): #=============================================
#        
#        if self.UpdateUI == True:
#            
#            #---- Update Instance Variables ----
#            
#            self.hydrograph.language = self.language_box.currentText()
#            
#            #---- Update Graph if Exists ----
#           
#            if self.hydrograph.isHydrographExists == True:
#                
#                self.hydrograph.draw_ylabels()
#                self.hydrograph.draw_xlabels()
#        
#                self.refresh_hydrograph()
                
#    def Ptot_scale_changed(self): #===========================================
#        
#        if self.UpdateUI == True:
#            
#            #---- Update Instance Variables ----
#            
#            self.hydrograph.RAINscale = self.Ptot_scale.value()
#            
#            #---- Update Graph if Exists ----
#           
#            if self.hydrograph.isHydrographExists == True:
#                
#                self.hydrograph.update_precip_scale()
#                self.hydrograph.draw_ylabels()
#            
#                self.refresh_hydrograph()
                
        
#    def waterlvl_scale_changed(self): #=======================================
#        
#        if self.UpdateUI == True:
#            
#            #---- Update Instance Variables ----
#        
#            self.hydrograph.WLmin = self.waterlvl_max.value()
#            self.hydrograph.WLscale = self.waterlvl_scale.value()
#            
#            #---- Update Graph if Exists ----
#           
#            if self.hydrograph.isHydrographExists == True:
#                
#                self.hydrograph.update_waterlvl_scale()
#                self.hydrograph.draw_ylabels()
#            
#                self.refresh_hydrograph()
                
#    def datum_changed(self, index): #=========================================
#        
#        if self.UpdateUI == True:
#            
#            #---- Update Instance Variables ----
#            
#            self.hydrograph.WLdatum = index
#            self.hydrograph.WLmin = (self.waterlvl_data.ALT - 
#                                     self.hydrograph.WLmin)
#          
#            self.hydrograph.update_waterlvl_scale()            
#            self.hydrograph.draw_waterlvl()
#            self.hydrograph.draw_ylabels()
#            
#            self.refresh_hydrograph()
    
#    def time_scale_changed(self): #===========================================
#        
#        if self.UpdateUI == True:
#            
#            #---- Update Instance Variables ----
#            
#            year = self.date_start_widget.date().year()
#            month = self.date_start_widget.date().month()
#            day = 1
#            date = xldate_from_date_tuple((year, month, day), 0)
#            self.hydrograph.TIMEmin = date
#            
#            year = self.date_end_widget.date().year()
#            month = self.date_end_widget.date().month()
#            day = 1
#            date = xldate_from_date_tuple((year, month, day),0)
#            self.hydrograph.TIMEmax = date
#            
#            #---- Update Graph if Exists ----
#           
#            if self.hydrograph.isHydrographExists == True:
#               
#                self.hydrograph.set_time_scale()
#                self.hydrograph.draw_weather()
#                self.hydrograph.draw_figure_title()
#            
#                self.refresh_hydrograph()
#    
#    def fig_title_state_changed(self): #======================================
#        
#        if self.graph_status.isChecked() == True:
#            self.graph_title.setEnabled(True)
#        else:
#            self.graph_title.setEnabled(False)
#        
#        if self.UpdateUI == True:
#           
#           #---- Update Instance Variables ----
#           
#           if self.graph_status.isChecked():
#               self.hydrograph.title_state = 1
#               self.hydrograph.title_text = self.graph_title.text()
#           else:
#               self.hydrograph.title_state = 0
#           
#           #---- Update Graph if Exists ----
#           
#           if self.hydrograph.isHydrographExists == True:
#
#               self.hydrograph.set_margins()
#               self.hydrograph.draw_figure_title()
#               self.refresh_hydrograph()
#               
#           else: # No hydrograph plotted yet
#               pass
                
#    def fig_title_changed(self): #============================================
#        
#        if self.UpdateUI == True :
#            
#            #---- Update Instance Variables ----
#        
#            self.hydrograph.title_text = self.graph_title.text()
#            
#            #---- Update Graph if Exists ----
#            
#            if self.hydrograph.isHydrographExists == True:
#                        
#                self.hydrograph.draw_figure_title()
#                self.refresh_hydrograph()
#
#            else: # No hydrograph plotted yet
#               pass
    
    def refresh_hydrograph(self): #===========================================
       
        self.hydrograph_scrollarea.load_image(self.hydrograph)
           
                                                                         

                

#=============================================================================    
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

    
    def __init__(self, parent=None): #==========================================
     
        if platform.system() == 'Windows':
            self.projectfile = '..\Projects\Example\Example.what'
        elif platform.system() == 'Linux':
            self.projectfile = '../Projects/Example/Example.what'
            
        self.language = 'English'
        
        self.full_error_analysis = 0
        self.fontsize_general = '14px'
        self.fontsize_console = '10px'
        self.fontsize_menubar = '12px'
    
    def save_pref_file(self): #=================================================
            
        projectfile = path.relpath(self.projectfile).encode('utf-8')
        
        fcontent = [['Project File:', projectfile],
                    ['Language:', self.language],
                    ['Full Error Analysis:', self.full_error_analysis],
                    ['Font-Size-General:', self.fontsize_general],
                    ['Font-Size-Console:', self.fontsize_console],
                    ['Font-Size-Menubar:', self.fontsize_menubar]]
       
        with open('WHAT.pref', 'wb') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(fcontent)
    
           
    def load_pref_file(self): #===============================================
            
        if not path.exists('WHAT.pref'):
            
            # Default values will be kept and a new .pref file will be
            # generated
            
            print('No "WHAT.pref" file found. A new one has been created.')
        
            self.save_pref_file()
        
        else:
            
            with open('WHAT.pref', 'rb') as f:
                reader = list(csv.reader(f, delimiter='\t'))
            
            self.projectfile = reader[0][1].decode('utf-8')
            if platform.system() == 'Linux':
                self.projectfile = self.projectfile.replace('\\', '/')
                        
            self.language = reader[1][1]
            
            try:
                self.full_error_analysis = int(reader[2][1])
            except:
                self.full_error_analysis = 0
            try:
                self.fontsize_general = reader[3][1]
            except:
                pass # keep default value
            try:
                self.fontsize_console = reader[4][1]
            except:
                pass # keep default value
            try:
                self.fontsize_menubar = reader[5][1]
            except:
                pass # keep default value
                        
            print('self.full_error_analysis = %d' % self.full_error_analysis)
            print
        

#=============================================================================                
class MyProject():
    """
    This class contains all the info and utilities to manage the current 
    active project.
    """
#=============================================================================

    
    def __init__(self, parent=None): #========================================
        
        self.name = ''
        self.lat = 0
        self.lon = 0
        
    
    def load_project_info(self, projectfile): #===============================
            
        print('Loading project info')
        
        with open(projectfile, 'rb') as f:
            reader = list(csv.reader(f, delimiter='\t'))
            
        self.name = reader[0][1].decode('utf-8')
        self.lat = float(reader[6][1])
        self.lon = float(reader[7][1])
        
       
################################################################################
#                                                                           
#                              MAIN FUNCTION
#                                                                          
################################################################################       

        
if __name__ == '__main__':
    
    app = QtGui.QApplication(sys.argv)
    instance_1 = MainWindow()
    sys.exit(app.exec_())
    


    
    
    
    
    
