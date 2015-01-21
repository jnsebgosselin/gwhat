# -*- coding: utf-8 -*-
"""
Copyright 2015 Jean-Sebastien Gosselin

email: jnsebgosselin@gmail.com

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

software_version = 'WHAT Beta 4.1.0'
last_modification = '20/01/2015'

#---- STANDARD LIBRARY IMPORTS ----

import csv
from copy import copy
#from urllib import urlretrieve
from urllib2 import urlopen, URLError
from sys import argv
from time import ctime, strftime, sleep, gmtime
from os import getcwd, listdir, makedirs, path
from string import maketrans
from datetime import datetime

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
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg
import matplotlib.pyplot as plt
#from scipy import signal
#from statsmodels.regression.quantile_regression import QuantReg

#---- PERSONAL IMPORTS ----

import database as db
import hydroprint
from hydroprint import LatLong2Dist
import meteo
import envirocan
from fill_weather_data import Weather_File_Info

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

class MainWindow(QtGui.QMainWindow):
    
    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.initUI()
    
    # A generic widget is first set as the central widget of the
    # MainWindow. Then, a QGridLayout is applied to this central
    # widget. Two widgets are then added to the central widget's grid:
    # (1) a Qsplitter widget on top and (2) a QProgressBar on the
    # bottom.
    #    
    # Two additional widgets are then added to the Qsplitter widget:
    # (1) a QTabWidget and (2) a QTextEdit widget that is the console 
    # terminal that was discussed above.
    #
    # The QTabWidget is composed of four tabs. Each
    # tab is defined within its own class that are child classes of the
    # MainWindow class. The layout of each tab is handled with a
    # QGridLayout.
    
    def initUI(self):
                            
#        self.setGeometry(350, 75, 800, 750)
        self.setWindowTitle(software_version)
        self.setWindowIcon(iconDB.WHAT)
        
        self.what_pref = WHATPref(self)
                        
        #----------------------------------------------------- MAIN CONSOLE ----
        
        self.main_console = QtGui.QTextEdit()        
        self.main_console.setReadOnly(True)
        self.main_console.setLineWrapMode(QtGui.QTextEdit.LineWrapMode.NoWrap)

        self.write2console(
        '''<font color=black>Thanks for using %s.</font>''' % software_version)
        self.write2console(
        '''<font color=black>Please report any bug or wishful feature to 
             Jean-S&eacute;bastien Gosselin at jnsebgosselin@gmail.com.
           </font>''')
        
        #------------------------------------------------------- TAB WIDGET ----
        
        Tab_widget = QtGui.QTabWidget()
        
        self.tab_dwnld_data = TabDwnldData(self)
        self.tab_fill = TabFill(self)
        tab_about = TabAbout(self)
        self.tab_hydrograph = TabHydrograph(self)
        
        Tab_widget.addTab(self.tab_dwnld_data, labelDB.text.TAB1)        
        Tab_widget.addTab(self.tab_fill, labelDB.text.TAB2) 
        Tab_widget.addTab(self.tab_hydrograph, labelDB.text.TAB3) 
        Tab_widget.addTab(tab_about, labelDB.text.TAB4)
        
        #-------------------------------------------------- SPLITTER WIDGET ----
                
        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Vertical)
        
        splitter.addWidget(Tab_widget)
        splitter.addWidget(self.main_console)
        
        splitter.setCollapsible(0, True)
        splitter.setStretchFactor(0, 100)    
        
        # Forces initially the main_console to its minimal height.
        splitter.setSizes([100, 1])          

        #---------------------------------------------- PROJECT DIR SUBGRID ----
                        
        project_label = QtGui.QLabel('Project Directory :')
        project_label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.project_dir_display = QtGui.QLineEdit()
        self.project_dir_display.setReadOnly(True)      
        
        self.btn_project_dir = QtGui.QPushButton('Browse')
        self.btn_project_dir.setIcon(iconDB.openFolder)
        
        proDir_widget = QtGui.QWidget()
        subgrid_proDir = QtGui.QGridLayout()
        
        row = 0
        subgrid_proDir.addWidget(project_label, row, 0)
        subgrid_proDir.addWidget(self.project_dir_display, row, 1)
        subgrid_proDir.addWidget(self.btn_project_dir, row, 2)
        
        subgrid_proDir.setSpacing(5)
        subgrid_proDir.setContentsMargins(0, 0, 0, 0) #Left, Top, Right, Bottom 
        subgrid_proDir.setColumnStretch(1, 500)
        
        proDir_widget.setLayout(subgrid_proDir)
        
        #-------------------------------------------------------- MAIN GRID ----
        
        self.pbar = QtGui.QProgressBar()
        self.pbar.setValue(0)
        
        main_widget = QtGui.QWidget()
        self.setCentralWidget(main_widget)        
        
        mainGrid = QtGui.QGridLayout()
        mainGrid.setSpacing(10)
        
        row = 0
        mainGrid.addWidget(proDir_widget, row, 0)
        row += 1
        mainGrid.addWidget(splitter, row, 0)
        row += 1
        mainGrid.addWidget(self.pbar, row, 0)
        
        main_widget.setLayout(mainGrid)
        
    #--------------------------------------------------------------- EVENTS ----
        
        self.btn_project_dir.clicked.connect(self.select_project_dir)
       
    #----------------------------------------------------------------- INIT ----
        
        self.what_pref.load_pref_file()
        self.load_project_dir(self.what_pref.project_dir)
        
    #===========================================================================  
    def write2console(self, console_text):
        '''
        This function is the bottle neck through which all messages writen in
        the console window must go through.
        '''
    #===========================================================================
        
        textime = '<font color=black>[' + ctime()[4:-8] + '] </font>'
                        
        self.main_console.append(textime + console_text)
        
    #===========================================================================
    def select_project_dir(self):
        '''
        <select_project_dir> is called by the event <btn_project_dir.clicked>.
        It allows the user to select a new active project directory.
        '''
    #===========================================================================
        
        dialog = QtGui.QFileDialog(self)
        dialog.setReadOnly(False)         
        project_dir = dialog.getExistingDirectory(self, 
                                   'Select a new or existing project directory',
                                   getcwd() + '/../Projects')
        
        self.load_project_dir(project_dir)                                   
                                   
    #===========================================================================
    def load_project_dir(self, project_dir):
        '''
        This method is called either on startup during <initUI> or when a new
        project folder is chosen with <select_project_dir>.        
        '''
    #===========================================================================
        
        if project_dir:
            
            self.what_pref.project_dir = project_dir
            
            self.what_pref.save_pref_file()            
            self.what_pref.load_pref_file()
            
            self.project_dir_display.setText(project_dir)
            
            #---- Load Station List ----
                    
#            station_list = []
#            for files in listdir(project_dir):
#                if files.endswith('.lst'):
#                    station_list.append(project_dir + '/' + files)
#            
#            if len(station_list) > 0:
#                self.tab_dwnld_data.station_list_path = station_list[0]            
#            else:
#                self.tab_dwnld_data.station_list_path = []

            self.tab_dwnld_data.load_stationList()
                
            #---- Load Weather Input Files ----
            
            self.tab_fill.load_data_dir_content()
            
            # ----- RESET UI Memory Variables -----
            
            self.tab_hydrograph.meteo_dir = project_dir + '/Meteo/Output'
            self.tab_hydrograph.waterlvl_dir = project_dir + '/Water Levels'
            self.tab_hydrograph.save_fig_dir = project_dir
                    
################################################################ @TAB HYDROGRAPH
        
class TabHydrograph(QtGui.QWidget):
    
################################################################ @TAB HYDROGRAPH
    
    def __init__(self, parent):
        super(TabHydrograph, self).__init__(parent)
        self.parent = parent        
        self.initUI()
        self.initUI_weather_normals()
    
    
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
        self.graph_params = hydroprint.GraphParameters(self)
        self.waterlvl_data = hydroprint.WaterlvlData()
        self.meteo_data = meteo.MeteoObj()
        
    #-------------------------------------------------------------- TOOLBAR ----
        
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
        btn_draw.setIcon(iconDB.draw_hydrograph)        
        btn_draw.setToolTip(ttipDB.draw_hydrograph)
        
        btn_weather_normals = QtGui.QToolButton()
        btn_weather_normals.setAutoRaise(True)
        btn_weather_normals.setIcon(iconDB.meteo)        
        btn_weather_normals.setToolTip(ttipDB.weather_normals)

        btn_save = QtGui.QToolButton()
        btn_save.setAutoRaise(True)
        btn_save.setIcon(iconDB.save)
        btn_save.setToolTip(ttipDB.save_hydrograph)

        separator1 = QtGui.QFrame()
        separator1.setFrameStyle(StyleDB.HLine)
        separator2 = QtGui.QFrame()
        separator2.setFrameStyle(StyleDB.HLine)
        separator3 = QtGui.QFrame()
        separator3.setFrameStyle(StyleDB.HLine)                    
                                     
        subgrid_toolbar = QtGui.QGridLayout()
        toolbar_widget = QtGui.QWidget()
        
        row = 0
        subgrid_toolbar.addWidget(btn_draw, row, 0)
        row += 1
        subgrid_toolbar.addWidget(btn_save, row, 0)
        row += 1
        subgrid_toolbar.addWidget(btn_loadConfig, row, 0)
        row += 1
        subgrid_toolbar.addWidget(btn_saveConfig, row, 0)
        row += 1
        subgrid_toolbar.addWidget(separator1, row, 0)
        row += 1
        subgrid_toolbar.addWidget(btn_bestfit_waterlvl, row, 0)
        row += 1
        subgrid_toolbar.addWidget(btn_bestfit_time, row, 0)
        row += 1
        subgrid_toolbar.addWidget(btn_closest_meteo, row, 0)
        row += 1
        subgrid_toolbar.addWidget(separator2, row, 0)
        row += 1
        subgrid_toolbar.addWidget(btn_weather_normals, row, 0)
        row += 1
        subgrid_toolbar.addWidget(separator3, row, 0)
       
        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)
        subgrid_toolbar.setRowStretch(row+1, 500)

        btn_loadConfig.setIconSize(QtCore.QSize(36, 36))
        btn_saveConfig.setIconSize(QtCore.QSize(36, 36))
        btn_bestfit_waterlvl.setIconSize(QtCore.QSize(36, 36))
        btn_bestfit_time.setIconSize(QtCore.QSize(36, 36))
        btn_closest_meteo.setIconSize(QtCore.QSize(36, 36))
        btn_weather_normals.setIconSize(QtCore.QSize(36, 36))
        btn_draw.setIconSize(QtCore.QSize(36, 36))
        btn_save.setIconSize(QtCore.QSize(36, 36))
        
        toolbar_widget.setLayout(subgrid_toolbar)
    
    #----------------------------------------------------------- GRID RIGHT ----
        
        #----- SubGrid Data Files -----
       
        btn_waterlvl_dir = QtGui.QPushButton('    Water Level Data File')
        btn_waterlvl_dir.setIcon(iconDB.openFile)
        self.well_info_widget = QtGui.QTextEdit()
        self.well_info_widget.setReadOnly(True)
        self.well_info_widget.setFixedHeight(150)
        
        btn_weather_dir = QtGui.QPushButton('    Weather Data File')
        btn_weather_dir.setIcon(iconDB.openFile)
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
        
        #----- SubGrid Dates -----
        
        subgrid2_widget=(QtGui.QFrame())
        subgrid2_widget.setFrameStyle(
                                  QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        label_date_start = QtGui.QLabel('Date Start :')
        label_date_end = QtGui.QLabel('Date End :')
        self.date_start_widget = QtGui.QDateEdit()
        self.date_start_widget.setDisplayFormat('dd / MM / yyyy')
        self.date_end_widget = QtGui.QDateEdit()
        self.date_end_widget.setDisplayFormat('dd / MM / yyyy')
        subgrid2 = QtGui.QGridLayout()
        subgrid2.setSpacing(5)
        row = 0
        subgrid2.addWidget(label_date_start, row, 0)
        subgrid2.addWidget(self.date_start_widget, row, 1)
        row +=1
        subgrid2.addWidget(label_date_end, row, 0)  
        subgrid2.addWidget(self.date_end_widget, row, 1)
        
        subgrid2_widget.setLayout(subgrid2)
        subgrid2.setContentsMargins(5, 5, 5, 5)
        
        #----- SubGrid Water Level Scale -----
        
        subgrid3_widget=(QtGui.QFrame())
        subgrid3_widget.setFrameStyle(
                                  QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        subgrid3 = QtGui.QGridLayout()
        subgrid3.setSpacing(5)
        
        row = 0
        label_waterlvl_scale = QtGui.QLabel('Water Level Scale :') 
        self.waterlvl_scale = QtGui.QDoubleSpinBox()
        self.waterlvl_scale.setSingleStep(0.05)
        self.waterlvl_scale.setSuffix('  m')
        self.waterlvl_scale.setAlignment(QtCore.Qt.AlignLeft)
        subgrid3.addWidget(label_waterlvl_scale, row, 0)        
        subgrid3.addWidget(self.waterlvl_scale, row, 1)
        row += 1
        label_waterlvl_max = QtGui.QLabel('Water Level Max :') 
        self.waterlvl_max = QtGui.QDoubleSpinBox()
        self.waterlvl_max.setSingleStep(0.1)
        self.waterlvl_max.setSuffix('  m')
        self.waterlvl_max.setAlignment(QtCore.Qt.AlignLeft)
        self.waterlvl_max.setMinimum(-1000)

        subgrid3.addWidget(label_waterlvl_max, row, 0)        
        subgrid3.addWidget(self.waterlvl_max, row, 1)
        
        subgrid3_widget.setLayout(subgrid3)
        subgrid3.setContentsMargins(5, 5, 5, 5) # (left, top, right, bottom)
                
        #----- ASSEMBLING SubGrids -----

        language_label = QtGui.QLabel('Label Language:')
        self.language_box = QtGui.QComboBox()
        self.language_box.setEditable(False)
        self.language_box.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.language_box.addItems(['French', 'English'])
        self.language_box.setCurrentIndex(1)
        
        grid_RIGHT = QtGui.QGridLayout()
        grid_RIGHT_widget = QtGui.QFrame()
        
        row = 0
        grid_RIGHT.addWidget(subgrid_widget, row, 0, 1, 2)
        row += 1
        grid_RIGHT.addWidget(subgrid2_widget, row, 0, 1, 2)        
        row += 1
        grid_RIGHT.addWidget(subgrid3_widget, row, 0, 1, 2)        
        row += 1
        grid_RIGHT.addWidget(language_label, row, 0)
        grid_RIGHT.addWidget(self.language_box, row, 1)
        
        grid_RIGHT_widget.setLayout(grid_RIGHT)
        grid_RIGHT.setContentsMargins(0, 0, 0, 0) # Left, Top, Right, Bottom 
        grid_RIGHT.setSpacing(15)
        grid_RIGHT.setRowStretch(row+1, 500)
        
    #------------------------------------------------------------ GRID LEFT ----
        
        #---- SubGrid Figure Frame ----
        
        # Two figures are generated. (1) One as a preview to display in the
        # UI and (2) the other to be saved as the final figure. This is to
        # circumvent any possible issue with computer screen resolution or any
        # distortion of the image by the backend or the UI widget.
        
        self.hydrograph2display = plt.figure() 
        self.hydrograph2display.patch.set_facecolor('white')
        
        self.hydrograph2save = plt.figure()
        self.hydrograph2save.set_size_inches(11, 8.5)
        self.hydrograph2save.patch.set_facecolor('white')

        self.hydrograph_widget = FigureCanvasQTAgg(self.hydrograph2display)
        
        hydrograph_frame = QtGui.QFrame()
        hydrograph_frame.setStyleSheet("QWidget{background-color: white}")
        hydrograph_frame.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        hydrograph_frame.setLineWidth(1)
        hydrograph_frame.setMidLineWidth(0)
        
        frame_layout =  QtGui.QGridLayout() 
        
        frame_layout.addWidget(self.hydrograph_widget, 1, 1)
        
        hydrograph_frame.setLayout(frame_layout)
        
        frame_layout.setRowStretch(0, 500)
        frame_layout.setRowStretch(2, 500)
        frame_layout.setColumnStretch(0, 500)
        frame_layout.setColumnStretch(2, 500)
        
        self.hydrograph_widget.setFixedWidth(1100/1.5)
        self.hydrograph_widget.setFixedHeight(800/1.5)
        
#        self.hydrograph_widget.setFixedWidth(1100/2.)
#        self.hydrograph_widget.setFixedHeight(800/2.)
#        policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
#        policy.setHeightForWidth(True)
#        self.hydrograph_widget.setSizePolicy(policy)
        
        #----- ASSEMBLING SubGrids -----
                
        graph_title_label = QtGui.QLabel('Figure Title :')
        self.graph_title = QtGui.QLineEdit()
        self.graph_title.setMaxLength(65)
        self.graph_title.setEnabled(False)
        self.graph_title.setText('Add A Title To The Figure Here')
        self.graph_status = QtGui.QCheckBox()        
        
        grid_LEFT = QtGui.QGridLayout()
        grid_LEFT_widget = QtGui.QFrame()
        
        row = 0
        grid_LEFT.addWidget(graph_title_label, row, 0)
        grid_LEFT.addWidget(self.graph_title, row, 1)
        grid_LEFT.addWidget(self.graph_status, row, 2)
        row += 1
        grid_LEFT.addWidget(hydrograph_frame, row, 0, 1, 3)
        
        grid_LEFT_widget.setLayout(grid_LEFT)
        grid_LEFT.setContentsMargins(0, 0, 0, 0) # Left, Top, Right, Bottom 
        grid_LEFT.setSpacing(15)
        grid_LEFT.setColumnStretch(1, 500)
        
    #----------------------------------------------------------- MAIN GRID -----
        
        mainGrid = QtGui.QGridLayout()
        
        row = 0 
        mainGrid.addWidget(grid_LEFT_widget, row, 0)
        mainGrid.addWidget(grid_RIGHT_widget, row, 1)
        mainGrid.addWidget(toolbar_widget, row, 2)        
        
        self.setLayout(mainGrid)
        mainGrid.setContentsMargins(10, 10, 10, 10) # Left, Top, Right, Bottom 
        mainGrid.setSpacing(15)
        mainGrid.setColumnStretch(0, 500)
        
    #------------------------------------------------------- MESSAGE BOXES -----
                                          
        self.msgBox = QtGui.QMessageBox()
        self.msgBox.setIcon(QtGui.QMessageBox.Question)
        self.msgBox.setStandardButtons(QtGui.QMessageBox.Yes |
                                       QtGui.QMessageBox.No)
        self.msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
        self.msgBox.setWindowTitle('Save Graph Layout')
        
        self.msgError = QtGui.QMessageBox()
        self.msgError.setIcon(QtGui.QMessageBox.Warning)
        self.msgError.setWindowTitle('Error Message')
        
    #-------------------------------------------------------------- EVENTS -----
        
        #----- Toolbox -----
        
        btn_loadConfig.clicked.connect(self.load_graph_layout)
        btn_saveConfig.clicked.connect(self.save_config_isClicked)
        btn_bestfit_waterlvl.clicked.connect(self.best_fit_waterlvl)
        btn_bestfit_time.clicked.connect(self.best_fit_time)
        btn_closest_meteo.clicked.connect(self.select_closest_meteo_file)
        btn_draw.clicked.connect(self.draw_hydrograph)
        btn_save.clicked.connect(self.select_save_path)
        btn_weather_normals.clicked.connect(self.show_weather_normals)
                
        #----- Others -----
        
        btn_waterlvl_dir.clicked.connect(self.select_waterlvl_file)
        btn_weather_dir.clicked.connect(self.select_meteo_file)
        self.graph_status.stateChanged.connect(self.enable_graph_title)
    
    def initUI_weather_normals(self):
        
        self.normals_fig = plt.figure()        
        self.normals_fig.set_size_inches(8.5, 5)        
        self.normals_fig.patch.set_facecolor('white')
        self.normals_fig_widget = FigureCanvasQTAgg(self.normals_fig)
        
        self.toolbar = NavigationToolbar2QTAgg(self.normals_fig_widget, self)
        # https://sukhbinder.wordpress.com/2013/12/16/
        #         simple-pyqt-and-matplotlib-example-with-zoompan/
             
        grid_normals = QtGui.QGridLayout()
        self.normals_window = QtGui.QWidget()
        
        row = 0
        grid_normals.addWidget(self.normals_fig_widget, row, 0)
        row += 1
        grid_normals.addWidget(self.toolbar, row, 0)
                
        self.normals_window.setLayout(grid_normals)
#        grid_normals.setContentsMargins(0, 0, 0, 0) # Left, Top, Right, Bottom 
#        grid_normals.setSpacing(15)
#        grid_normals.setColumnStretch(1, 500)
#        
#        self.normals_window.resize(250, 150)
        self.normals_window.setWindowTitle('Weather Normals')
    
    def show_weather_normals(self):
        
        fmeteo = self.graph_params.fmeteo
        if fmeteo:
            self.normals_window.setWindowTitle(
                        'Weather Normals for %s' % self.meteo_data.station_name) 
            TNORM, PNORM, RNORM, TSTD = meteo.calculate_normals(fmeteo)
            meteo.plot_monthly_normals(
                                    self.normals_fig, TNORM, PNORM, RNORM, TSTD)                      
            self.normals_fig_widget.draw()            
            self.normals_window.show()            
   
    def enable_graph_title(self):
        
        if self.graph_status.isChecked() == True:
            self.graph_title.setEnabled(True)
        else:
            self.graph_title.setEnabled(False)
            
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
        If <filename> exists, the (1) water level time series, (2) observation 
        well info and (3) the manual measures are loaded and saved in the class 
        instance <waterlvl_data>.
        '''
    #===========================================================================   
        
        if filename:
            
            #----- Update UI Memory Var -----
            
            self.waterlvl_dir = path.dirname(filename)
            self.fwaterlvl = filename
            
            #----- Load Data -----
            
            self.waterlvl_data.load(filename)
            
            name_well = self.waterlvl_data.name_well
            
            self.best_fit_waterlvl()
            self.best_fit_time()
            
            #----- Load Manual Measures -----
            
            filename = self.parent.what_pref.project_dir
            filename += '/waterlvl_manual_measurements.xls'
            
            if not path.exists(filename):
                # Force the creation of a new 'waterlvl_manual_measurements.csv'
                self.parent.what_pref.load_pref_file()
            
            self.waterlvl_data.load_waterlvl_measures(filename, name_well)
            
            #----- Load and Display Well Info in UI -----
            
            self.well_info_widget.setText(self.waterlvl_data.well_info)
            
            self.parent.write2console(
            '''<font color=black>Water level data set loaded successfully for
                 well %s.</font>''' % name_well)
            
            #----- Check if Layout -----
            
            self.check_if_layout_exist(name_well)
    
    def check_if_layout_exist(self, name_well):
        
        layoutExist  = self.graph_params.checkConfig(name_well)
                        
        if layoutExist == True:
            self.parent.write2console(
            '''<font color=black>A graph layout exists for well %s.
               </font>''' % name_well)
            
            self.msgBox.setText('<b>A graph layout already exists ' +
                                    'for well ' + name_well + '.<br><br> Do ' +
                                     'you want to load it?</b>')
            override = self.msgBox.exec_()

            if override == self.msgBox.Yes:
                self.load_graph_layout()
                            
            elif override == self.msgBox.No:
                self.select_closest_meteo_file()
                
        elif layoutExist == False:            
            self.select_closest_meteo_file()
        
            
    def select_closest_meteo_file(self):
                
        meteo_folder = self.parent.what_pref.project_dir + '/Meteo/Output'
        
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

        self.load_meteo_file(filename)
    
    #===========================================================================       
    def load_meteo_file(self, filename):
    #===========================================================================
    
        if filename:
            
            self.meteo_dir = path.dirname(filename)
            self.graph_params.fmeteo = filename
            self.graph_params.finfo = filename[:-3] + 'log'
            
            self.meteo_data.load(filename)
            
            self.parent.write2console(
            '''<font color=black>Weather data set loaded successfully for
                 station %s.</font>''' % self.meteo_data.station_name)
              
            self.meteo_info_widget.setText(self.meteo_data.info )        
    
    #===========================================================================
    def update_graph_layout_parameter(self):
        '''
        This method is called either by the methods <save_graph_layout>
        or by <draw_hydrograph>. It fetches the values that are currently 
        displayed in the UI and save them in the class instance <graph_params>
        of the class <GraphParameters>.  <graph_params> is an input 
        of the function <hydroprint.generate_hydrograph>.
        '''
    #===========================================================================
        
        if self.UpdateUI == True:
            
            year = self.date_start_widget.date().year()
            month = self.date_start_widget.date().month()
            day = 1
            date = xldate_from_date_tuple((year, month, day),0)
            self.graph_params.TIMEmin = date
            
            year = self.date_end_widget.date().year()
            month = self.date_end_widget.date().month()
            day = 1
            date = xldate_from_date_tuple((year, month, day),0)
            self.graph_params.TIMEmax = date
            
            self.graph_params.WLscale = self.waterlvl_scale.value()
            self.graph_params.WLmin = self.waterlvl_max.value()
            
            if self.graph_status.isChecked():
                self.graph_params.title_state = 1
            else:
                self.graph_params.title_state = 0
                
            self.graph_params.title_text = self.graph_title.text()
            
            self.graph_params.language = self.language_box.currentText()
                        
    def load_graph_layout(self):
        
        if not self.fwaterlvl:
            
            self.parent.write2console(
            '''<font color=red>No valid water level data file currently 
                 selected. Cannot load graph layout.</font>''')
                               
            self.emit_error_message(
            '''<b>Please select a valid water level data file.</b>''')
            
        else:
            name_well = self.waterlvl_data.name_well
            layoutExist  = self.graph_params.checkConfig(name_well)
                        
            if layoutExist == False:
                
                self.parent.write2console(
                '''<font color=red>No graph layout exists for well %s.
                   </font>''' % name_well)
                
                self.emit_error_message('''<b>No graph layout exists 
                                             for well %s.</b>''' % name_well)
            
            else: # Load graph layout for this well
                
                self.graph_params.load(name_well)
                
            #--------------------------------------------------- Update UI -----
                
                self.UpdateUI = False
                
                #----- Check if Weather Data File exists -----
                
                if path.exists(self.graph_params.fmeteo):
                    self.meteo_data.load(self.graph_params.fmeteo)
                    self.meteo_info_widget.setText(self.meteo_data.info )
                    self.parent.write2console(
                    '''<font color=black>Graph layout loaded successfully for 
                       well %s.</font>''' % name_well)
                else:
                    self.meteo_info_widget.setText('')
                    self.parent.write2console(
                    '''<font color=red>Unable to read the weather data file. %s
                       does not exist.</font>''' % self.graph_params.fmeteo)
                    self.emit_error_message(
                    '''<b>Unable to read the weather data file.<br><br>
                       %s does not exist.<br><br> Please select another weather
                       data file.<b>''' % self.graph_params.fmeteo)
                    self.graph_params.fmeteo = []
                    self.graph_params.finfo = []
                         
                date = self.graph_params.TIMEmin
                date = xldate_as_tuple(date, 0)
                self.date_start_widget.setDate(QDate(date[0], date[1], date[2]))
                
                date = self.graph_params.TIMEmax
                date = xldate_as_tuple(date, 0)
                self.date_end_widget.setDate(QDate(date[0], date[1], date[2]))
                                            
                self.waterlvl_scale.setValue(self.graph_params.WLscale)
                self.waterlvl_max.setValue(self.graph_params.WLmin)
                 
                if self.graph_params.title_state == 1:
                    self.graph_status.setCheckState(QtCore.Qt.Checked)
                else:                    
                    self.graph_status.setCheckState(QtCore.Qt.Unchecked)
                    
                self.graph_title.setText(self.graph_params.title_text)
                    
                self.UpdateUI = True
    
    def save_config_isClicked(self):
        
        if not self.fwaterlvl or not self.graph_params.fmeteo:
            
            self.parent.write2console(
            '''<font color=red>No valid water level or/and valid weather data 
                 file currently selected. Cannot save graph layout.
               </font>''')
            
            self.msgError.setText('''<b>Please select valid water level or/and 
                                       a valid weather data file.</b>''')
            self.msgError.exec_() 
            
        else:
            name_well = self.waterlvl_data.name_well
            
            layoutExist = self.graph_params.checkConfig(name_well)

            if layoutExist == True:
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
        self.graph_params.save(name_well)
        self.parent.write2console(
        '''<font color=black>Graph layout saved successfully
             for well %s.</font>''' % name_well)
            
    def best_fit_waterlvl(self):
        
        if len(self.waterlvl_data.lvl)!=0:
            
            WL = self.waterlvl_data.lvl
            WLscale, WLmin = self.graph_params.best_fit_waterlvl(WL)
            
            self.waterlvl_scale.setValue(WLscale)
            self.waterlvl_max.setValue(WLmin)
            
    def best_fit_time(self):
            
        if len(self.waterlvl_data.time)!=0:
            
            TIME = self.waterlvl_data.time 
            date0, date1 = self.graph_params.best_fit_time(TIME)
            
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
                fname = fname + ftype[1:]
                
            self.save_fig_dir = path.dirname(fname)
            self.save_figure(fname)
            
    def save_figure(self, fname):
        
        hydroprint.generate_hydrograph(self.hydrograph2save,
                                       self.waterlvl_data,
                                       self.meteo_data,
                                       self.graph_params)
                                       
        self.hydrograph2save.savefig(fname)
    
    def draw_hydrograph(self):
        
        if not self.fwaterlvl or not self.graph_params.fmeteo:
            console_text = ('<font color=red>Please select a valid water ' +
                            'level and a valid weather data file</font>')
            self.parent.write2console(console_text)
            
        elif self.fwaterlvl and self.graph_params.fmeteo:
            
            self.update_graph_layout_parameter()
            
            hydroprint.generate_hydrograph(self.hydrograph2display,
                                           self.waterlvl_data,
                                           self.meteo_data,
                                           self.graph_params)
                                       
            self.hydrograph_widget.draw()    
          
################################################################## @TAB DOWNLOAD
        
class TabDwnldData(QtGui.QWidget):

################################################################## @TAB DOWNLOAD  
    
    def __init__(self, parent):
        super(TabDwnldData, self).__init__(parent)
        self.parent = parent
        self.initUI()        
        
    def initUI(self):
        
    #-------------------------------------------------------SubGrid Station-----

        #----- SubGrid Weather Station -----#
        
        self.staName_display = QtGui.QComboBox()
        self.staName_display.setEditable(False)
        self.staName_display.setInsertPolicy(QtGui.QComboBox.NoInsert)
                
        btn_search4station = QtGui.QToolButton()
        btn_search4station.setAutoRaise(True)
        btn_search4station.setIcon(iconDB.search)
        btn_search4station.setToolTip(ttipDB.search4stations)
        
        btn_browse_staList = QtGui.QToolButton()
        btn_browse_staList.setIcon(iconDB.openFolder)
        btn_browse_staList.setAutoRaise(True)
        btn_browse_staList.setToolTip(ttipDB.btn_browse_staList)
        
        #btn_refresh_staList = QtGui.QToolButton()
        #btn_refresh_staList.setAutoRaise(True)
        #btn_refresh_staList.setIcon(iconDB.refresh)
        #btn_refresh_staList.setToolTip(ttipDB.refresh_staList)
        
        widget_weather_station = QtGui.QFrame()
        subgrid_weather_station = QtGui.QGridLayout()
        
        row = 0
        subgrid_weather_station.addWidget(self.staName_display, row, 0)
        subgrid_weather_station.addWidget(btn_search4station, row, 1)
        subgrid_weather_station.addWidget(btn_browse_staList, row, 2)
        #subgrid_weather_station.addWidget(btn_refresh_staList, row, 3)
        
        widget_weather_station.setLayout(subgrid_weather_station)
        subgrid_weather_station.setContentsMargins(0, 0, 0, 0) # Left, Top, 
                                                               # Right, Bottom 
        subgrid_weather_station.setSpacing(10)
        subgrid_weather_station.setColumnStretch(3, 500)
        subgrid_weather_station.setColumnMinimumWidth(0, 200)
                
        #----- SubGrid StartYear and EndYear -----#
        
        year_label1 = QtGui.QLabel('from')
        year_label1.setAlignment(QtCore.Qt.AlignCenter)
        self.yStart_edit = QtGui.QSpinBox()
        self.yStart_edit.setAlignment(QtCore.Qt.AlignCenter)        
        self.yStart_edit.setSingleStep(1)
        self.yStart_edit.setValue(0)        
        year_label2 = QtGui.QLabel('to')
        year_label2.setAlignment(QtCore.Qt.AlignCenter)
        self.yEnd_edit = QtGui.QSpinBox()
        self.yEnd_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.yEnd_edit.setSingleStep(1)
        self.yEnd_edit.setValue(0)
        
        subgrid_year_widget = QtGui.QFrame()
        subgrid_year = QtGui.QGridLayout()
        
        row = 0
        subgrid_year.addWidget(year_label1, row, 0)
        subgrid_year.addWidget(self.yStart_edit, row, 1)
        subgrid_year.addWidget(year_label2, row, 2)
        subgrid_year.addWidget(self.yEnd_edit, row, 3)
        
        subgrid_year_widget.setLayout(subgrid_year)
        subgrid_year.setContentsMargins(0, 0, 0, 0) #Left, Top, Right, Bottom 
        subgrid_year.setSpacing(15)
        subgrid_year.setColumnStretch(4, 500)
        
        #---- ASSEMBLING SubGrids -----#
        
        staName_label = QtGui.QLabel('Weather Station :')
        year_title = QtGui.QLabel('Download Data :')
         
        subgrid_Station = QtGui.QGridLayout()
        Station_widget = QtGui.QFrame()
        Station_widget.setFrameStyle(StyleDB.frame)                      
        
        row = 0
        subgrid_Station.addWidget(staName_label, row, 1)
        subgrid_Station.addWidget(widget_weather_station, row, 2)
        row += 1
        subgrid_Station.addWidget(year_title, row, 1)
        subgrid_Station.addWidget(subgrid_year_widget, row, 2)
        
        Station_widget.setLayout(subgrid_Station)
        subgrid_Station.setContentsMargins(15, 15, 15, 15) # Left, Top, 
                                                           # Right, Bottom 
        subgrid_Station.setVerticalSpacing(20)
        subgrid_Station.setHorizontalSpacing(10)
        # subgrid_Station.setColumnStretch(0, 100)
        subgrid_Station.setColumnStretch(6, 100)
                
    #-------------------------------------------------- GRID DOWNLOAD DATA -----
                
        self.btn_get = QtGui.QPushButton(labelDB.btn_get_text)
        self.btn_get.setIcon(iconDB.download)
        self.btn_get.setToolTip(ttipDB.btn_GetData)
                         
        grid_TOP = QtGui.QGridLayout()
        TOP_widget = QtGui.QFrame()
        
        row = 0
        grid_TOP.addWidget(Station_widget, row, 0, 1, 2)
        row += 1
        grid_TOP.addWidget(self.btn_get, row, 0)
                
        # Total number of columns = 3
        
        TOP_widget.setLayout(grid_TOP)
        grid_TOP.setContentsMargins(0, 0, 0, 15) #Left, Top, Right, Bottom 
        grid_TOP.setSpacing(15)
        grid_TOP.setColumnStretch(1, 500)
        
    #-----------------------------------------------------------GRID BOTTOM-----                     
        
        #----SubGrid display-------------------#
        
        self.merge_stats_display = QtGui.QTextEdit()
        self.merge_stats_display.setReadOnly(True)        
        self.merge_stats_display.setFrameStyle(0)
        
        grid_display = QtGui.QGridLayout()
        display_grid_widget = QtGui.QFrame()
        display_grid_widget.setFrameStyle(StyleDB.frame)
        
        row = 0
        grid_display.addWidget(self.merge_stats_display, row, 0)
        
        display_grid_widget.setLayout(grid_display)
        grid_display.setContentsMargins(0, 0, 0, 0) #Left, Top, Right, Bottom 
                
        #---ASSEMBLING SubGrids-------------------#
    
        self.merge_stats_display.setMaximumHeight(200)
        btn_select = QtGui.QPushButton(' Select')
        btn_select.setIcon(iconDB.openFile)
        btn_save = QtGui.QPushButton('Save')
        btn_save.setIcon(iconDB.save)
        self.saveAuto_checkbox = QtGui.QCheckBox(
                                           'Automatically save concatened data')
              
        grid_BOTTOM = QtGui.QGridLayout()
        BOTTOM_widget = QtGui.QFrame()
        
        row = 0
        grid_BOTTOM.addWidget(display_grid_widget, row, 0, 1, 8)        
        grid_BOTTOM.setRowStretch(row, 500)
        row += 1
        grid_BOTTOM.addWidget(btn_select, row, 0)
        grid_BOTTOM.addWidget(btn_save, row, 1, 1, 2) 
        grid_BOTTOM.addWidget(self.saveAuto_checkbox, row, 3, 1, 4)
        
        BOTTOM_widget.setLayout(grid_BOTTOM)
        grid_BOTTOM.setContentsMargins(0, 0, 0, 0) #Left, Top, Right, Bottom
        grid_BOTTOM.setSpacing(10)
        
    #-------------------------------------------------------------GRID MAIN-----
        
        TITLE_TOP = QtGui.QLabel(labelDB.title_download)    
        TITLE_BOTTOM  = QtGui.QLabel(labelDB.title_concatenate)
        
        line1 = QtGui.QFrame()
        line1.setFrameStyle(StyleDB.HLine)
        line2 = QtGui.QFrame()
        line2.setFrameStyle(StyleDB.HLine)
        line3 = QtGui.QFrame()
        line3.setFrameStyle(StyleDB.HLine)
        line4 = QtGui.QFrame()
        line4.setFrameStyle(StyleDB.HLine)        
                
        grid_MAIN = QtGui.QGridLayout()
        
        row = 0
        grid_MAIN.addWidget(line1, row, 1)
        row += 1
        grid_MAIN.addWidget(TITLE_TOP, row, 1)
        row += 1
        grid_MAIN.addWidget(line2, row, 1)
        row += 1
        grid_MAIN.addWidget(TOP_widget, row, 1)
        row += 1
        grid_MAIN.addWidget(line3, row, 1)
        row += 1
        grid_MAIN.addWidget(TITLE_BOTTOM, row, 1)
        row += 1
        grid_MAIN.addWidget(line4, row, 1)
        row += 1
        grid_MAIN.addWidget(BOTTOM_widget, row, 1)
        row += 1
        grid_MAIN.setRowStretch(row, 500)
        
        self.setLayout(grid_MAIN)
        grid_MAIN.setContentsMargins(15, 15, 15, 15) #Left, Top, Right, Bottom
        grid_MAIN.setHorizontalSpacing(10)
        grid_MAIN.setVerticalSpacing(10)
        grid_MAIN.setColumnStretch(0, 500)
        grid_MAIN.setColumnStretch(2, 500)
        
        #-------------------------------------------------------MESSAGE BOX-----
                                          
        self.msgBox = QtGui.QMessageBox()
        self.msgBox.setIcon(QtGui.QMessageBox.Warning)
        self.msgBox.setWindowTitle('Error Message')
        
        #----------------------------------------------------VARIABLES INIT-----
        
        self.MergeOutput = np.array([])
        self.dwnl_rawfiles = DownloadRawDataFiles(self)
        self.initUI_search4stations()
        
        #------------------------------------------------------------EVENTS-----       
                
        self.dwnl_rawfiles.ProgBarSignal.connect(self.setProgBarSignal)
        self.dwnl_rawfiles.ConsoleSignal.connect(self.parent.write2console)
        self.dwnl_rawfiles.MergeSignal.connect(self.download_is_finished)
        
        self.staName_display.currentIndexChanged.connect(self.staName_isChanged)
        self.btn_get.clicked.connect(self.fetch_start_and_stop)      
        #btn_refresh_staList.clicked.connect(self.load_stationList)
        btn_search4station.clicked.connect(self.show_search4stations)
        self.btn_go_search4station.clicked.connect(self.search4stations)
        btn_browse_staList.clicked.connect(self.select_stationList)
        
        btn_select.clicked.connect(self.select_raw_files)
        btn_save.clicked.connect(self.select_concatened_save_path)
                        
        self.yStart_edit.valueChanged.connect(self.start_year_changed)
        self.yEnd_edit.valueChanged.connect(self.end_year_changed)
        
        self.search4station_minYear.valueChanged.connect(
                                            self.search4station_minYear_changed)
        self.search4station_maxYear.valueChanged.connect(
                                            self.search4station_maxYear_changed)
    
    def start_year_changed(self):
        
        if len(self.staList) > 0:
        
            index = self.staName_display.currentIndex()
            min_yr = max(self.yStart_edit.value(), int(self.staList[index, 2]))
            max_yr = int(self.staList[index, 3])
                
            self.yEnd_edit.setRange(min_yr, max_yr)
   
    def end_year_changed(self):
        
        if len(self.staList) > 0:
            
            index = self.staName_display.currentIndex()
            min_yr = int(self.staList[index, 2])
            max_yr = min(self.yEnd_edit.value(), int(self.staList[index, 3]))
                    
            self.yStart_edit.setRange(min_yr, max_yr)
            
    def search4station_minYear_changed(self):
            
            min_yr = min_yr = max(self.search4station_minYear.value(), 1840)
            
            now = datetime.now()
            max_yr = now.year
                    
            self.search4station_maxYear.setRange(min_yr, max_yr)
            
    def search4station_maxYear_changed(self):
        
            min_yr = 1840
            
            now = datetime.now()
            max_yr = min(self.search4station_maxYear.value(), now.year)
                    
            self.search4station_minYear.setRange(min_yr, max_yr)
    
    #===========================================================================
    def initUI_search4stations(self):
        '''
        Sub-window that allows the user to search for weather stations on the
        Gov. of Can. website.
        '''
    #===========================================================================
        
        #---- Widgets ----
        
        label_Lat = QtGui.QLabel('Latitude :')
        label_Lat2 = QtGui.QLabel('N')
        label_Lon = QtGui.QLabel('Longitude :')
        label_Lon2 = QtGui.QLabel('W')
        label_radius = QtGui.QLabel('Radius :')
        
        self.latitude_SpinBox = QtGui.QDoubleSpinBox()
        self.latitude_SpinBox.setAlignment(QtCore.Qt.AlignCenter)        
        self.latitude_SpinBox.setSingleStep(0.1)
        self.latitude_SpinBox.setValue(0)
        self.latitude_SpinBox.setMinimum(0)
        self.latitude_SpinBox.setMaximum(180)
        self.latitude_SpinBox.setSuffix(u' °')
        
        self.longitude_SpinBox = QtGui.QDoubleSpinBox()
        self.longitude_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.longitude_SpinBox.setSingleStep(0.1)
        self.longitude_SpinBox.setValue(0)
        self.longitude_SpinBox.setMinimum(0)
        self.longitude_SpinBox.setMaximum(180)
        self.longitude_SpinBox.setSuffix(u' °')
        
        self.radius_SpinBox = QtGui.QSpinBox()
        self.radius_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.radius_SpinBox.setSingleStep(5)
        self.radius_SpinBox.setMinimum(5)
        self.radius_SpinBox.setMaximum(500)
        self.radius_SpinBox.setSuffix(' km')
        
        now = datetime.now()

        label_startYear = QtGui.QLabel('Start Year :')
        
        self.search4station_minYear = QtGui.QSpinBox()
        self.search4station_minYear.setAlignment(QtCore.Qt.AlignCenter)
        self.search4station_minYear.setSingleStep(1)
        self.search4station_minYear.setMinimum(1840)
        self.search4station_minYear.setMaximum(now.year)
        self.search4station_minYear.setValue(1840)
        
        label_endYear = QtGui.QLabel('End Year :')
        
        self.search4station_maxYear = QtGui.QSpinBox()
        self.search4station_maxYear.setAlignment(QtCore.Qt.AlignCenter)
        self.search4station_maxYear.setSingleStep(1)
        self.search4station_maxYear.setMinimum(1840)
        self.search4station_maxYear.setMaximum(now.year)
        self.search4station_maxYear.setValue(now.year)
        
        self.btn_go_search4station = QtGui.QPushButton('Search')
        self.btn_go_search4station.setIcon(iconDB.search)
        
        line1 = QtGui.QFrame()
        line1.setFrameStyle(StyleDB.VLine)
        
        #---- GRID ----
                        
        self.widget_search4stations = QtGui.QWidget()
        grid_search4stations = QtGui.QGridLayout()
        
        row = 1
        grid_search4stations.addWidget(label_Lat, row, 1, 1, 2)
        grid_search4stations.addWidget(self.latitude_SpinBox, row, 3)
        grid_search4stations.addWidget(label_Lat2, row, 4)
        grid_search4stations.addWidget(line1, row, 5, 3, 1)
        grid_search4stations.addWidget(label_startYear, row, 6)
        grid_search4stations.addWidget(self.search4station_minYear, row, 7) 
        row += 1
        grid_search4stations.addWidget(label_Lon, row, 1, 1, 2)
        grid_search4stations.addWidget(self.longitude_SpinBox, row, 3)
        grid_search4stations.addWidget(label_Lon2, row, 4)
        grid_search4stations.addWidget(label_endYear, row, 6)
        grid_search4stations.addWidget(self.search4station_maxYear, row, 7)
        row += 1
        grid_search4stations.addWidget(label_radius, row, 1, 1, 2)
        grid_search4stations.addWidget(self.radius_SpinBox, row, 3)
        row += 1
        grid_search4stations.addWidget(self.btn_go_search4station, row, 1, 1, 7)
                
        self.widget_search4stations.setLayout(grid_search4stations)
        grid_search4stations.setContentsMargins(25, 25, 25, 25) # Left, Top,
                                                                # Right, Bottom 
        grid_search4stations.setSpacing(10)
        grid_search4stations.setColumnStretch(0, 500)
        grid_search4stations.setColumnStretch(8, 500)
        grid_search4stations.setRowStretch(0, 500)
        grid_search4stations.setRowStretch(row + 1, 500)
        
        self.widget_search4stations.setWindowTitle(
                                                  'Search For Weather Stations')
#        self.widget_search4stations.setGeometry(250, 800, 250, 150)
        self.widget_search4stations.setFixedSize(450, 200)
        self.widget_search4stations.setWindowIcon(iconDB.WHAT)
    
    #===========================================================================
    def show_search4stations(self):
        '''
        Show sub-window search for weather stations when <btn_search4station>
        is clicked.
        '''
    #===========================================================================

        self.widget_search4stations.show()
    
    #===========================================================================
    def search4stations(self):
        '''
        Seach for weather stations with daily data. The results are saved in a
        "weather_stations.lst" and are automatically loaded in the "weather
        stations" dropbox list.
        '''
    #===========================================================================
        
        #---- Close sub-window ----
        
        self.widget_search4stations.close()
               
        #---- Generate New List ----
        
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        self.parent.write2console('''<font color=black>
                                       Searching for weather stations. Please
                                       wait...
                                     </font>''')
                                     
        QtCore.QCoreApplication.processEvents()
        QtCore.QCoreApplication.processEvents()
        
        LAT = self.latitude_SpinBox.value()
        LON = self.longitude_SpinBox.value()
        RADIUS = self.radius_SpinBox.value()
        startYear = self.search4station_minYear.value()
        endYear = self.search4station_maxYear.value()
      
        staList, cmt = envirocan.search4meteo(LAT, LON, RADIUS, 
                                              startYear, endYear)
        
        self.parent.write2console(cmt)
        
        #---- Save List ----
        
        projectdir = self.parent.what_pref.project_dir        
        fname = projectdir + '/weather_stations.lst'    
        with open(fname, 'wb') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(staList)
        
        #---- Load List ----
        
        self.load_stationList()
        
        QtGui.QApplication.restoreOverrideCursor()
        
    #===========================================================================
    def select_stationList(self):
        '''
        This method is called when the <btn_browse_staList> is clicked.
        It allows the user to select and load a custom weather station list.
        Info are loaded into memory and saved in the file named
        "weather_stations.lst".
        '''
    #===========================================================================
        
        dirname = self.parent.what_pref.project_dir
        
        
        fname, _ = QtGui.QFileDialog.getOpenFileName(
                         self, 'Select a valid station list', dirname, '*.lst')        
                        
        if fname:
            
            default_list_name = dirname + '/weather_stations.lst'
            
            if fname == default_list_name:
                 
                 #---- Load List in UI ----
            
                self.load_stationList()   
                
            else:
            
                #---- Load List ----
            
                reader = open(fname,'rb')
                reader = csv.reader(reader, delimiter='\t')
          
                #---- Save List in Default Name ----
            
                with open(default_list_name, 'wb') as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerows(reader)
            
                #---- Load List in UI ----
                
                QtGui.QApplication.processEvents()
                self.load_stationList()
            
    #===========================================================================
    def load_stationList(self): # refresh_stationList(self):
        '''
        This method is started either by :
        (1) when a new project folder is loaded in 
            <MainWindow.load_project_dir>
        (2) after a search has been completed for weather stations with 
            <search4stations>
        (3) When a station list is loaded manually by the user from method
            <select_stationList>.
        
        It loads the informations in the "weather_stations.lst" file that is
        located in the project folder and save it as a table in <self.staList>
        and displays the station list in the QComboBox widget.
        
        ----- weather_stations.lst -----
        
        The weather_station.lst is a tabulation separated csv file that contains
        the following information:  station names, station ID , date at which
        the data records begin and date at which the data records end, the
        provinces to which each station belongs, the climate ID and the
        Proximity value in km for the original search location.
        
        All these information can be found on the Government of Canada
        website in the address bar of the web browser when a station is
        selected. Note that the station ID is not the same as the Climate ID 
        of the station. For example, the ID for the station Abercorn is 5308,
        as it can be found in the following address:
        
        "http://climate.weather.gc.ca/climateData/dailydata_e.html?timeframe=
         2&Prov=QUE&StationID=5308&dlyRange=1950-12-01|1985-01-31&Year=
         1985&Month=1&Day=01"
        '''
    #===========================================================================
        
        self.staName_display.clear()
        self.staList = []        
        station_list_path = (self.parent.what_pref.project_dir + 
                             '/weather_stations.lst')
                                      
        # Force the creation of a new "weather_station.lst" file
        if not path.exists(station_list_path):
            self.parent.what_pref.load_pref_file()
            
        reader = open(station_list_path,'rb')
        reader = csv.reader(reader, delimiter='\t')
        reader = list(reader)
        
    #--------------------------------------------------- CHECK LIST VERSION ----
        
        # Check if the list is from an older version, and update it if yes
        header = ['staName', 'stationId', 'StartYear', 'EndYear', 'Province',
                  'ClimateID', 'Proximity (km)']
        
        nCONFG, nPARA = np.shape(reader)         
        if nPARA < len(header):
            print 'This list is from an older version of WHAT.'
            print 'Converting to new format.'
            
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                                                        
            self.parent.write2console('''<font color=black>
                                           Converting weather station list to
                                           a more recent format. Please wait...
                                         </font>''')
            QtGui.QApplication.processEvents()
            QtGui.QApplication.processEvents()
            
            nMissing = len(header) - nPARA
            
            col2add = np.zeros((nCONFG, nMissing)).astype(int)
            col2add = col2add.astype(str)
            
            reader = np.hstack((reader, col2add))
            reader[0] = header
            
            if nPARA < 6:
                for i in range(nCONFG-1):
                    Prov = reader[i+1, 4]
                    stationId = reader[i+1, 1]
                    reader[i+1, 5] = envirocan.get_climate_ID(Prov, stationId)
            
            #---- Save List ----
            
            with open(station_list_path, 'wb') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(reader)
    
    #----------------------------------------------------------- LOAD TO UI ----
    
        if len(reader) > 1:
            
            self.parent.write2console('''<font color=black>
                                           Weather station list loaded 
                                           successfully.
                                         </font>''')
                                         
            #----- Enable and Refresh UI ----
                                         
            self.staName_display.setEnabled(True)
            self.yStart_edit.setEnabled(True)
            self.yEnd_edit.setEnabled(True)
            
            self.staList = np.array(reader[1:])
            self.staName_display.addItems(self.staList[:, 0])
                                         
        else: 
            
            self.parent.write2console('''<font color=red>
                                           Weather Station list is empty.
                                         </font>''')
        
            #----- Disable UI ----
        
            self.staName_display.setEnabled(False)
            self.yStart_edit.setEnabled(False)
            self.yStart_edit.setRange(0, 1)
            self.yStart_edit.setValue(0)
            self.yEnd_edit.setEnabled(False)
            self.yEnd_edit.setRange(0, 1)
            self.yEnd_edit.setValue(0)
            
        QtGui.QApplication.restoreOverrideCursor()
        
    #=========================================================================== 
    def staName_isChanged(self):
        '''
        The following method updates the fields StationId and Years when the 
        station name is changed by the user. It is called by the event
        <self.staName_display.currentIndexChanged>.
        '''
    #===========================================================================
        
        sta_index = self.staName_display.currentIndex()
        
        year_start = int(self.staList[sta_index, 2])
        year_end = int(self.staList[sta_index, 3])
        
        self.yStart_edit.setRange(year_start, year_end)
        self.yEnd_edit.setRange(year_start, year_end)
        
        self.yStart_edit.setValue(year_start)
        self.yEnd_edit.setValue(year_end)
        
    #===========================================================================
    def select_raw_files(self):
        '''
        This method is called by the event <btn_select.clicked.connect>.
        It allows the user to select a group of raw data files belonging to a
        given meteorological station in order to concatenate them into a single
        file with the method <concatenate_and_display>.
        '''
    #===========================================================================
        
        dialog_fir = self.parent.what_pref.project_dir + '/Meteo/Raw'
        
        fname, _ = QtGui.QFileDialog.getOpenFileNames(self, 'Open files', 
                                                      dialog_fir, '*.csv')
        if fname:
           self.concatenate_and_display(fname)           
        
    #===========================================================================      
    def concatenate_and_display(self, fname):              
    # <concatenate_and_display> handles the concatenation process of raw data 
    # files and display the results in the <merge_stats_display> widget. 
    # 
    # It is started either from the method <select_raw_files> or by the event
    # <dwnl_rawfiles.MergeSignal> that is emitted after the
    # downloading of a serie of raw data files is completed. 
    #===========================================================================
        
        self.MergeOutput, LOG, COMNT = concatenate(fname)
        
        StaName = self.MergeOutput[0, 1]
        YearStart = self.MergeOutput[8, 0][:4]
        YearEnd = self.MergeOutput[-1, 0][:4]
        climateID = self.MergeOutput[5, 1]
        
        self.merge_stats_display.setText(LOG)      
        self.parent.write2console('<font color=black>Raw data files ' +
                                  'concatened successfully for station ' + 
                                  StaName +'</font>')  
                                  
        if COMNT:
        # A comment is issued only when all raw data files do not belong to
        # the same weather station. 
            self.parent.write2console(COMNT)
        
        if self.saveAuto_checkbox.isChecked():
            
            # Check if the characters "/" or "\" are present in the station 
            # name and replace these characters by "-" if applicable.
            intab = "/\\"
            outtab = "--"
            trantab = maketrans(intab, outtab)
            StaName = StaName.translate(trantab)
            
            project_dir = self.parent.what_pref.project_dir
            save_dir = project_dir + '/Meteo/Input/'
            if not path.exists(save_dir):
                makedirs(save_dir)
                
            filename = '%s (%s)_%s-%s.csv' % (StaName, climateID,
                                              YearStart, YearEnd)
            fname = save_dir + filename
            
            self.save_concatened_data(fname)            
        
    #===========================================================================        
    def select_concatened_save_path(self):
        '''        
        <select_concatened_save_path> is called by the event <btn_save.clicked>.
        It allows the user to select a path for the file in which the 
        concatened data are going to be saved.
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
            
            project_dir = self.parent.what_pref.project_dir
            filename = '%s (%s)_%s-%s.csv' % (StaName, climateID,
                                              YearStart, YearEnd)
            dialog_dir = project_dir + '/Meteo/Input/' + filename
                          
            fname, ftype = QtGui.QFileDialog.getSaveFileName(
                                         self, 'Save file', dialog_dir, '*.csv')
            
            if fname:                
                self.save_concatened_data(fname)    
    
    #===========================================================================         
    def save_concatened_data(self, fname):  
        """
        <save_concatened_data> saves the concatened data into a single csv file.
    
        It is started from the method <select_concatened_save_path> or the 
        method <concatenate_and_display> if <self.saveAuto_checkbox.isChecked>.
        """
    #===========================================================================                

#        if not path.exists(dirname):
#        makedirs(dirname)
        
        with open(fname, 'wb') as f:
            writer = csv.writer(f,delimiter='\t')
            writer.writerows(self.MergeOutput)
            
        self.parent.write2console('<font color=black>Concatened data ' + 
                                  'saved in: ' + fname + '</font>')   
    
    #===========================================================================
    def fetch_start_and_stop(self):
        """
        This method is started from the event "self.btn_get.clicked".
        It starts the downloading process of the raw data files.
        
        Also, this method manages the stopping of the downloading process
        and the state of the "btn_get". Right before the downloading
        process is started with "self.dwnl_rawfiles.start()", the text and
        icon of "btn_get" is changed to look like a stop button. If "btn_get" 
        is clicked again by the user during the downloading process, its state 
        reverts back to its original 'Get Data' display. In addition the value
        of the "STOP" flag is forced to True in the download Thread.
 
        When the working function "fetch" sees this, the downloading loop is
        broken, and so is also the downloading process of raw data files.
        """
    #===========================================================================
        
        if self.dwnl_rawfiles.isRunning():
            
            # Stop the Download process and reset UI
            
            self.dwnl_rawfiles.STOP = True

            self.btn_get.setIcon(iconDB.download)
        
            self.staName_display.setEnabled(True)
            self.yStart_edit.setEnabled(True)
            self.yEnd_edit.setEnabled(True)
            
        else:
            
        #------------------------------------------------- Check for Errors ----
            
            ERRFLAG = False # Flag to check if there is errors before starting
                            # the downloading process.
            
            if self.staName_display.currentIndex() == -1:
                
                ERRFLAG = True
                self.msgBox.setText('Station list is empty.')
                self.msgBox.exec_()
        
        #------------------------------------------------- Start the Thread ----
        
            if ERRFLAG == False:
                
                #----- Update UI -----
                
                self.staName_display.setEnabled(False)
                self.yStart_edit.setEnabled(False)
                self.yEnd_edit.setEnabled(False)
                
                self.btn_get.setIcon(iconDB.stop)
                
                #----- Push input values to the class instance -----
                
                sta_index = self.staName_display.currentIndex()
                
                stationID = self.staList[sta_index, 1]
                self.dwnl_rawfiles.stationID = stationID
                
                climateID = self.staList[sta_index, 5]
                self.dwnl_rawfiles.climateID = climateID
                
                dirname = self.parent.what_pref.project_dir + '/Meteo/Raw'           
                self.dwnl_rawfiles.dirname = dirname                
                 
                #----- Start Download -----
                 
                self.dwnl_rawfiles.start()
    
    #===========================================================================
    def download_is_finished(self, fname):
        '''   
        This method is started by the signal <MergeSignal> that is emitted after
        a downloading task has ended. The signal contains the list of raw
        data files that has been downloaded.
        '''
    #===========================================================================    
        
        # Reset UI and start the concatenation of the data.         
        
        self.staName_display.setEnabled(True)
        self.yStart_edit.setEnabled(True)
        self.yEnd_edit.setEnabled(True)
        self.btn_get.setText(labelDB.btn_get_text)
        self.btn_get.setIcon(iconDB.download)
        
        if len(fname) > 0:
            self.concatenate_and_display(fname)
    
    #===========================================================================       
    def setProgBarSignal(self, progress):
    # <setProgBarSignal> updates the value of the progression bar widget
    # of the main window in order to display the raw data files downloading
    # progress. The method is called by the event signal 
    # <self.dwnl_rawfiles.ProgBarSignal> that is being emitted by the 
    # instance <self.dwnl_rawfiles> of the <DownloadRawDataFiles>
    # thread class.
    #===========================================================================
    
        self.parent.pbar.setValue(progress)

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
        
    #----------------------------------------------------------- GRID LEFT -----
        
        #----- Subgrid Target Station -----
        
        target_station_label = QtGui.QLabel('<b>Target Station :</b>')
        self.target_station = QtGui.QComboBox()
        self.target_station_info = QtGui.QTextEdit()
        self.target_station_info.setReadOnly(True)
        self.target_station_info.setMaximumHeight(110)
        self.btn3 = QtGui.QToolButton()
        self.btn3.setIcon(iconDB.refresh)
        self.btn3.setAutoRaise(True)
        
        subgrid_widget6 = (QtGui.QWidget())
                     
        subgrid6 = QtGui.QGridLayout()
                
        row = 0
        subgrid6.addWidget(target_station_label, row, 0, 1, 2)
        row = 1
        subgrid6.addWidget(self.target_station, row, 0)
        subgrid6.addWidget(self.btn3, row, 1)
        row = 2
        subgrid6.addWidget(self.target_station_info, row, 0, 1, 2)

        # Total number of columns = 2
        
        subgrid6.setSpacing(5)
        subgrid6.setColumnStretch(0, 500)
        subgrid_widget6.setLayout(subgrid6)
        subgrid6.setContentsMargins(0, 0, 0, 10) #Left, Top, Right, Bottom
        
       #----- SubGrid Cutoff Values -----
        
        Cutoff_title = QtGui.QLabel('<b>Stations Selection Criteria :</b>')
        
        Nmax_label = QtGui.QLabel('Maximum number of stations')
        self.Nmax = QtGui.QSpinBox ()
        self.Nmax.setRange(0, 99)
        self.Nmax.setSingleStep(1)
        self.Nmax.setValue(4)
        distlimit_label = QtGui.QLabel(labelDB.distlimit_text)
        distlimit_label.setToolTip(labelDB.distlimit_help)
        self.distlimit = QtGui.QSpinBox()
        self.distlimit.setRange(-1, 9999)
        self.distlimit.setSingleStep(1)
        self.distlimit.setValue(100)
        self.distlimit.setToolTip(labelDB.distlimit_help)
        altlimit_label = QtGui.QLabel(labelDB.altlimit_text)
        altlimit_label.setToolTip(labelDB.altlimit_help)
        self.altlimit = QtGui.QSpinBox()
        self.altlimit.setRange(-1, 9999)
        self.altlimit.setSingleStep(1)
        self.altlimit.setValue(350)
        self.altlimit.setToolTip(labelDB.altlimit_help)
            
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
         
        #----- SubGrid Regression Model Selection -----
        
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
        
        subgrid_widget3=(QtGui.QWidget())
        subgrid3 = QtGui.QGridLayout()
        subgrid3.setSpacing(10)
        row = 0
        subgrid3.addWidget(regression_model_label, row, 0)
        row = 1
        subgrid3.addWidget(regression_model, row, 0)
        
        # Total number of columns = 1
        
        subgrid3.setContentsMargins(0, 10, 0, 10) #Left, Top, Right, Bottom
        subgrid_widget3.setLayout(subgrid3)
        
        #----- SubGrid Gapfill Dates -----
        
        label_Dates_Title = QtGui.QLabel('<b>Gap Fill Data Record :</b>')
        label_From = QtGui.QLabel('From :  ')
        self.date_start_widget = QtGui.QDateEdit()
        self.date_start_widget.setDisplayFormat('dd / MM / yyyy')
        self.date_start_widget.setEnabled(False)
        label_To = QtGui.QLabel('To :  ')
        self.date_end_widget = QtGui.QDateEdit()
        self.date_end_widget.setEnabled(False)
        self.date_end_widget.setDisplayFormat('dd / MM / yyyy')
        
        subgrid_widget5=(QtGui.QWidget())
                     
        subgrid5 = QtGui.QGridLayout()
        subgrid5.setSpacing(10)
        
        row = 0
        subgrid5.addWidget(label_Dates_Title, row, 0, 1, 3)
        row = 1
        subgrid5.addWidget(label_From, row, 1)
        subgrid5.addWidget(self.date_start_widget, row, 2)
        row = 2
        subgrid5.addWidget(label_To, row, 1)  
        subgrid5.addWidget(self.date_end_widget, row, 2)        
        
        # Total number of columns = 3
        
        subgrid5.setColumnStretch(4, 500)
        subgrid5.setColumnStretch(0, 500)
        subgrid_widget5.setLayout(subgrid5)
        subgrid5.setContentsMargins(0, 10, 0, 0) #Left, Top, Right, Bottom
        
        #----- ASSEMBLING SUBGRIDS FOR GRID LEFT -----        
         
        grid_LEFT = QtGui.QGridLayout()
        LEFT_widget = QtGui.QFrame()
        LEFT_widget.setFrameStyle(StyleDB.frame)                                  

        seprator1 = QtGui.QFrame()
        seprator1.setFrameStyle(StyleDB.HLine)
        seprator2 = QtGui.QFrame()
        seprator2.setFrameStyle(StyleDB.HLine)        
        seprator3 = QtGui.QFrame()
        seprator3.setFrameStyle(StyleDB.HLine)
        
        row = 0 
        grid_LEFT.addWidget(subgrid_widget6, row, 0) # SubGrid 6: Target Sta.
        row += 1
        grid_LEFT.addWidget(seprator1, row, 0)       # Separator
        row += 1
        grid_LEFT.addWidget(subgrid_widget2, row, 0) # SubGrid 2: Cutoff Values
        row += 1  
        grid_LEFT.addWidget(seprator2, row, 0)       # Separator
        row += 1 
        grid_LEFT.addWidget(subgrid_widget3, row, 0) # SubGrid 3: MLRM Selection
        row += 1
        grid_LEFT.addWidget(seprator3, row, 0)       # Separator
        row += 1
        grid_LEFT.addWidget(subgrid_widget5, row, 0) # SubGrid 5: GapFill Dates
        row += 1
        grid_LEFT.setRowStretch(row, 500)
        
        # Total number of columns = 1
        
        LEFT_widget.setLayout(grid_LEFT)
        grid_LEFT.setContentsMargins(10, 10, 10, 10) #Left, Top, Right, Bottom
        
   #-------------------------------------------------------------GRID RIGHT-----
       
        self.FillTextBox = QtGui.QTextEdit()
        self.FillTextBox.setReadOnly(True)
        self.FillTextBox.setFrameStyle(0)
        self.FillTextBox.setFrameStyle(StyleDB.frame)
        
        self.btn_fill = QtGui.QPushButton(labelDB.btn_fill_text)
        self.btn_fill.setIcon(iconDB.play)
        self.btn_fill.setToolTip(labelDB.btn_fill_help)        
        self.btn_fill_all = QtGui.QPushButton(labelDB.btn_fill_all_text)
        self.btn_fill_all.setToolTip(labelDB.btn_fill_all_help)
        self.btn_fill_all.setIcon(iconDB.forward)
        
        grid_RIGHT = QtGui.QGridLayout()
        RIGHT_widget = QtGui.QFrame()
#        RIGHT_widget.setFrameStyle(StyleDB.frame)
        RIGHT_widget.setFrameStyle(0)
        
        row = 0
        grid_RIGHT.addWidget(self.FillTextBox, row, 0, 1, 3)
        row += 1
        grid_RIGHT.addWidget(self.btn_fill, row, 1)
        grid_RIGHT.addWidget(self.btn_fill_all, row, 2)
        
        # Total number of columns = 3        
        
        grid_RIGHT.setRowStretch(0, 500)
        grid_RIGHT.setColumnStretch(0, 500)
        grid_RIGHT.setContentsMargins(0, 0, 0, 0) #Left, Top, Right, Bottom
                        
        RIGHT_widget.setLayout(grid_RIGHT)
                 
    #-------------------------------------------------------------GRID MAIN-----
       
        grid_MAIN = QtGui.QGridLayout()
        grid_MAIN.setSpacing(15)
        
        row = 0
        grid_MAIN.addWidget(RIGHT_widget, row, 1)
        grid_MAIN.addWidget(LEFT_widget, row, 0)
        
        # Total number of columns = 3
        
        grid_MAIN.setColumnStretch(1, 500)
        grid_MAIN.setColumnMinimumWidth(1, 700)
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
        Initiale the loading of Weater Data Files contained in the 
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
        
        input_folder = self.parent.what_pref.project_dir + '/Meteo/Input'
        
        if path.exists(input_folder):            
            
            # Generate a list of data file paths.            
            Sta_path = []
            for files in listdir(input_folder):
                if files.endswith(".csv"):
                    Sta_path.append(input_folder + '/' + files)
            
            if len(Sta_path) > 0:
                self.WEATHER.load_and_format_data(Sta_path)
                self.WEATHER.generate_summary(self.parent.what_pref.project_dir)
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
        
        if self.fill_all_inProgress == True:
            
            self.fill_all_inProgress = False     

            # Reset UI state
            self.btn_fill_all.setIcon(iconDB.forward)        
            self.target_station.setEnabled(True)
            self.btn_fill.setEnabled(True)
            self.parent.btn_project_dir.setEnabled(True)
            self.btn3.setEnabled(True)
            self.parent.project_dir_display.setEnabled(True)
            
            QtGui.QApplication.processEvents()
            
            if self.fillworker.isRunning():
            # Pass a flag to the worker in order to force him to stop.
                self.fillworker.STOP = True
            else:
                'Do nothing. Worker is not running.'
                
        elif self.fill_all_inProgress == False:
            
            FLAG = False # Flag used to check if there is errors in the settings
            
            y = self.date_start_widget.date().year()
            m = self.date_start_widget.date().month()
            d = self.date_start_widget.date().month()
            time_start = xldate_from_date_tuple((y, m, d), 0)
     
            y = self.date_end_widget.date().year()
            m = self.date_end_widget.date().month()
            d = self.date_end_widget.date().day()
            time_end = xldate_from_date_tuple((y, m, d), 0)
        
        #-------------------------------------------------CHECKS FOR ERRORS-----
            
            if len(self.WEATHER.STANAME) == 0:
                FLAG = True
                self.msgBox.setText('<b>Data directory</b> is empty.')
                self.msgBox.exec_()
                print 'No target station selected.'
            elif time_start > time_end:
                FLAG = True
                self.msgBox.setText('<b>Fill and Save Data</b> start date is ' +
                                    'set to a later time than the end date.')
                self.msgBox.exec_()
                print 'The time period is invalid.'
            
        #------------------------------------------------START THREAD IF OK-----
           
            if FLAG == True:
                'Do nothing, something is wrong.'
            else:
                self.fill_all_inProgress = True
                
                # Update UI
                self.btn_fill_all.setIcon(iconDB.stop)
                self.target_station.setEnabled(False)
                self.btn_fill.setEnabled(False)
                self.parent.btn_project_dir.setEnabled(False)
                self.btn3.setEnabled(False)
                self.parent.project_dir_display.setEnabled(False)
                
                self.CORRFLAG = 'off' 
                self.target_station.setCurrentIndex(0)
                self.TARGET.index = self.target_station.currentIndex()
                self.TARGET.name = \
                        self.WEATHER.STANAME[self.target_station.currentIndex()]
                self.CORRFLAG = 'on'
                
                QtGui.QApplication.processEvents()                
                
                self.correlation_UI()
                
                # Pass information to the worker.
                self.fillworker.project_dir = self.parent.what_pref.project_dir
                
                self.fillworker.time_start = time_start
                self.fillworker.time_end = time_end                       
                
                self.fillworker.WEATHER = self.WEATHER
                self.fillworker.TARGET = self.TARGET
                                            
                self.fillworker.regression_mode = \
                                                self.RMSE_regression.isChecked()
            
                # Start the gapfilling procedure.
                self.fillworker.start()
        
    #===========================================================================                                          
    def fill_is_clicked(self):
    # Method that handles the gapfilling process on the UI side.
    #
    # check if there is anything wrong with the parameters defined by the user
    # before starting the fill process and issue warning if anything is wrong.
    #===========================================================================
        if self.fillworker.isRunning():
            
            # Reset UI.
            self.btn_fill.setIcon(iconDB.play)
            self.target_station.setEnabled(True)
            self.btn_fill_all.setEnabled(True)
            QtGui.QApplication.processEvents()
            
            # Pass a flag to the worker in order to force him to stop.
            self.fillworker.STOP = True
            
        else:
            FLAG = False
            
            y = self.date_start_widget.date().year()
            m = self.date_start_widget.date().month()
            d = self.date_start_widget.date().month()
            time_start = xldate_from_date_tuple((y, m, d), 0)
     
            y = self.date_end_widget.date().year()
            m = self.date_end_widget.date().month()
            d = self.date_end_widget.date().day()
            time_end = xldate_from_date_tuple((y, m, d), 0)
            
        #------------------------------------------------------------CHECKS-----
            
            if self.target_station.currentIndex() == -1:
                FLAG = True
                self.msgBox.setText('No <b>Target station</b> is currently ' +
                                    'selected.')
                self.msgBox.exec_()
                print 'No target station selected.'
            elif time_start > time_end:
                FLAG = True
                self.msgBox.setText('<b>Gap Fill Data Record</b> start date is ' +
                                    'set to a later time than the end date.')
                self.msgBox.exec_()
                print 'The time period is invalid.'
            
        #------------------------------------------------START THREAD IF OK-----
                                       
            if FLAG == True:
                'Do nothing, something is wrong.'
            else:
                # Update UI.
                self.btn_fill.setIcon(iconDB.stop)
                self.target_station.setEnabled(False)
                self.btn_fill_all.setEnabled(False)
                
                # Pass information to the worker.
                self.fillworker.project_dir = self.parent.what_pref.project_dir
                
                self.fillworker.time_start = time_start
                self.fillworker.time_end = time_end                       
                
                self.fillworker.WEATHER = self.WEATHER
                self.fillworker.TARGET = self.TARGET
                                            
                self.fillworker.regression_mode = \
                                                self.RMSE_regression.isChecked()
            
                # Start the gapfilling procedure.
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
            self.parent.btn_project_dir.setEnabled(True)
            self.btn3.setEnabled(True)
            self.parent.project_dir_display.setEnabled(True)


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
        
        grid.addWidget(AboutTextBox, 0, 0)
        
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
                        jean-sebastien.gosselin@ete.inrs.ca
                        </p>
                        <p align="center" style="margin-right:150px; 
                        margin-left:150px">
                        <br><br><br>%s is free software: 
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
                        <br><br><br>
                        </p>
                        <p align="right" style="margin-right:150px">
                        Last modification: %s </p>''' % (software_version,
                        software_version, last_modification)
        
        AboutTextBox.setText(about_text)

       
################################################################################
#                                                                           
#                             @SECTION WORKER METEO                             
#                                                                          
################################################################################
        
        
#===============================================================================        
class DownloadRawDataFiles(QtCore.QThread):        
    '''
    This thread is called when the "Get Data" button of the Tab 
    "Download Data" is clicked on. It downloads the raw data files from
    www.climate.weather.gc.ca and saves them automatically in
    <Project_directory>/Meteo/Raw/<station_name>.

    New in 4.0.6: Raw data files that already exists in the Raw directory
                  won't be downloaded again from the server.
    
    ---- Input ----

    self.STOP = Flag that is used to stop the thread from the UI side.
    
    ---- Output ----
    
    self.ERRFLAG = Flag for the download of files - np.arrays
                   0 -> File downloaded successfully
                   1 -> Problem downloading the file
                   3 -> File NOT downloaded because it already exists
    '''
#===============================================================================   
    
    MergeSignal = QtCore.Signal(list)
    ProgBarSignal = QtCore.Signal(int)
    ConsoleSignal = QtCore.Signal(str)
    
    def __init__(self, parent):
        super(DownloadRawDataFiles, self).__init__(parent)
        self.parent = parent
        
        self.STOP = False  
        self.dirname = [] # Directory where the downloaded files are saved
        self.ERRFLAG = []
        self.stationID = []
        self.climateID = [] # Unique identifier for the station
          
    def run(self): 
        
    #---------------------------------------------------------------- INIT -----
        
        staID = self.stationID   
        yr_start = self.parent.yStart_edit.value()
        yr_end = self.parent.yEnd_edit.value()
        StaName = self.parent.staName_display.currentText()
        climateID = self.climateID
        
        self.ERRFLAG = np.ones(yr_end - yr_start + 1)
             
        self.ConsoleSignal.emit(
        '''<font color=black>Downloading data from </font>
           <font color=blue>www.climate.weather.gc.ca</font>
           <font color=black> for station %s</font>''' % StaName)
        self.ProgBarSignal.emit(0)         
        
        self.dirname += '/%s (%s)' % (StaName, climateID)
        if not path.exists(self.dirname):
            makedirs(self.dirname)
            
        #-------------------------------------------------------- DOWNLOAD -----
            
        # Data are downloaded on a yearly basis from yStart to yEnd
         
        fname4merge = [] # list of paths of the yearly raw data files that will
                         # be pass to contatenate and merge function.
        i = 0
        for year in range(yr_start, yr_end+1):
            
            if self.STOP == True : # User stopped the downloading process.                
                break
            
            #----- File and URL Paths -----
            
            fname = self.dirname + '/eng-daily-0101%s-1231%s.csv' % (year, year) 
            
            url = ('http://climate.weather.gc.ca/climateData/bulkdata_e.html?' +
                   'format=csv&stationID=' + str(staID) + '&Year=' + str(year) +
                   '&Month=1&Day=1&timeframe=2&submit=Download+Data')
            
            #----- Download Data For That Year -----
            
            if path.exists(fname):
                
                # If the file was downloaded in the same year that of the data
                # record, data will be downloaded again in case the data series
                # was not complete.
                
                myear = path.getmtime(fname) # Year of file last modification
                myear = gmtime(myear)[0]
                
                if myear == year:
                    self.ERRFLAG[i] = self.dwndfile(url, fname)
                else:
                    self.ERRFLAG[i] = 3
                    print 'Not downloading: Raw Data File already exists.'
                    
            else:
                self.ERRFLAG[i] = self.dwndfile(url, fname)

            #----- Update UI -----
            
            progress = (year - yr_start + 1.) / (yr_end + 1 - yr_start) * 100
            self.ProgBarSignal.emit(int(progress))
            
            if self.ERRFLAG[i] == 1:
                
                self.ConsoleSignal.emit(
                '''<font color=red>There was a problem downloading the data 
                     of station %s for year %d.
                   </font>''' % (StaName, year))                

            elif self.ERRFLAG[i] == 0:
                
                self.ConsoleSignal.emit(
                '''<font color=black>Weather data for station %s downloaded
                     successfully for year %d.</font>''' % (StaName, year))
                fname4merge.append(fname)
                
            elif self.ERRFLAG[i] == 3:
                
                self.ConsoleSignal.emit(
                '''<font color=green>A weather data file already existed for
                     station %s for year %d. Downloading is skipped.
                   </font>''' % (StaName, year))
                fname4merge.append(fname)
                            
            i += 1
            
    #--------------------------------------------------------- End of Task -----
        
        if self.STOP == True:
            
            self.STOP = False
            self.ConsoleSignal.emit('''<font color=red>Downloading process for
                                         station %s stopped.
                                       </font>''' % StaName)
        else:
                 
            self.MergeSignal.emit(fname4merge)
            self.ProgBarSignal.emit(0)
                
    def dwndfile(self, url, fname):
        
        # http://stackoverflow.com/questions/4028697
        # https://docs.python.org/3/howto/urllib2.html
        
        ERRFLAG = 0
        
        try:
            f = urlopen(url)
            print "downloading " + fname

            # write downlwaded content to local file
            with open(fname, "wb") as local_file:
                local_file.write(f.read())
                
        except URLError as e:
            
            ERRFLAG = 1
            
            if hasattr(e, 'reason'):
                print('Failed to reach a server.')
                print('Reason: ', e.reason)
                
            elif hasattr(e, 'code'):
                print('The server couldn\'t fulfill the request.')
                print('Error code: ', e.code)
                
        return ERRFLAG
            
#===============================================================================        
def concatenate(fname):    
#===============================================================================

    fname = np.sort(fname)     # list of the raw data file paths
   
    COLN = (1, 2, 3, 5, 7, 9, 19) # columns of the raw data files to extract
    #year, month, day, Tmax, Tmin, Tmean, Ptot
    
    ALLDATA = np.zeros((0,len(COLN))) # matrix containing all the data
    StaName = np.zeros(len(fname)).astype('str')  # station names
    StaMatch = np.zeros(len(fname)).astype('str') # station match 
    for i in range(len(fname)):
        reader = open(fname[i],'rb')
        reader = csv.reader(reader, delimiter=',')
        reader = list(reader)
                  
        StaName[i] =  reader[0][1]         
        StaMatch[i] = StaName[0]==StaName[i]
        
        row_data_start = 0
        fieldSearch = 'None'
        while fieldSearch != 'Date/Time':
            try:
                fieldSearch = reader[row_data_start][0]
            except:
                pass
            
            row_data_start += 1
            
            if row_data_start > 50:
                print 'There is a compatibility problem with the data.'
                print 'Please, write at jnsebgosselin@gmail.com'
                break
            
        DATA = np.array(reader[row_data_start:])
        DATA = DATA[:, COLN]
        DATA[DATA == ''] = 'nan'
        DATA = DATA.astype('float')
        
        ALLDATA = np.vstack((ALLDATA, DATA)) 
    
    FIELDS = ['Temp. Max.', 'Temp. Min.', 'Temp. Avg.', 'Prec. Tot.', 'Total']
    
    ndata = float(len(ALLDATA[:, 0]))
    Ndata = float(len(ALLDATA[:, 0]) * 4) 
    
    LOG = '''
          <p>
            Number of Missing Data for Years %d to %d for station %s :
          </p>
          <br>
          <table border="0" cellpadding="2" cellspacing="0" align="left">
          ''' % (np.min(ALLDATA[:,0]), np.max(ALLDATA[:,0]), StaName[0])
    for i in range(0, len(FIELDS)-1):
         nonan = sum(np.isnan(ALLDATA[:, i+3]))
         LOG += '''
                <tr>
                  <td width=60></td>
                  <td align="left">%s</td>
                  <td align="left" width=20>:</td>          
                  <td align="right">%d/%d</td>
                  <td align="center">(%0.1f%%)</td>
                </tr>
                ''' % (FIELDS[i], nonan, ndata, nonan/ndata*100)
               
    nonan = np.sum(np.isnan(ALLDATA[:, 3:]))
    LOG += '''
             <tr></tr>
             <tr>
               <td></td>
               <td align="left">%s</td>
               <td align="left" width=20>:</td>
               <td align="right">%d/%d</td>
               <td align="center">(%0.1f%%)</td>
             </tr>
           </table>
           ''' % (FIELDS[-1], nonan, Ndata, nonan/Ndata*100)
    
    HEADER = np.zeros((8, len(COLN))).astype('str')
    HEADER[:] = ''
    HEADER[0:6,0:2] = np.array(reader[0:6])
    HEADER[7,:] = ['Year','Month', 'Day','Max Temp (deg C)', 'Min Temp (deg C)',
                   'Mean Temp (deg C)', 'Total Precip (mm)']
    
    MergeOutput = np.vstack((HEADER, ALLDATA.astype('str'))) 
    
    if min(StaMatch) == 'True':
        COMNT = []
    else:
        COMNT = ('font color=red> WARNING: All the data files do not ' + 
                 'belong to station' + StaName[0] + '</font>')
  
    return MergeOutput, LOG, COMNT
    
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
#   row :  meteorological variables
#   colm : weather stations
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
                'Do nothing. Value will be nan by default'
        
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
    This functions is called when the <Fill and Save> button of the Tab named 
    Fill is clicked on. It is the main routine that fill the missing data
    in the weather record.
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
        # --> If True = Ordinary Least Square
        # --> If False = Least Absolute Deviations
        
        self.STOP = False # Used to stop the Thread on the UI side
        
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
        
    #----------------------------------------------------STATION HEADER INFO----
        
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
        
    #---------------------------------------------------------------------------
        
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
        
    #-------------------------------------------------CHECK CUTOFF CRITERIA-----        
        
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
    
    #---------------------------------------CHECK VARIABLE WITH ENOUGH DATA-----
        
        # NOTE: When a station does not have enough data for a given variable,
        #       its correlation coefficient is set to nan.
        
        var2fill = np.sum(~np.isnan(CORCOEF[:, :]), axis=1)
        var2fill = np.where(var2fill > 1)[0]
        
        print; print var2fill
        
        for var in range(nVAR):
            if var not in var2fill:
            
                message = ('!Variable %d/%d won''t be filled because there ' +
                           'is not enough data!') % (var+1, nVAR)
                print message
        
    #-------------------------------------------------------------FILL LOOP-----

        FLAG_nan = False # If some missing data can't be completed because 
                         # all the neighboring stations are empty, a flag is
                         # raised and a comment is issued at the end of the 
                         # completion process.
        
        nbr_nan_total = np.isnan(Y2fill[index_start:index_end+1, var2fill])
        nbr_nan_total = np.sum(nbr_nan_total)
        
        if self.full_error_analysis == False:
            progress_total = nbr_nan_total
        else:
            progress_total = len(Y2fill[:, 0]) * len(var2fill)
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
            
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            if self.STOP == True:
                self.ConsoleSignal.emit(                           
                    '''<font color=red>Completion process for station %s 
                         stopped.</font>''' % target_station_name)
                break 
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            
            message = ('Data completion for variable %d/%d in progress'
                       ) % (var+1, nVAR)
            print message
            
            colm_memory = np.array([]) # Column sequence memory matrix
            RegCoeff_memory = [] # Regression coefficient memory matrix
            RMSE_memory = []
            
            # Sort station in descending correlation coefficient order.
            # Target station index is pushed at position 0.
            Sta_index = sort_stations_correlation_order(CORCOEF[var, :])
            
            # Data for this variable are stored in a 2D matrix with data in
            # descending correlation order. Target station data serie is
            # contained at j = 0.
            YX = np.copy(DATA[:, Sta_index, var])              
            
            # Find rows where data are missing between the date limits
            # that correspond to index_start and index_end
            row_nan = np.where(np.isnan(YX[:, 0]))[0]
            row_nan = row_nan[row_nan >= index_start]
            row_nan = row_nan[row_nan <= index_end]
            it_avg = 0 # counter used in the calculation of average RMSE
                       # and NSTA values.
            
            if self.full_error_analysis == False :
                row2fill = row_nan
            else:
                row2fill = range(len(Y2fill[:, 0]))
                
            for row in row2fill:
                
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                sleep(0.000001) #If no sleep, the UI becomes whacked
                if self.STOP == True: 
                    print 'BREAK!!!!'
                    break
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                  
                # Find neighboring stations with valid entries entries at 
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
                    # sum(colm * 10**np.arange(0, 2*len(colm), 2))
                    
                    # A check is made to see if the current combination
                    # of neighboring stations has been encountered
                    # previously in the routine. Regression coefficients
                    # are calculated only once for a given neighboring
                    # station combination.
                    index_memory = np.where(colm_memory == colm_seq)[0]                                   
                    
                    if len(index_memory) == 0:
                    # First time this neighboring station combination
                    # is encountered in this routine, regression
                    # coefficients are calculated.
                    
                        colm_memory = np.append(colm_memory, colm_seq)
                    
                        # Columns of DATA for the variable VAR are sorted
                        # in descending correlation coefficient and the 
                        # information is stored in a 2D matrix (The data for 
                        # the target station are included at index j=0).
                        YXcolm = np.copy(YX)       
                        YXcolm = YXcolm[:, colm]
                        
                        # All rows containing NAN entries are removed.
                        YXcolm = YXcolm[~np.isnan(YXcolm).any(axis=1)]
                    
                        # Rows for which precipitation of the target station
                        # and all neighboring station is 0 are removed.
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
                            # my own function.
                            
                            #model = sm.OLS(Y, X) 
                            #results = model.fit()
                            #print results.params
                            
                            #model = QuantReg(Y, X)
                            #results = model.fit(q=0.5)
                            #A = results.params
                            
                    #--------------------------------------------------RMSE-----
                        
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
                                            
                #----------------------------------MISSING VALUE ESTIMATION-----
                    
                    # Calculate missing value of Y at row <row>.
                    Y_row = np.dot(A, X_row)
                    
                    # Limit precipitation based variable to positive values.
                    # This may happens when there is one or more negative 
                    # regression coefficients in A and round the results.
                    if var in (3, 4, 5):
                        Y_row = max(Y_row, 0)
                    Y_row = round(Y_row ,1)
                    
                #---------------------------------------------STORE RESULTS-----
                  
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
                
                #-----------------------------------------------END FOR ROW-----
                
            if it_avg > 0:
                AVG_RMSE[var] /= it_avg
                AVG_NSTA[var] /= it_avg
            else:
                AVG_RMSE[var] = np.nan
                AVG_NSTA[var] = np.nan
                
            print_message = ('Data completion for variable %d/%d completed'
                             ) % (var+1, nVAR)
            print print_message             
                
            #----------------------------------------------END FOR VARIABLE-----

    #----------------------------------------------------WRITE DATA TO FILE-----

        if self.STOP == True: 
        # Routine was stopped before the end. There is nothing to save. 
        
            self.STOP = False
            
        elif self.STOP == False:
                    
            self.ConsoleSignal.emit('<font color=black>Data completion ' + 
                                    'for station ' + target_station_name +
                                    ' completed</font>')
                                    
            if FLAG_nan == True:
                self.ConsoleSignal.emit(
                    '<font color=red>WARNING: Some missing data were not ' +
                    'completed because all neighboring station were empty ' +
                    'for that period</font>')
        
        #------------------------------------------INFO DATA POSTPROCESSING-----
            
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
           
        #------------------------------------------------------------HEADER-----
                  
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
            
            #------------------------------------------------LOG GENERATION-----
            
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
                nofill_percent = round(nbr_nofill / nbr_nan * 100, 1)
                fill_percent = round(nbr_fill / nbr_nan * 100, 1)
                
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
                    
        #-------------------------------------------------------- SAVE INFO ----
                                      
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
                
        #-------------------------------------------------------- SAVE DATA ----
            
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
            self.STOP = False
            
        #--------------------------------------- SAVE ERROR ANALYSIS REPORT ----
            
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
            
            #-------------------------------------------- SOME CALCULATIONS ----
                
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
# L1LinearRegression: Calculates L-1 multiple linear regression by IRLS
# (Iterative reweighted least squares)
# 
# B = L1LinearRegression(Y,X)
#
# B = discovered linear coefficients 
# X = independent variables 
# Y = dependent variable 
# 
# Note 1: An intercept term is NOT assumed (need to append a unit column if
#         needed). 
# Note 2: a.k.a. LAD, LAE, LAR, LAV, least absolute, etc. regression 
#
# SOURCE:
# This function is originally from a Matlab code written by Will Dwinnell
# www.matlabdatamining.blogspot.ca/2007/10/l-1-linear-regression.html
# Last accessed on 21/07/2014
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
    
    
################################################################################
#                                                                           
#                   @SECTION LANGUAGE, ICONS AND PREFERENCES
#                                                                          
################################################################################    

# http://stackoverflow.com/questions/78799

class LabelDataBase(): # Default language is English.
    
    
    def __init__(self, language): #------------------------------- ENGLISH -----
        
        self.text = self.Text(language)
              
        #----- TAB DOWNLOAD DATA-----
        
        self.title_download = ('<font size="4"><b>Download Data : </b></font>')
        self.title_concatenate = (
            '''<font size="4">
                 <b>Concatenate and Format Raw Data Files :</b>
               </font>''')
                
        self.btn_load_text = 'Load'        
        self.btn_get_text = 'Get Data'                              
        self.btn_get_all_text = 'Get All'
        self.btn_get_all_help = (
            '''<p>Download weather data for all the weather station in the 
                 current list for the specified time period.</p>''')
              
        #----- TAB FILL DATA -----
        
        self.btn_fill_text = 'Fill'
        self.btn_fill_help = (        
            '''<p>Fill the gaps in the weather data record of the selected
                 target station.</p>''')
           
        self.btn_fill_all_text = 'Fill All'
        self.btn_fill_all_help = (
            '''<p>Fill the gaps in all the weather data records found in the
                 <i>Data Directory</i>.</p>''')
        
        self.distlimit_text = 'Cutoff distance (km)'
        self.distlimit_help = (                
            '''<p>Distance limit beyond which neighboring stations are excluded
                 from the gapfilling procedure.</p>
               <p>This condition is ignored if set to a value of -1.</p>''')
        
        self.altlimit_text = 'Cutoff altitude difference (m)'
        self.altlimit_help = (
            '''<p>Altitude difference limit over which neighboring stations are
                 excluded from the gapfilling procedure.</p>
               <p>This condition is ignored if set to a value of -1.</p>''')
         
        if language == 'French': #--------------------------------- FRENCH -----
                       
            #----- TAB DOWNLOAD DATA -----    
            
            self.title_download = (
                u'''<font size="4">
                      <b>Téléchargement des données : </b>
                    </font>''')
                                      
            self.title_concatenate = (
                u'''<font size="4">
                      <b>Mise en commun et mise en forme des données :</b>
                    </font>''')
                
    class Text():
        
        def __init__(self, language): #--------------------------- ENGLISH -----
        
            self.TAB1 = 'Download Data'
            self.TAB2 = 'Fill Data'
            self.TAB3 = 'Hydrograph'
            self.TAB4 = 'About'
            
            if language == 'French': #----------------------------- FRENCH -----

                self.TAB1 = u'Télécharger'
                self.TAB2 = u'Combler les données'
                self.TAB3 = u'Hydrogramme'
                self.TAB4 = u'À propos'

#===============================================================================    
class WHATPref():
#===============================================================================

    
    def __init__(self, parent=None):
        
        # now = datetime.now()
        # now = (now.year, now.month, now.day)
        # self.project_dir = getcwd() + '/Projects/New_%d%d%d' % now
        self.project_dir = getcwd() + '/../Projects/Example'
        self.first_startup = 0
    
    def save_pref_file(self):
            
        fcontent = [['Project Dir:', self.project_dir]]
       
        with open('WHAT.pref', 'wb') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(fcontent)
            
    def load_pref_file(self):
            
        if not path.exists('WHAT.pref'):            
            # Default values will be kept and a new .pref file will be
            # generated
            
            print 'No "WHAT.pref" file found. A new one has been created.'
        
            self.save_pref_file()
        
        else:
            
            reader = open('WHAT.pref', 'rb')
            reader = csv.reader(reader, delimiter='\t')
            reader = list(reader)
            
            self.project_dir = reader[0][1]
        
        #----- System folder hierarchy -----
        
        if not path.exists( self.project_dir + '/Meteo/Raw'):
            makedirs(self.project_dir + '/Meteo/Raw')
        if not path.exists( self.project_dir + '/Meteo/Input'):
            makedirs(self.project_dir + '/Meteo/Input')
        if not path.exists( self.project_dir + '/Meteo/Output'):
            makedirs(self.project_dir + '/Meteo/Output')
        if not path.exists( self.project_dir + '/Water Levels'):
            makedirs(self.project_dir + '/Water Levels')
            
        #---- waterlvl_manual_measurements.xls ----
        
        fname = self.project_dir + '/waterlvl_manual_measurements.xls'
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
            
#            fcontent = [['Well_ID', 'Time (days)', 'Obs. (mbgs)']]
#            with open(fname, 'wb') as f:
#                writer = csv.writer(f, delimiter='\t')
#                writer.writerows(fcontent)
            
        #---- weather_stations.lst ----
                
        fname = self.project_dir + '/weather_stations.lst'
        if not path.exists(fname):
            
            msg = ('No "weather_stations.lst" file found. ' +
                   'A new one has been created.')
            print msg
            
            fcontent = [['staName', 'stationId', 'StartYear', 'EndYear',
                         'Province', 'ClimateID', 'Proximity (km)']]
            
            with open(fname, 'wb') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(fcontent)
                               
       
################################################################################
#                                                                           
#                              MAIN FUNCTION
#                                                                          
################################################################################       

        
if __name__ == '__main__':
    
    app = QtGui.QApplication(argv)
    
    language = 'English'
    global labelDB
    labelDB = LabelDataBase(language)
    global iconDB
    iconDB = db.icons()
    global StyleDB
    StyleDB = db.styleUI()
    global ttipDB
    ttipDB = db.tooltips(language)    
        
    instance_1 = MainWindow()
    instance_1.show()
    app.exec_()   
    
