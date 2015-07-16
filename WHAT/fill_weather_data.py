# -*- coding: utf-8 -*-
"""
Copyright 2014-2015 Jean-Sebastien Gosselin

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

#---- STANDARD LIBRARY IMPORTS ----

import csv
import sys
from time import ctime, strftime, sleep
from os import getcwd, listdir, makedirs, path
from copy import copy

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui, QtCore
import numpy as np
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple
from numpy.linalg import lstsq as linalg_lstsq

#---- PERSONAL IMPORTS ----

from MyQWidget import MyQToolBox
import database as db
from meteo import make_timeserie_continuous
from hydroprint import LatLong2Dist
import MyQWidget


#===============================================================================
class GapFillWeather(QtGui.QWidget):
#===============================================================================
    
    ConsoleSignal = QtCore.Signal(str)
    
    def __init__(self, parent=None): #========================
        super(GapFillWeather, self).__init__(parent)

        self.isFillAll_inProgress = False
        self.WEATHER = Weather_File_Info()
        self.TARGET = Target_Station_Info()
        
        self.fillworker = FillWorker(self)        
        self.FILLPARAM = GapFill_Parameters()
        
        self.CORRFLAG = 'on'  # Correlation calculation won't be triggered by
                              # events when this is 'off'
        
        self.initUI()        
               
    def initUI(self): #=========================================================
        
        """        
        Layout is organized with an ensemble of grids that are assembled
        together on 3 different levels. First level is the main grid.
        Second level is where are the LEFT and RIGHT grids. Finally, third
        level is where are the SubGrids. The Left and Right grids can contain
        any number of subgrids.
        
                                  MAIN GRID                                                 
                     ----------------------------------                         
                     |               |                |
                     |   LEFT GRID   |   RIGHT GRID   |     
                     |               |                |     
                     ----------------------------------
                     |           TOOLBAR              |
                     ----------------------------------
        """    
        
        #--------------------------------------------------------- Database ----
        
        styleDB = db.styleUI()
        iconDB = db.Icons()
        ttipDB = db.Tooltips('English')
        labelDB = db.labels('English')
        
        #------------------------------------------------------ Main Window ----
        
        self.setWindowIcon(iconDB.WHAT)
#        self.setFont(styleDB.font1) 
        
        #---------------------------------------------------------- TOOLBAR ----
        
        self.btn_fill = QtGui.QPushButton(labelDB.btn_fill_weather)
        self.btn_fill.setIcon(iconDB.fill_data)
        self.btn_fill.setToolTip(ttipDB.btn_fill)
        self.btn_fill.setIconSize(styleDB.iconSize2)
        
        self.btn_fill_all = QtGui.QPushButton(labelDB.btn_fill_all_weather)
        self.btn_fill_all.setToolTip(ttipDB.btn_fill_all)
        self.btn_fill_all.setIcon(iconDB.fill_all_data)
        self.btn_fill_all.setIconSize(styleDB.iconSize2)
        
        grid_toolbar = QtGui.QGridLayout()
        widget_toolbar = QtGui.QFrame()
        
        row = 0
        col = 1
        grid_toolbar.addWidget(self.btn_fill, row, col)
        col += 1
        grid_toolbar.addWidget(self.btn_fill_all, row, col)
        
        grid_toolbar.setSpacing(5)
        grid_toolbar.setContentsMargins(0, 0, 0, 0)
        grid_toolbar.setColumnStretch(0, 100)
        grid_toolbar.setColumnStretch(col+1, 100)
        
        widget_toolbar.setLayout(grid_toolbar)
        
        #------------------------------------------------------- LEFT PANEL ----
        
        #---- Target Station ----
        
        target_station_label = QtGui.QLabel('<b>%s</b>' % labelDB.fill_station)
        self.target_station = QtGui.QComboBox()
        self.target_station_info = QtGui.QTextEdit()
        self.target_station_info.setReadOnly(True)
        self.target_station_info.setMaximumHeight(110)
        
        self.btn_refresh_staList = QtGui.QToolButton()
        self.btn_refresh_staList.setIcon(iconDB.refresh)
        self.btn_refresh_staList.setAutoRaise(True)
        self.btn_refresh_staList.setIconSize(styleDB.iconSize2)
        
        self.tarSta_widg = QtGui.QWidget()                     
        tarSta_grid = QtGui.QGridLayout()
                
        row = 0
        tarSta_grid.addWidget(target_station_label, row, 0, 1, 2)
        row = 1
        tarSta_grid.addWidget(self.target_station, row, 0)
        tarSta_grid.addWidget(self.btn_refresh_staList, row, 1)
        row = 2
        tarSta_grid.addWidget(self.target_station_info, row, 0, 1, 2)
        
        tarSta_grid.setSpacing(5)
        tarSta_grid.setColumnStretch(0, 500)
        tarSta_grid.setContentsMargins(0, 0, 0, 10) #Left, Top, Right, Bottom
        self.tarSta_widg.setLayout(tarSta_grid)
        
        #---- Gapfill Dates ----
        
        label_From = QtGui.QLabel('From :  ')
        self.date_start_widget = QtGui.QDateEdit()
        self.date_start_widget.setDisplayFormat('dd / MM / yyyy')
        self.date_start_widget.setEnabled(False)
        label_To = QtGui.QLabel('To :  ')
        self.date_end_widget = QtGui.QDateEdit()
        self.date_end_widget.setEnabled(False)
        self.date_end_widget.setDisplayFormat('dd / MM / yyyy')
        
        self.fillDates_widg = QtGui.QWidget()                     
        fillDates_grid = QtGui.QGridLayout()
                
        row = 0
        col = 0
        fillDates_grid.addWidget(label_From, row, col)
        col += 1
        fillDates_grid.addWidget(self.date_start_widget, row, col)
        row += 1
        col = 0
        fillDates_grid.addWidget(label_To, row, col)
        col += 1
        fillDates_grid.addWidget(self.date_end_widget, row, col)        
                
        fillDates_grid.setColumnStretch(row+1, 500)
        fillDates_grid.setContentsMargins(0, 0, 0, 0) # [L, T, R, B]
        fillDates_grid.setSpacing(10)
        
        self.fillDates_widg.setLayout(fillDates_grid)
        
        #---- Cutoff Values ----
        
        Nmax_label = QtGui.QLabel(labelDB.NbrSta)
        self.Nmax = QtGui.QSpinBox ()
        self.Nmax.setRange(0, 99)
        self.Nmax.setSingleStep(1)
        self.Nmax.setValue(4)
        self.Nmax.setAlignment(QtCore.Qt.AlignCenter)

        distlimit_label = QtGui.QLabel(labelDB.distlimit)
        distlimit_label.setToolTip(ttipDB.distlimit)
        self.distlimit = QtGui.QSpinBox()
        self.distlimit.setRange(-1, 9999)
        self.distlimit.setSingleStep(1)
        self.distlimit.setValue(100)
        self.distlimit.setToolTip(ttipDB.distlimit)
        self.distlimit.setSuffix(' km')
        self.distlimit.setAlignment(QtCore.Qt.AlignCenter)

        altlimit_label = QtGui.QLabel(labelDB.altlimit)
        altlimit_label.setToolTip(ttipDB.altlimit)
        self.altlimit = QtGui.QSpinBox()
        self.altlimit.setRange(-1, 9999)
        self.altlimit.setSingleStep(1)
        self.altlimit.setValue(350)
        self.altlimit.setToolTip(ttipDB.altlimit)
        self.altlimit.setSuffix(' m')
        self.altlimit.setAlignment(QtCore.Qt.AlignCenter)
        
        cutoff_widg = QtGui.QFrame()                     
        cutoff_grid = QtGui.QGridLayout()        
        
        row = 0
        cutoff_grid.addWidget(self.Nmax, row, 1)
        cutoff_grid.addWidget(Nmax_label, row, 0)        
        row += 1
        cutoff_grid.addWidget(distlimit_label, row, 0)
        cutoff_grid.addWidget(self.distlimit, row, 1)
        row += 1
        cutoff_grid.addWidget(altlimit_label, row, 0)
        cutoff_grid.addWidget(self.altlimit, row, 1)
                
        cutoff_grid.setContentsMargins(10, 0, 10, 0) # [L, T, R, B]
        cutoff_grid.setColumnStretch(2, 500)
        cutoff_grid.setSpacing(10)
        cutoff_widg.setLayout(cutoff_grid)
                
        #---- Regression Model ----
        
        self.RMSE_regression = QtGui.QRadioButton('Ordinary Least Squares')
        self.RMSE_regression.setChecked(True)
        self.ABS_regression = QtGui.QRadioButton('Least Absolute Deviations')
        
        MLRM_widg= QtGui.QFrame()
        MLRM_grid = QtGui.QGridLayout()
        
        row = 0
        MLRM_grid.addWidget(self.RMSE_regression, row, 0)
        row += 1
        MLRM_grid.addWidget(self.ABS_regression, row, 0)
        
        MLRM_grid.setSpacing(5)
        MLRM_grid.setContentsMargins(10, 0, 10, 0) # [L, T, R, B]
        MLRM_widg.setLayout(MLRM_grid)
        
        #---- Advanced Settings ----

        self.full_error_analysis = QtGui.QCheckBox('Full Error Analysis')
        self.full_error_analysis.setCheckState(QtCore.Qt.CheckState.Unchecked)
        
        advanced_widg = QtGui.QFrame()
        advanced_grid = QtGui.QGridLayout()
        
        advanced_grid.addWidget(self.full_error_analysis, 0, 0)
        
        advanced_grid.setSpacing(5)
        advanced_grid.setContentsMargins(10, 0, 10, 0) # [L, T, R, B]
        advanced_grid.setRowStretch(1, 100)
        advanced_widg.setLayout(advanced_grid)
        
        #---- Stacked Widget ----
                
        self.stack_widget = MyQToolBox()
        self.stack_widget.addItem(cutoff_widg, 'Stations Selection Criteria :')
        self.stack_widget.addItem(MLRM_widg, 'Regression Model :')
        self.stack_widget.addItem(advanced_widg, 'Advanced Settings :')
        
        #--- SUBGRIDS ASSEMBLY ----
        
        grid_leftPanel = QtGui.QGridLayout()
        self.LEFT_widget = QtGui.QFrame()
        self.LEFT_widget.setFrameStyle(0) #styleDB.frame

        seprator1 = QtGui.QFrame()
        seprator1.setFrameStyle(styleDB.HLine)
        seprator2 = QtGui.QFrame()
        seprator2.setFrameStyle(styleDB.HLine)        
        seprator3 = QtGui.QFrame()
        seprator3.setFrameStyle(styleDB.HLine)
        
        row = 0 
        grid_leftPanel.addWidget(self.tarSta_widg, row, 0)
        row += 1
        grid_leftPanel.addWidget(self.fillDates_widg, row, 0)
        row += 1
        grid_leftPanel.addWidget(seprator1, row, 0)
        row += 1
        grid_leftPanel.addWidget(self.stack_widget, row, 0)
        row += 2         
        grid_leftPanel.addWidget(seprator2, row, 0)
        row += 1 
        grid_leftPanel.addWidget(widget_toolbar, row, 0)
                
        grid_leftPanel.setVerticalSpacing(15)
        grid_leftPanel.setRowStretch(row-2, 500)
        grid_leftPanel.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)
#        grid_leftPanel.setColumnMinimumWidth(0, styleDB.sideBarWidth)
        
        self.LEFT_widget.setLayout(grid_leftPanel)
        
        #------------------------------------------------------ RIGHT PANEL ----
       
        self.FillTextBox = QtGui.QTextEdit()
        self.FillTextBox.setReadOnly(True)
        self.FillTextBox.setFrameStyle(styleDB.frame)
        self.FillTextBox.setMinimumWidth(700)
        
        grid_RIGHT = QtGui.QGridLayout()
        RIGHT_widget = QtGui.QFrame()
        RIGHT_widget.setFrameStyle(0)
        
        row = 0
        grid_RIGHT.addWidget(self.FillTextBox, row, 0)
        
        grid_RIGHT.setRowStretch(0, 500)
        grid_RIGHT.setColumnStretch(0, 500)
        grid_RIGHT.setContentsMargins(0, 0, 0, 0) #Left, Top, Right, Bottom
                        
        RIGHT_widget.setLayout(grid_RIGHT)
                        
        #-------------------------------------------------------- MAIN GRID ----
        
        grid_MAIN = QtGui.QGridLayout()
        
        row = 0
        grid_MAIN.addWidget(self.LEFT_widget, row, 0)
        grid_MAIN.addWidget(RIGHT_widget, row, 1)
                
        grid_MAIN.setColumnStretch(1, 500)
        grid_MAIN.setRowStretch(0, 500)
        grid_MAIN.setSpacing(15)
        grid_MAIN.setContentsMargins(15, 15, 15, 15) #Left, Top, Right, Bottom
                
        self.setLayout(grid_MAIN)
        
        #----------------------------------------------------- Progress Bar ----

        self.pbar = QtGui.QProgressBar()
        self.pbar.setValue(0)
        self.pbar.hide()
        
        #----------------------------------------------------------- EVENTS ----
                
        self.btn_refresh_staList.clicked.connect(self.load_data_dir_content)
        
        #---- correlation ----
        
        self.target_station.currentIndexChanged.connect(self.correlation_UI)
        self.distlimit.valueChanged.connect(self.correlation_table_display)
        self.altlimit.valueChanged.connect(self.correlation_table_display)
        self.date_start_widget.dateChanged.connect(
                                                 self.correlation_table_display)
        self.date_end_widget.dateChanged.connect(self.correlation_table_display)
        
        #---- gapfill ----
        
        self.fillworker.ProgBarSignal.connect(self.pbar.setValue)
        self.fillworker.EndProcess.connect(self.manage_gapfill)
        self.btn_fill.clicked.connect(self.manage_gapfill)
        self.btn_fill_all.clicked.connect(self.manage_gapfill)
        
        #------------------------------------------------------ MESSAGE BOX ----
                                          
        self.msgBox = MyQWidget.MyQErrorMessageBox()
        
        
    def set_workdir(self, directory): #=========================================
        
        self.workdir = directory
        
        
    def load_data_dir_content(self) : #=========================================
                
        '''
        Initiate the loading of Weater Data Files contained in the 
        </Meteo/Input> folder and display the resulting station list in the
        Target station combo box widget.
        '''
                
        self.FillTextBox.setText('')
        self.target_station_info.setText('')
        self.target_station.clear()
        QtGui.QApplication.processEvents()
        
        self.CORRFLAG = 'off' # Correlation calculation won't 
                              # be triggered when this is off
        
        input_folder = self.workdir + '/Meteo/Input'
        
        if path.exists(input_folder):            
            
            # Generate a list of data file paths.            
            Sta_path = []
            for files in listdir(input_folder):
                if files.endswith(".csv"):
                    Sta_path.append(input_folder + '/' + files)
            
            if len(Sta_path) > 0:
                self.WEATHER.load_and_format_data(Sta_path)
                self.WEATHER.generate_summary(self.workdir)
                self.set_fill_and_save_dates()
                
                self.target_station.addItems(self.WEATHER.STANAME)
                
                self.target_station.setCurrentIndex(-1)
                self.TARGET.index = -1
            else:
                'Data Directory is empty. Do nothing'
        else:
            'Data Directory path does not exists. Do nothing'
            
        self.CORRFLAG = 'on'
        
    
    def set_fill_and_save_dates(self): #========================================
        
        """
        Set first and last dates of the data serie in the boxes of the
        <Fill and Save> area.
        """                                                              
        
        if len(self.WEATHER.DATE) > 0: 

            self.date_start_widget.setEnabled(True)
            self.date_end_widget.setEnabled(True)
            
            DATE = self.WEATHER.DATE
            
            DateMin = QtCore.QDate(DATE[0, 0], DATE[0, 1], DATE[0, 2])
            DateMax = QtCore.QDate(DATE[-1, 0], DATE[-1, 1], DATE[-1, 2])
            
            self.date_start_widget.setDate(DateMin)
            self.date_start_widget.setMinimumDate(DateMin)
            self.date_start_widget.setMaximumDate(DateMax)
                    
            self.date_end_widget.setDate(DateMax)
            self.date_end_widget.setMinimumDate(DateMin)
            self.date_end_widget.setMaximumDate(DateMax)
            
            
    def correlation_table_display(self): #======================================
    
        """
        This method plot the table in the display area. It is separated from
        the method <Correlation_UI> because red numbers and statistics
        regarding missing data for the selected time period can be updated in
        the table when the user changes the values without having to
        recalculate the correlation coefficient each time.
        """
       
        if self.CORRFLAG == 'on' and self.target_station.currentIndex() != -1:

            self.FILLPARAM.limitDist = self.distlimit.value()
            self.FILLPARAM.limitAlt = self.altlimit.value()
           
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
            
           
    def correlation_UI(self): #=================================================
        
        """
        Calculate automatically the correlation coefficients when a target
        station is selected by the user in the drop-down menu.
        """
        
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
            
            self.ConsoleSignal.emit(
            '''<font color=black>
                 Correlation coefficients calculation for station %s completed
               </font>''' % (self.TARGET.name))
                                      
            self.correlation_table_display()
            
        elif self.CORRFLAG == 'off':
            'Do nothing'
    
    def restoreUI(self): #======================================================
        
        iconDB = db.Icons()
        
        self.btn_fill.setIcon(iconDB.fill_data)
        self.btn_fill.setEnabled(True)
        
        self.btn_fill_all.setIcon(iconDB.fill_all_data)
        self.btn_fill_all.setEnabled(True)
        
        self.tarSta_widg.setEnabled(True)
        self.fillDates_widg.setEnabled(True)
        self.stack_widget.setEnabled(True)
        
        QtGui.QApplication.processEvents()

        self.pbar.hide()
            
    def manage_gapfill(self): #=================================================
        
        iconDB = db.Icons()
                    
        #-------------------------------------------- CHECK FOR DATA ERRORS ----
                            
        y = self.date_start_widget.date().year()
        m = self.date_start_widget.date().month()
        d = self.date_start_widget.date().month()
        time_start = xldate_from_date_tuple((y, m, d), 0)
 
        y = self.date_end_widget.date().year()
        m = self.date_end_widget.date().month()
        d = self.date_end_widget.date().day()
        time_end = xldate_from_date_tuple((y, m, d), 0)
            
        if time_start > time_end:
            
            print 'The time period is invalid.'
            self.msgBox.setText('<b>Gap Fill Data Record</b> start date is ' +
                                'set to a later time than the end date.')
            self.msgBox.exec_()
            
            
            return

        #----------------------------------------------------- Check Sender ----
        
        nSTA = len(self.WEATHER.STANAME)
        button = self.sender()
        
        if button == self.btn_fill:
            
            #--------------------------------- Check if Station is Selected ----

            if self.target_station.currentIndex() == -1:

                self.msgBox.setText('No <b>weather station</b> is currently ' +
                                    'selected.')
                self.msgBox.exec_()
                print 'No weather station selected.'
                
                return
                
            #------------------------------------- Stop Thread (if running) ----
                
            if self.fillworker.isRunning(): # Stop the process

                self.restoreUI()
                
                #---- Pass a flag to the worker to tell him to stop ----
                
                self.fillworker.STOP = True
                self.isFillAll_inProgress = False
                
                return
            
            self.btn_fill.setIcon(iconDB.stop)
                        
            self.tarSta_widg.setEnabled(False)
            self.fillDates_widg.setEnabled(False)
            self.stack_widget.setEnabled(False)
            self.btn_fill_all.setEnabled(False)
            
            self.pbar.show()
        
            self.isFillAll_inProgress = False
            sta_indx2fill = self.target_station.currentIndex()

        elif button == self.btn_fill_all:
            
            #--------------------------- Check if Station List is not Empty ----

            if nSTA == 0:

                self.msgBox.setText('There is no data to fill.')
                self.msgBox.exec_()
                print'There is no data to fill.'
                
                return
            
            #------------------------------------- Stop Thread (if running) ----
            
            if self.fillworker.isRunning(): # Stop the process
                print'Coucou fill worker is running'
                self.restoreUI()
                
                #---- Pass a flag to the worker to tell him to stop ----
                
                self.fillworker.STOP = True
                self.isFillAll_inProgress = False
                
                return
            
            #---- Disable UI ----
            
            self.btn_fill_all.setIcon(iconDB.stop)
            self.btn_fill.setEnabled(False)
            self.tarSta_widg.setEnabled(False)
            self.fillDates_widg.setEnabled(False)
            self.stack_widget.setEnabled(False)
            self.pbar.show()
            
            self.isFillAll_inProgress = True
            sta_indx2fill = 0
            
            QtGui.QApplication.processEvents()                
        
            self.correlation_UI()
        
        else: #-------------------------------- Check if process isFinished ----

            sta_indx2fill = self.target_station.currentIndex() + 1
            
            
            if self.isFillAll_inProgress == False or sta_indx2fill == nSTA: 
                
                # Single fill process completed sucessfully for the current
                # selected weather station OR Fill All process completed 
                # sucessfully for all the weather stations in the list.

                self.restoreUI()
                return
                
            else:
                    
               # Fill All process in progress, continue with next
               # weather station in the list.
                    
               pass            
                            
        #-------------------------------------------------------- UPDATE UI ----
                            
        self.CORRFLAG = 'off' 
        self.target_station.setCurrentIndex(sta_indx2fill)
        self.TARGET.index = self.target_station.currentIndex()
        self.TARGET.name = self.WEATHER.STANAME[self.TARGET.index]                        
        self.CORRFLAG = 'on'   
        
        # Calculate correlation coefficient for the next station.
        self.correlation_UI()
        
        #----------------------------------------------------- START THREAD ----
        
        #----- Wait for the QThread to finish -----
        
        # Protection in case the QTread did not had time to close completely
        # before starting the downloading process for the next station.
        
        waittime = 0
        while self.fillworker.isRunning():
            print('Waiting for the fill weather data thread to close')
            sleep(1)
            waittime += 1
            if waittime > 15:
                msg = ('This function is not working as intended.' +
                       ' Please report a bug.')
                print(msg)
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
                return
                
        #---- Pass information to the worker ----
        
        self.fillworker.project_dir = self.workdir
        
        self.fillworker.time_start = time_start
        self.fillworker.time_end = time_end   

        self.fillworker.Nbr_Sta_max_user = self.Nmax.value()
        self.fillworker.limitDist = self.distlimit.value()
        self.fillworker.limitAlt = self.altlimit.value()                     
        
        self.fillworker.WEATHER = self.WEATHER
        self.fillworker.TARGET = self.TARGET
                                    
        self.fillworker.regression_mode = self.RMSE_regression.isChecked()
        
        self.fillworker.full_error_analysis = self.full_error_analysis.isChecked()
                                        
        #---- Start the Thread ----
                                        
        self.fillworker.start()
            
        return
    
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
class Weather_File_Info():
    """
    <Weather_File_Info> class contains all the weather data and station info
    that are needed for the gapfilling algorithm.
    
    
    Data = Weather data organised in a 3D matrix [i, j, k], where:

               layer k=1 is Maximum Daily Temperature
               layer k=2 is Minimum Daily Temperature
               layer k=3 is Daily Mean Temperature
               layer k=4 is Total Daily Precipitation
               rows are the time
               columns are the stations listed in STANAME
    """
#=============================================================================== 
        
    def __init__(self):
        
        self.DATA = []       # Weather data
        self.DATE = []       # Date in tuple format [YEAR, MONTH, DAY]
        self.TIME = []       # Date in numeric format
        self.STANAME = []    # Station names
        self.ALT = []        # Station elevation in m
        self.LAT = []        # Station latitude in decimal degree
        self.LON = []        # Station longitude in decimal degree
        self.VARNAME = []    # Names of the meteorological variables
        self.ClimateID = []  # Climate Identifiers of weather station
        self.PROVINCE = []   # Provinces where weater station are located        
        self.DATE_START = [] # Date start of the original data records
        self.DATE_END = []   # Date end of the original data records
        self.NUMMISS = []    # Number of missing data
        
    def load_and_format_data(self, fnames):  #==================================
        
        # fnames = list of paths of weater data files
    
        nSTA = len(fnames) # Number of weather data file
        
        #-------------------------------------------- INITIALIZED VARIABLES ----
        
        self.STANAME = np.zeros(nSTA).astype('str')
        self.ALT = np.zeros(nSTA)
        self.LAT = np.zeros(nSTA)
        self.LON = np.zeros(nSTA)
        self.PROVINCE = np.zeros(nSTA).astype('str')
        self.ClimateID = np.zeros(nSTA).astype('str')
        self.DATE_START = np.zeros((nSTA, 3)).astype('int')
        self.DATE_END = np.zeros((nSTA, 3)).astype('int')
            
        FLAG_date = False # If True, a new DATE matrix will be rebuilt at the
                          # of this routine.
        
        for i in range(nSTA):
        
            #------------------------------------------ WEATHER DATA IMPORT ----
        
            with open(fnames[i], 'rb') as f:
                reader = list(csv.reader(f, delimiter='\t'))
            
            STADAT = np.array(reader[8:]).astype('float')
            
            self.DATE_START[i, :] = STADAT[0, :3]
            self.DATE_END[i, :] = STADAT[-1, :3]
            
            #---------------------------------------- TIME CONTINUITY CHECK ----
            
            # Check if data are continuous over time. If not, the serie will be
            # made continuous and the gaps will be filled with nan values.
            
            time_start = xldate_from_date_tuple((STADAT[0, 0].astype('int'),
                                                 STADAT[0, 1].astype('int'),
                                                 STADAT[0, 2].astype('int')), 0)

            time_end = xldate_from_date_tuple((STADAT[-1, 0].astype('int'),
                                               STADAT[-1, 1].astype('int'),
                                               STADAT[-1, 2].astype('int')), 0)
            
            if time_end - time_start + 1 != len(STADAT[:,0]):
                print; print reader[0][1], ' is not continuous, correcting...'
            
                STADAT = make_timeserie_continuous(STADAT)
            
                print reader[0][1], ' is now continuous.'
            else: # Data is continuous over time
                pass
            
            time_new = np.arange(time_start, time_end + 1)
            
            #------------------------------------------- FIRST TIME ROUTINE ----
            
            if i == 0:
                self.VARNAME = reader[7][3:]
                nVAR = len(self.VARNAME) # number of meteorological variable
                self.TIME = np.copy(time_new)
                self.DATA = np.zeros((len(STADAT[:, 0]), nSTA, nVAR)) * np.nan
                self.DATE = STADAT[:, :3]
                self.NUMMISS = np.zeros((nSTA, nVAR)).astype('int')
            else:
                pass
                
            #------------------------------------ <DATA> & <TIME> RESHAPING ----
            
            # This part of the function fits neighboring data series to the
            # target data serie in the 3D data matrix. Default values in the
            # 3D data matrix are nan.
        
            if self.TIME[0] <= time_new[0]:
                
                if self.TIME[-1] >= time_new[-1]:
                    
                    #    [---------------]    self.TIME
                    #         [-----]         time_new
                    
                    pass
                    
                else:
                    
                    #    [--------------]         self.TIME
                    #         [--------------]    time_new
                    #                    
                    #           OR
                    #
                    #    [--------------]           self.TIME
                    #                     [----]    time_new
                                        
                    FLAG_date = True
                    
                    # Expand <DATA> and <TIME> to fit the new data serie
                    
                    EXPND = np.zeros((time_new[-1] - self.TIME[-1],
                                      nSTA, nVAR)) * np.nan
                    
                    self.DATA = np.vstack((self.DATA, EXPND))
                
                    self.TIME = np.arange(self.TIME[0], time_new[-1] + 1)
                 
            elif self.TIME[0] > time_new[0]:
                
                if self.TIME[-1] >= time_new[-1]:
            
                    #        [----------]    self.TIME
                    #    [----------]        time_new
                    #           
                    #            OR
                    #           [----------]    self.TIME
                    #    [----]                 time_new
                    
                    FLAG_date = True
                    
                    # Expand <DATA> and <TIME> to fit the new data serie
                    
                    EXPND = np.zeros((self.TIME[0] - time_new[0],
                                  nSTA, nVAR)) * np.nan
                                  
                    self.DATA = np.vstack((EXPND, self.DATA))
                
                    self.TIME = np.arange(time_new[0], self.TIME[-1] + 1)
            
                else:
                    
                    #        [----------]        self.TIME
                    #    [------------------]    time_new
                    
                    FLAG_date = True
                    
                    # Expand <DATA> and <TIME> to fit the new data serie
                    
                    EXPNDbeg = np.zeros((self.TIME[0] - time_new[0],
                                         nSTA, nVAR)) * np.nan
                    
                    EXPNDend = np.zeros((time_new[-1] - self.TIME[-1],
                                         nSTA, nVAR)) * np.nan
                    
                    self.DATA = np.vstack((EXPNDbeg, self.DATA, EXPNDend))
                    
                    self.TIME = np.copy(time_new)
                    
        #---------------------------------------------------- FILL MATRICES ----
         
            ifirst = np.where(self.TIME == time_new[0])[0][0]
            ilast = np.where(self.TIME == time_new[-1])[0][0]
            
            self.DATA[ifirst:ilast+1, i, :] = STADAT[:, 3:]
            
            # Calculate number of missing data.
            
            isnan = np.isnan(STADAT[:, 3:])
            self.NUMMISS[i, :] = np.sum(isnan, axis=0)
            
            # Check if a station with this name already exist.
            
            isNameExist = np.where(reader[0][1] == self.STANAME)[0]
            if len(isNameExist) > 0:
                
                print 'Station name already exists, adding a number at the end'
                
                count = 2
                while len(isNameExist) > 0:
                    newname = '%s (%d)' % (reader[0][1], count)
                    isNameExist = np.where(newname == self.STANAME)[0]
                    count += 1
                
                self.STANAME[i] = newname
                
            else:
                self.STANAME[i] = reader[0][1]
                        
            self.PROVINCE[i] = reader[1][1]
            self.LAT[i] = float(reader[2][1])
            self.LON[i] = float(reader[3][1])
            self.ALT[i] = float(reader[4][1])
            self.ClimateID[i] = str(reader[5][1])
            
        #-------------------------------------- SORT STATION ALPHABETICALLY ----

        sort_index = np.argsort(self.STANAME)
        
        self.DATA = self.DATA[:, sort_index, :]
        self.STANAME = self.STANAME[sort_index]
        self.PROVINCE = self.PROVINCE[sort_index]
        self.LAT = self.LAT[sort_index]
        self.LON = self.LON[sort_index]
        self.ALT = self.ALT[sort_index]
        self.ClimateID = self.ClimateID[sort_index]
        
        self.NUMMISS = self.NUMMISS[sort_index, :]
        self.DATE_START = self.DATE_START[sort_index]
        self.DATE_END = self.DATE_END[sort_index]
        
        #---------------------------------------------- GENERATE DATE SERIE ----
    
        # Rebuild a date matrix if <DATA> size changed.
    
        if FLAG_date == True:
            self.DATE = np.zeros((len(self.TIME), 3))
            for i in range(len(self.TIME)):
                date_tuple = xldate_as_tuple(self.TIME[i], 0)
                self.DATE[i, 0] = date_tuple[0]
                self.DATE[i, 1] = date_tuple[1]
                self.DATE[i, 2] = date_tuple[2]
        if FLAG_date == False:
            'Do nothing, keep <DATE> as is'

    
    def generate_summary(self, project_folder): #===============================

        """
        This method will generate a summary of the weather records including all
        the data files contained in "/<project_folder>/Meteo/Input", including
        dates when the records begin and end, total number of data, and total 
        number of data missing for each meteorological variable, and more.
        """
    
        nVAR = len(self.VARNAME)
        nSTA = len(self.STANAME)
        
        CONTENT = [['#', 'STATION NAMES', 'ClimateID',
                    'Lat. (dd)', 'Lon. (dd)', 'Alt. (m)',
                    'DATE START', 'DATE END', 'Nbr YEARS' , 'TOTAL DATA',
                    'MISSING Tmax', 'MISSING Tmin', 'MISSING Tmean',
                    'Missing Precip', 'Missing TOTAL']]
                                
        for i in range(nSTA):
            record_date_start = '%04d/%02d/%02d' % (self.DATE_START[i, 0],
                                                    self.DATE_START[i, 1],
                                                    self.DATE_START[i, 2]) 
                                                    
            record_date_end = '%04d/%02d/%02d' % (self.DATE_END[i, 0],
                                                  self.DATE_END[i, 1],
                                                  self.DATE_END[i, 2])
                                                  
            time_start = xldate_from_date_tuple((self.DATE_START[i, 0],
                                                 self.DATE_START[i, 1],
                                                 self.DATE_START[i, 2]), 0)
    
            time_end = xldate_from_date_tuple((self.DATE_END[i, 0],
                                               self.DATE_END[i, 1],
                                               self.DATE_END[i, 2]), 0)
                                               
            number_data = float(time_end - time_start + 1)
            
            CONTENT.append([i+1 , self.STANAME[i], self.ClimateID[i],
                            '%0.2f' % self.LAT[i], '%0.2f' % self.LON[i],
                            '%0.2f' % self.ALT[i],
                            record_date_start, record_date_end,
                            '%0.1f' % (number_data / 365.25), number_data])
                            
            # Missing data information for each meteorological variables   
            for var in range(len(self.VARNAME)):
                txt1 = self.NUMMISS[i, var]
                txt2 = self.NUMMISS[i, var] / number_data * 100
                CONTENT[-1].extend(['%d (%0.1f %%)' % (txt1, txt2)])
            
            # Total missing data information.
            txt1 = np.sum(self.NUMMISS[i, :])
            txt2 = txt1 / (number_data * nVAR) * 100
            CONTENT[-1].extend(['%d (%0.1f %%)' % (txt1, txt2)])
        
        output_path = project_folder + '/weather_datasets_summary.log'
                
        with open(output_path, 'wb') as f:
            writer = csv.writer(f,delimiter='\t')
            writer.writerows(CONTENT)
            
#===============================================================================
def alt_and_dist_calc(WEATHER, target_station_index):
    """
    <alt_and_dist_calc> computes the horizontal distance in km and the altitude
    difference in m between the target station and each neighboring stations
    """
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
    
    #---------------------------------------------TARGET STATION INFO TABLE-----
    
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
    
    #---------------------------------------------------------SORT STATIONS-----
    
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
              
    #-----------------------------------------------------CORRELATION TABLE-----
    
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
                  Correlation coefficients are set to <b>nan</b> for a given 
                  variable if there is less than <b>%d</b> pairs of data 
                  between the target and the neighboring station.
                </p>''' % (Ndata_limit)
             
    return table, target_info

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
        self.Nbr_Sta_max_user = 4
        self.limitDist = 100
        self.limitAlt = 350
        
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
        
        print STANAME
        print target_station_index, target_station_name
        
        HORDIST = np.copy(self.TARGET.HORDIST)
        ALTDIFF = np.copy(np.abs(self.TARGET.ALTDIFF))
        
        Nbr_Sta_max_user = self.Nbr_Sta_max_user
        limitDist = self.limitDist
        limitAlt = self.limitAlt
        

        # Save target data serie in a new 2D matrix that will be filled during
        # the data completion process
        Y2fill = np.copy(DATA[:, target_station_index, :])
        
        if self.full_error_analysis == True:
            YpFULL = np.copy(Y2fill) * np.nan
            print; print 'A full error analysis will be performed'; print
        
        msg = 'Data completion for station %s started' % target_station_name
        print(msg)
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)
        
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
            progress_total = np.copy(nbr_nan_total)
            
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
            Sta_index = sort_stations_correlation_order(CORCOEF[var, :],
                                                        target_station_index)
            
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

        #=============================================== WRITE DATA TO FILE ====
                    
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
        HEADER.append(['Created by', db.software_version])
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
        
        target_station_name = target_station_name.replace('\\', '_')
        target_station_name = target_station_name.replace('/', '_')

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
        
        print; print '!Data completion completed successfully!'; print                 
        self.STOP = False # Just in case. This is a precaution override.  
        self.EndProcess.emit(1) 
        
        return 
        
            # MAE = np.abs(Y - Yp)
            # MAE = MAE[MAE!=0]
            # MAE = np.mean(MAE)

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


def sort_stations_correlation_order(CORCOEF, target_station_index): #===========
        
    # An index is associated with each value of the CORCOEF array.
    Sta_index = range(len(CORCOEF))    
    CORCOEF = np.vstack((Sta_index, CORCOEF)).transpose()
    
    # Remove target station from the stack. This is necessary in case there is
    # some data that belong to the same station, but without the same length.
    
    CORCOEF = np.delete(CORCOEF, target_station_index, axis=0)
    
    # Stations for which the correlation coefficient is nan are removed.
    CORCOEF = CORCOEF[~np.isnan(CORCOEF).any(axis=1)] 
               
    # The station indexes are sorted in descending order of their
    # correlation coefficient.
    CORCOEF = CORCOEF[np.flipud(np.argsort(CORCOEF[:, 1])), :]
    
    Sta_index = np.copy(CORCOEF[:, 0].astype('int'))
    
    # Add target station to the first value of the array.
    Sta_index = np.insert(Sta_index, 0, target_station_index)
    
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
    
           
if __name__ == '__main__':
    
    app = QtGui.QApplication(sys.argv) 
    
    instance1 = GapFillWeather()   

    instance1.set_workdir("../Projects/Project4Testing")

    #---- SHOW ----
              
    instance1.show()
        
    qr = instance1.frameGeometry()
    cp = QtGui.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    instance1.move(qr.topLeft())
    
    instance1.load_data_dir_content()
       
    sys.exit(app.exec_())
    
    