# -*- coding: utf-8 -*-
"""
Copyright 2014-2015 Jean-Sebastien Gosselin

email: jnsebgosselin@gmail.com

This file is part of WHAT (Well Hydrograph Analysis Toolbox).

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

#----- STANDARD LIBRARY IMPORTS -----

from urllib2 import urlopen, URLError
from datetime import datetime
from sys import argv
from os import getcwd, path, makedirs
from time import gmtime, sleep
import csv
from string import maketrans

#----- THIRD PARTY IMPORTS -----

import numpy as np
from PySide import QtGui, QtCore

#---- PERSONAL IMPORTS ----

import database as db

class Tooltips():
    
    def __init__(self, language): #------------------------------- ENGLISH -----
        
        self.search4stations = ('Search for weather stations in the ' +
                                'Canadian Daily Climate Database (CDCD)')
        self.refresh_staList = 'Refresh the current weather station list'
        self.btn_browse_staList = 'Load an existing weather station list'
        self.btn_save_staList = 'Save current station list.'
        self.btn_delSta = 'Remove selected weather stations from the list'
        
        
        self.btn_GetData = 'Download data for the selected weather stations'
        
        
        self.btn_select_rawData = 'Select and format raw weather data files' 
        self.btn_save_concatenate = 'Save formated weather data in a csv file'
        
        if language == 'French': #--------------------------------- FRENCH -----
            
            pass

#===============================================================================
class dwnldWeather(QtGui.QWidget):
    """
    Interface that allow to download daily weather data from the governement
    of Canada website.
    """
#===============================================================================
    
    ConsoleSignal = QtCore.Signal(str)
    
    def __init__(self, parent=None):
        super(dwnldWeather, self).__init__(parent)
        
        self.initUI()
        
    def initUI(self):
        
        #--------------------------------------------------------- Database ----
        
        styleDB = db.styleUI()
        iconDB = db.icons()
        ttipDB = Tooltips('English')
        labelDB = db.labels('English')
        
        #--------------------------------------------------- VARIABLES INIT ----
        
        self.workdir = getcwd()
        
        self.staList_fname = []
        self.staList_isNotSaved = False
        
        self.mergeHistoryLog = []
        self.mergeHistoryIndx = 0
        self.mergeHistoryFnames = []
        
        self.staList2dwnld = []
        self.dwnld_indx = 0
        
        #--------------------------------------------------- Instances init ----
        
        self.search4stations = search4stations(self)
        self.search4stations.setWindowFlags(QtCore.Qt.Window)
        self.search4stations.workdir = self.workdir
        
        self.station_table = stationTable(self)
        
        self.dwnl_raw_datafiles = DownloadRawDataFiles(self)
        
        #---------------------------------------------------------- TOOLBAR ----
       
        btn_save_menu = QtGui.QMenu()
        btn_save_menu.addAction('Save As...', self.btn_saveAs_staList_isClicked)
        
        self.btn_save_staList = QtGui.QToolButton()
        self.btn_save_staList.setIcon(iconDB.save)
        self.btn_save_staList.setAutoRaise(True)
        self.btn_save_staList.setToolTip(ttipDB.btn_save_staList)
        self.btn_save_staList.setIconSize(styleDB.iconSize)
        self.btn_save_staList.setMenu(btn_save_menu)
        self.btn_save_staList.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
                
        btn_search4station = QtGui.QToolButton()
        btn_search4station.setAutoRaise(True)
        btn_search4station.setIcon(iconDB.search)
        btn_search4station.setToolTip(ttipDB.search4stations)
        btn_search4station.setIconSize(styleDB.iconSize)
        
        btn_browse_staList = QtGui.QToolButton()
        btn_browse_staList.setIcon(iconDB.openFile)
        btn_browse_staList.setAutoRaise(True)
        btn_browse_staList.setToolTip(ttipDB.btn_browse_staList)
        btn_browse_staList.setIconSize(styleDB.iconSize)
        
        btn_delSta = QtGui.QToolButton()
        btn_delSta.setIcon(iconDB.clear_search)
        btn_delSta.setAutoRaise(True)
        btn_delSta.setToolTip(ttipDB.btn_delSta)
        btn_delSta.setIconSize(styleDB.iconSize)
        
        self.btn_get = QtGui.QToolButton()
        self.btn_get.setIcon(iconDB.download)
        self.btn_get.setAutoRaise(True)
        self.btn_get.setToolTip(ttipDB.btn_GetData)
        self.btn_get.setIconSize(styleDB.iconSize)
        
        self.saveAuto_checkbox = QtGui.QCheckBox(labelDB.saveMeteoAuto)
        self.saveAuto_checkbox.setCheckState(QtCore.Qt.Checked)
        
        separator1 = QtGui.QFrame()
        separator1.setFrameStyle(styleDB.VLine)
        separator2 = QtGui.QFrame()
        separator2.setFrameStyle(styleDB.VLine)
        
        toolbar_grid = QtGui.QGridLayout()
        toolbar_widg = QtGui.QWidget()
        
        row = 0
        col = 0
        toolbar_grid.addWidget(self.btn_save_staList, row, col)
        col += 1
        toolbar_grid.addWidget(btn_search4station, row, col)
        col += 1
        toolbar_grid.addWidget(btn_browse_staList, row, col)
        col += 1                
        toolbar_grid.addWidget(separator1, row, col)
        col += 1
        toolbar_grid.addWidget(btn_delSta, row, col)
        col += 1
        toolbar_grid.addWidget(self.btn_get, row, col)
        col += 1
        toolbar_grid.setColumnStretch(col, 100)
        col += 1
        toolbar_grid.addWidget(self.saveAuto_checkbox, row, col)
        
        toolbar_grid.setSpacing(5)
        toolbar_grid.setContentsMargins(0, 0, 0, 0)
        
        toolbar_widg.setLayout(toolbar_grid)
        
        #----------------------------------------------------- Progress Bar ----

        self.pbar = QtGui.QProgressBar()
        self.pbar.setValue(0)
        
        #------------------------------------------------------ Right Panel ----
                
        display_label = QtGui.QLabel('<b>Downloaded Weather Data Info :</b>')
        
        #---- Go Toolbar ----        
        
        self.btn_goNext = QtGui.QToolButton()
        self.btn_goNext.setIcon(iconDB.go_next)
        self.btn_goNext.setAutoRaise(True)
#        btn_goNext.setToolTip(ttipDB.btn_delSta)
        self.btn_goNext.setIconSize(styleDB.iconSize)
        self.btn_goNext.setEnabled(False)
        
        self.btn_goPrevious = QtGui.QToolButton()
        self.btn_goPrevious.setIcon(iconDB.go_previous)
        self.btn_goPrevious.setAutoRaise(True)
#        btn_goNext.setToolTip(ttipDB.btn_delSta)
        self.btn_goPrevious.setIconSize(styleDB.iconSize)
        self.btn_goPrevious.setEnabled(False)
        
        self.btn_goLast = QtGui.QToolButton()
        self.btn_goLast.setIcon(iconDB.go_last)
        self.btn_goLast.setAutoRaise(True)
#        btn_goLast.setToolTip(ttipDB.btn_delSta)
        self.btn_goLast.setIconSize(styleDB.iconSize)
        self.btn_goLast.setEnabled(False)
        
        self.btn_goFirst = QtGui.QToolButton()
        self.btn_goFirst.setIcon(iconDB.go_first)
        self.btn_goFirst.setAutoRaise(True)
#        btn_goNext.setToolTip(ttipDB.btn_delSta)
        self.btn_goFirst.setIconSize(styleDB.iconSize)
        self.btn_goFirst.setEnabled(False)
        
        goToolbar_grid = QtGui.QGridLayout()
        goToolbar_widg = QtGui.QFrame()
        
        col = 0
        goToolbar_grid.addWidget(self.btn_goFirst, 0, col)
        col += 1
        goToolbar_grid.addWidget(self.btn_goPrevious, 0, col)
        col += 1
        goToolbar_grid.addWidget(self.btn_goNext, 0, col)
        col += 1
        goToolbar_grid.addWidget(self.btn_goLast, 0, col)
        
        goToolbar_grid.setContentsMargins(0, 0, 0, 0) # [L, T, R, B]
        goToolbar_grid.setSpacing(5)
        
        goToolbar_widg.setLayout(goToolbar_grid)
        
        #---- Right Panel Assembly ----
        
        self.mergeDisplay = QtGui.QTextEdit()
        self.mergeDisplay.setReadOnly(True) 
        
        btn_selectRaw = QtGui.QPushButton(labelDB.btn_select_rawData)
        btn_selectRaw.setIcon(iconDB.openFile)
        btn_selectRaw.setToolTip(ttipDB.btn_select_rawData)
        btn_selectRaw.setIconSize(styleDB.iconSize2)   
        
        btn_saveMerge = QtGui.QPushButton(labelDB.btn_save_concatenate)
        btn_saveMerge.setToolTip(ttipDB.btn_save_concatenate)
        btn_saveMerge.setIcon(iconDB.save)
        btn_saveMerge.setIconSize(styleDB.iconSize2)
        
        rightPanel_grid = QtGui.QGridLayout()
        rightPanel_widg = QtGui.QFrame()
        
        row = 0  
             
        rightPanel_grid.addWidget(btn_selectRaw, row, 0)
        rightPanel_grid.addWidget(btn_saveMerge, row, 1)
        row += 1   
        rightPanel_grid.addWidget(self.mergeDisplay, row, 0, 1, 3)
        
        row += 1
        rightPanel_grid.addWidget(goToolbar_widg, row, 0, 1, 3)
        
        rightPanel_grid.setContentsMargins(0, 0, 0, 0) # [L, T, R, B]
        rightPanel_grid.setRowStretch(row+1, 100)
        rightPanel_grid.setColumnStretch(2, 100)
        
        rightPanel_widg.setLayout(rightPanel_grid)
        
        #-------------------------------------------------------- Main Grid ----
        
        vLine1 = QtGui.QFrame()
        vLine1.setFrameStyle(styleDB.VLine)
        
        main_grid = QtGui.QGridLayout()
        
        main_grid.addWidget(toolbar_widg, 0, 0)
        main_grid.addWidget(self.station_table, 1, 0)
        main_grid.addWidget(vLine1, 0, 1, 2, 1)
        
        main_grid.addWidget(display_label, 0, 2)
        main_grid.addWidget(rightPanel_widg, 1, 2)
                
        main_grid.setContentsMargins(10, 10, 10, 10) # [L, T, R, B] 
        main_grid.setColumnStretch(0, 500)
        main_grid.setRowStretch(1, 500)
        main_grid.setVerticalSpacing(5)
        main_grid.setHorizontalSpacing(15)
        
        self.setLayout(main_grid)
        
        #------------------------------------------------------ MESSAGE BOX ----
                                          
        self.msgBox = QtGui.QMessageBox()
        self.msgBox.setIcon(QtGui.QMessageBox.Warning)
        self.msgBox.setWindowTitle('Error Message')
        
        #----------------------------------------------------------- EVENTS ----
        
        #---- download raw data ----
        
        self.btn_get.clicked.connect(self.manage_raw_data_dwnld)
        self.dwnl_raw_datafiles.EndSignal.connect(self.manage_raw_data_dwnld)
        self.dwnl_raw_datafiles.MergeSignal.connect(self.concatenate_and_display)
        self.dwnl_raw_datafiles.ProgBarSignal.connect(self.set_progressBar)
        
        #---- concatenate raw data ----
        
        btn_selectRaw.clicked.connect(self.btn_selectRaw_isClicked)
        self.btn_goLast.clicked.connect(self.btn_goLast_isClicked)
        self.btn_goFirst.clicked.connect(self.btn_goFirst_isClicked)
        self.btn_goNext.clicked.connect(self.btn_goNext_isClicked)
        self.btn_goPrevious.clicked.connect(self.btn_goPrevious_isClicked)
        btn_saveMerge.clicked.connect(self.btn_saveMerge_isClicked)
        
        #---- weather station list ----
        
        btn_delSta.clicked.connect(self.btn_delSta_isClicked)
        btn_browse_staList.clicked.connect(self.btn_browse_staList_isClicked)
        self.btn_save_staList.clicked.connect(self.btn_save_staList_isClicked)
        
        #---- search4stations ----
        
        btn_search4station.clicked.connect(self.btn_search4station_isClicked) 
        self.search4stations.staListSignal.connect(
                                                 self.search4station_isFinished)        
        
            
    def set_workdir(self, directory):
        
        self.workdir = directory
        self.search4stations.workdir = directory
        
        
    def btn_delSta_isClicked(self):        
        
        # Going in reverse order to preserve indexes while scanning the rows if
        # any are deleted.
        
        for row in reversed(range(self.station_table.rowCount())):
            isChecked = self.station_table.cellWidget(row, 0).isChecked()
            if isChecked:                
                print('Removing %s (%s)' 
                      % (self.station_table.item(row, 1).text(),
                         self.station_table.item(row, 2).text())
                      ) 
                self.station_table.removeRow(row)
                self.staList_isNotSaved = True
                    
                    
    def btn_search4station_isClicked(self):
                
        qr = self.search4stations.frameGeometry()
        cp = self.frameGeometry().center()
        qr.moveCenter(cp)
        self.search4stations.move(qr.topLeft())
        
        self.search4stations.show()
        self.search4stations.setFixedSize(self.search4stations.size())       
    
    
    def search4station_isFinished(self, staList):
        
        self.station_table.populate_table(staList)
        self.staList_isNotSaved = True
        self.staList_fname = []
        
        
    def btn_browse_staList_isClicked(self):
        
        '''
        Allows the user to select a weather station list with 
        a 'lst' extension.
        '''
                
        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                            self, 'Select a valid station list',
                                            self.workdir, '*.lst')        

        if filename:
            
            QtGui.QApplication.processEvents()
            self.load_stationList(filename)
            
    
    def load_stationList(self, filename):
        
        '''
        It loads the informations in the weather stations list file (.lst) that
        is located in "filename". The content is then displayed in a
        QTableWidget named "station_table".
        
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
        
        #--------------------------------------------- Check if file exists ----
        
        # In case this method is not called from the UI.
        
        headerDB = db.headers()        
        self.staList_isNotSaved = False
        
        if not path.exists(filename):
            
            msg  = '%s not found. Please select an existing weather station'
            msg += ' list or search for new stations on the CDCD.'
            print(msg)
            self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
            
            self.station_table.populate_table(staList=[])
            self.staList_fname = []            
            
            return
        
        #-------------------------------------------------------- Open file ----
        
        with open(filename, 'rb') as f:
            reader = list(csv.reader(f, delimiter='\t'))
        
        #---------------------------------------------------- Check version ----
        
        # Check if the list is from an older version, and update it if yes
        
        header = headerDB.weather_stations[0]
        
        nCONFG, nPARA = np.shape(reader)         
        if nPARA < len(header):
            print 'This list is from an older version of WHAT.'
            print 'Converting to new format.'
            
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                                                        
            self.ConsoleSignal.emit('''<font color=black>Converting weather
            station list to a more recent format. Please wait...</font>''')
            
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
                    reader[i+1, 5] = get_climate_ID(Prov, stationId)
            
            #---- Save List ----
            
            with open(filename, 'wb') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(reader)
            
            QtGui.QApplication.restoreOverrideCursor()
    
    #------------------------------------------------------ Load list in UI ----
        
        if len(reader) > 1:
            
            print("Weather station list loaded successfully")
            self.ConsoleSignal.emit('''<font color=black>Weather station list 
            loaded successfully.</font>''')
           
            staList = np.array(reader[1:])            
                                         
        else:
            
            print("Weather station list is empty.")            
            self.ConsoleSignal.emit('''<font color=red>Weather Station list is
            empty.</font>''')
            
            staList = []
            
        self.station_table.populate_table(staList)
        self.staList_fname = filename
    
    def btn_save_staList_isClicked(self):
        
        filename = self.staList_fname
        
        if filename:
            
            print('Station list saved in %s' % filename)
            self.ConsoleSignal.emit('''<font color=black>
                                         Station list saved in %s 
                                       </font>''' % filename)

            self.station_table.save_staList(filename)
            self.staList_isNotSaved = False
                           
        else:
            self.btn_saveAs_staList_isClicked()
    
    def btn_saveAs_staList_isClicked(self):        
        
        dirname = self.workdir + '/weather_stations.lst'
        
        dialog = QtGui.QFileDialog()
        dialog.setConfirmOverwrite(True)
        fname, ftype = dialog.getSaveFileName(
                                    caption="Save Weather Stations List",
                                    dir=dirname, filter=('*.lst'))
                                  
        if fname:  
            
            if fname[-4:] != ftype[1:]:  # Add a file extension if there is none                
                fname = fname + ftype[1:]
        
            self.station_table.save_staList(fname)
            self.staList_fname = fname
            self.staList_isNotSaved = False
            
            print('Station list saved in %s' % fname)
            self.ConsoleSignal.emit('''<font color=black>
                                         Station list saved in %s 
                                       </font>''' % fname)

    
    def manage_raw_data_dwnld(self):
        
        """
        This method starts the downloading process of the raw weather
        data files.
        
        Also, this method manages the stopping of the downloading process
        and the state of the "btn_get". Before the downloading
        process is started, the text and the icon of "btn_get" is changed to 
        look like a stop button. 
        
        If "btn_get" is clicked again by the user during the downloading 
        process, the state of the button reverts back to its original display. 
        In addition the value of the "STOP" flag is forced to True in the 
        download Thread to stop the downloading process.
        """
        
        iconDB = db.icons()
        
        if self.dwnl_raw_datafiles.isRunning():
            
            # Stop the Download process and reset UI
            
            self.dwnl_raw_datafiles.STOP = True
            self.btn_get.setIcon(iconDB.download)
            self.dwnld_indx = 0
            
            self.station_table.setEnabled(True)
            self.pbar.hide()
            
            return
      
        if self.dwnld_indx == 0: #--------- Grab stations that are selected ----
            
            # Grabbing weather stations that are selected and saving them 
            # in a list. The structure of "weather_stations.lst" is preserved
            # in the process.
            
            self.staList2dwnld = [] 
            for row in range(self.station_table.rowCount()):
                
                # staList structure:
                # [staName, stationId, StartYear, EndYear,
                #  Province, ClimateID,Proximity (km)]
                #
                # staTable structure:
                # ('', 'Weather Stations', 'Proximity \n (km)', 'From \n Year', 
                #  'To \n Year', 'Prov.', 'Climate ID', 'Station ID') 
            
                if self.station_table.cellWidget(row, 0).isChecked():                
                    
                    #   0      1          2          3         4          5
                    # [row, StaName, Station ID, startYear, endYear, Climate ID]
                    
                    sta2add = (
                    [row,
                     self.station_table.item(row, 1).text(),
                     self.station_table.item(row, 7).text(),
                     self.station_table.cellWidget(row, 3).currentText(),
                     self.station_table.cellWidget(row, 4).currentText(),
                     self.station_table.item(row, 6).text()])
                    
                    self.staList2dwnld.append(sta2add)
                    
            if len(self.staList2dwnld) == 0:
                
                print('No weather station currently selected.')
                self.msgBox.setText('No weather station currently selected.')
                self.msgBox.exec_()
                return
        
        else: #-------------------------------- Check if process isFinished ----
                            
            if self.dwnld_indx >= (len(self.staList2dwnld)):
                
                print('Raw weather data downloaded for all selected stations.')
                
                # Reset UI and variables
                
                self.dwnld_indx = 0
                self.station_table.setEnabled(True)
                self.pbar.hide()
                self.btn_get.setIcon(iconDB.download)
                
                return
            
        #------------------------------------------------- Start the Thread ----
        
        #---- Push Thread Info ----  
        
        self.dwnl_raw_datafiles.dirname = self.workdir + '/Meteo/Raw'
        
        sta2dwnl = self.staList2dwnld[self.dwnld_indx]     
                
        self.dwnl_raw_datafiles.StaName = sta2dwnl[1]                
        self.dwnl_raw_datafiles.stationID = sta2dwnl[2]
        self.dwnl_raw_datafiles.yr_start = sta2dwnl[3]
        self.dwnl_raw_datafiles.yr_end = sta2dwnl[4]
        self.dwnl_raw_datafiles.climateID = sta2dwnl[5]
        
        #---- Update UI ----
            
        self.station_table.setEnabled(False)
        self.pbar.show()
        self.btn_get.setIcon(iconDB.stop)
        self.station_table.selectRow(sta2dwnl[0])
             
        #----- Start Download -----
        
        self.dwnld_indx += 1
             
        self.dwnl_raw_datafiles.start()
           
    #------------------------------------------------- Display Merge Memory ----
   
    def btn_goLast_isClicked(self):

        self.mergeHistoryIndx = len(self.mergeHistoryLog) - 1
        self.display_mergeHistory()
        
        
    def btn_goFirst_isClicked(self):

        self.mergeHistoryIndx = 0
        self.display_mergeHistory()
        
        
    def btn_goNext_isClicked(self):
        
        self.mergeHistoryIndx += 1
        self.display_mergeHistory()
        
        
    def btn_goPrevious_isClicked(self):
        
        self.mergeHistoryIndx += -1
        self.display_mergeHistory()
        
        
    def display_mergeHistory(self):
        self.mergeDisplay.setText(self.mergeHistoryLog[self.mergeHistoryIndx])
        
        if len(self.mergeHistoryLog) > 1:
        
            if self.mergeHistoryIndx == (len(self.mergeHistoryLog) - 1):
                self.btn_goLast.setEnabled(False)
                self.btn_goNext.setEnabled(False)
                self.btn_goFirst.setEnabled(True)
                self.btn_goPrevious.setEnabled(True)
            elif self.mergeHistoryIndx == 0:
                self.btn_goLast.setEnabled(True)
                self.btn_goNext.setEnabled(True)
                self.btn_goFirst.setEnabled(False)
                self.btn_goPrevious.setEnabled(False)
            else:
                self.btn_goLast.setEnabled(True)
                self.btn_goNext.setEnabled(True)
                self.btn_goFirst.setEnabled(True)
                self.btn_goPrevious.setEnabled(True)
    
    #---------------------------------------------------------------------------
    
    def btn_selectRaw_isClicked(self):
        
        """
        This method is called by the event <btn_select.clicked.connect>.
        It allows the user to select a group of raw data files belonging to a
        given meteorological station in order to concatenate them into a single
        file with the method <concatenate_and_display>.
        """
        
        dialog_fir = self.workdir + '/Meteo/Raw'
        
        fname, _ = QtGui.QFileDialog.getOpenFileNames(self, 'Open files', 
                                                      dialog_fir, '*.csv')
        if fname:
           self.concatenate_and_display(fname) 
           
    def concatenate_and_display(self, filenames):        
        
        """
        Handles the concatenation process of individual yearly raw data files 
        and display the results in the <mergeDisplay> widget.
        
        ---- CALLED BY----
        
        (1) Method: select_raw_files
        (2) Event:  self.dwnl_rawfiles.MergeSignal.connect
        """
        
        if len(filenames) == 0:
            print"No raw data file selected."
            return
        
        mergeOutput, LOG, COMNT = concatenate(filenames)
        
        StaName = mergeOutput[0, 1]
        YearStart = mergeOutput[8, 0][:4]
        YearEnd = mergeOutput[-1, 0][:4]
        climateID = mergeOutput[5, 1]
               
        self.ConsoleSignal.emit("""<font color=black>Raw data files concatened 
        successfully for station %s.</font>""" % StaName)
        
        #---- Update history variables and UI ----
        
        self.mergeHistoryLog.append(LOG)
        self.mergeHistoryIndx = len(self.mergeHistoryLog) - 1
        self.display_mergeHistory()
        self.mergeHistoryFnames.append(filenames)
                                  
        if COMNT:
            
            # A comment is issued only when all raw data files 
            # do not belong to the same weather station. 
            
            self.ConsoleSignal.emit(COMNT)
        
        if self.saveAuto_checkbox.isChecked():
            
            # Check if the characters "/" or "\" are present in the station 
            # name and replace these characters by "-" if applicable.
            
            intab = "/\\"
            outtab = "--"
            trantab = maketrans(intab, outtab)
            StaName = StaName.translate(trantab)
            
            save_dir = self.workdir + '/Meteo/Input/'
            if not path.exists(save_dir):
                makedirs(save_dir)
                
            filename = '%s (%s)_%s-%s.csv' % (StaName, climateID,
                                              YearStart, YearEnd)
            fname = save_dir + filename
            
            self.save_concatened_data(fname, mergeOutput) 
            
            
    def btn_saveMerge_isClicked(self):
        
        '''        
        This method allows the user to select a path for the file in which the 
        concatened data are going to be saved.
        
        ---- CALLED BY----
        
        (1) Event: btn_saveMerge.clicked.connect
        '''
    
        
        filenames = self.mergeHistoryFnames[self.mergeHistoryIndx]
        mergeOutput, _, _ = concatenate(filenames)
        
        if np.size(mergeOutput) != 0:
            
            StaName = mergeOutput[0, 1]
            YearStart = mergeOutput[8, 0][:4]
            YearEnd = mergeOutput[-1, 0][:4]
            climateID = mergeOutput[5, 1]
            
            # Check if the characters "/" or "\" are present in the station 
            # name and replace these characters by "-" if applicable.            
            intab = "/\\"
            outtab = "--"
            trantab = maketrans(intab, outtab)
            StaName = StaName.translate(trantab)
            
            filename = '%s (%s)_%s-%s.csv' % (StaName, climateID,
                                              YearStart, YearEnd)
            dialog_dir = self.workdir + '/Meteo/Input/' + filename
                          
            fname, _ = QtGui.QFileDialog.getSaveFileName(
                                         self, 'Save file', dialog_dir, '*.csv')
            
            if fname:                
                self.save_concatened_data(fname, mergeOutput)
            
    def save_concatened_data(self, fname, fcontent):  
        
        """
        This method saves the concatened data into a single csv file.
        
        ---- CALLED BY----
        
        (1) Method: btn_saveMerge_isClicked
        (2) Method: concatenate_and_display if self.saveAuto_checkbox.isChecked
        """
        
        with open(fname, 'wb') as f:
            writer = csv.writer(f,delimiter='\t')
            writer.writerows(fcontent)
        
        print('Concatened data saved in: %s.' % fname)
        self.ConsoleSignal.emit("""<font color=black>Concatened data saved 
        in: %s.</font>""" % fname)  
            
    
    def set_progressBar(self, progress):
        
        """
        Updates the value of the progression bar widget to display the raw 
        data files downloading progress.
        
        The method is called by a signal emitted by the instance 
        "dwnl_raw_datafiles".
        """

        self.pbar.setValue(progress)


#===============================================================================
class stationTable(QtGui.QTableWidget):
#===============================================================================
    
    def __init__(self, parent=None):
        super(stationTable, self).__init__(parent)
        
        self.initUI()
    
    def initUI(self):

        StyleDB = db.styleUI()
                
        #------------------------------------------------------------ Style ----
        
        self.setFrameStyle(StyleDB.frame)
        self.setMinimumWidth(650)
        self.setMinimumHeight(500)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        
        #----------------------------------------------------------- Header ----
        
        HEADER = ('', 'Weather Stations', 'Proximity \n (km)', 'From \n Year', 
                  'To \n Year', 'Prov.', 'Climate ID', 'Station ID')     
        self.setColumnCount(len(HEADER))
        
        self.setHorizontalHeaderLabels(HEADER)        
        self.verticalHeader().hide()
        
        #----------------------------------------------- Column Size Policy ----
        
        self.setColumnHidden(6, True)
        self.setColumnHidden(7, True)
        
        self.setColumnWidth(0, 32)
        self.setColumnWidth(3, 75)
        self.setColumnWidth(4, 75)

        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
    
    class NumTableWidgetItem(QtGui.QTableWidgetItem):
            
        # To be able to sort numerical item within a given column.

        # http://stackoverflow.com/questions/12673598/
        # python-numerical-sorting-in-qtablewidget
        
            def __init__(self, text, sortKey):
                QtGui.QTableWidgetItem.__init__(self, text, 
                                                QtGui.QTableWidgetItem.UserType)
                self.sortKey = sortKey

            # Qt uses a simple < check for sorting items, override this to use
            # the sortKey
            def __lt__(self, other):
                return self.sortKey < other.sortKey
                
    def populate_table(self, staList):
        
        nrow = len(staList)
        self.setRowCount(nrow)
        
        self.setSortingEnabled(False)
        
        for row in range(nrow):
            
            # More Options:
            
            # item.setFlags(QtCore.Qt.ItemIsEnabled & ~QtCore.Qt.ItemIsEditable)
            # item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

            
            col = 0  # Checkbox
            
            item = QtGui.QTableWidgetItem('')
            item.setFlags(~QtCore.Qt.ItemIsEditable & QtCore.Qt.ItemIsEnabled)
            self.setItem(row, col, item)
            
            self.dwnldCheck =  QtGui.QCheckBox()            
            self.setCellWidget(row, col, self.dwnldCheck)
            
            col += 1 # Weather Station
            
            item = QtGui.QTableWidgetItem(staList[row, 0])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setToolTip(staList[row, 0])
            self.setItem(row, col, item)
            
            col += 1 # Proximity
            
            item = self.NumTableWidgetItem('%0.2f' % float(staList[row, 6]),
                                           float(staList[row, 6]))
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, col, item)
            
            min_year = int(staList[row, 2])
            max_year = int(staList[row, 3])
            yearspan = np.arange(min_year, max_year+1).astype(str)
            
            col += 1 # From Year
            
            item = QtGui.QTableWidgetItem('')
            item.setFlags(~QtCore.Qt.ItemIsEditable & QtCore.Qt.ItemIsEnabled)
            self.setItem(row, col, item)
            
            self.fromYear = QtGui.QComboBox() 
            self.fromYear.setFixedWidth(75)
            self.fromYear.setInsertPolicy(QtGui.QComboBox.NoInsert)
            self.fromYear.addItems(yearspan)
            self.fromYear.setMinimumContentsLength(4)
            self.fromYear.setSizeAdjustPolicy(
                                  QtGui.QComboBox.AdjustToMinimumContentsLength)            
                                  
            self.setCellWidget(row, col, self.fromYear)
            
            col += 1 # To Year
            
            item = QtGui.QTableWidgetItem('')
            item.setFlags(~QtCore.Qt.ItemIsEditable & QtCore.Qt.ItemIsEnabled)
            self.setItem(row, col, item)
            
            self.toYear = QtGui.QComboBox()
            self.toYear.setFixedWidth(75)
            self.toYear.setInsertPolicy(QtGui.QComboBox.NoInsert)
            self.toYear.addItems(yearspan)
            self.toYear.setCurrentIndex(len(yearspan)-1)
            self.toYear.setMinimumContentsLength(4)
            self.toYear.setSizeAdjustPolicy(
                                  QtGui.QComboBox.AdjustToMinimumContentsLength)
                                  
            self.setCellWidget(row, col, self.toYear)
            
            col += 1 # Province
            
            item = QtGui.QTableWidgetItem(staList[row, 4])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, col, item)
            
            col += 1 # Climate ID (hidden)
            
            item = QtGui.QTableWidgetItem(staList[row, 5])
            self.setItem(row, col, item)
            
            col += 1 # Station ID
            
            item = QtGui.QTableWidgetItem(staList[row, 1])
            self.setItem(row, col, item)
            
        self.setSortingEnabled(True)

    def save_staList(self, filename):
        
        headerDB = db.headers()
                     
       #------------------------------------------ grabbing info from table ----              
              
        staList = headerDB.weather_stations        
        for row in range(self.rowCount()):
                
            # staList structure:
            
            # [staName, stationId, StartYear, EndYear,
            #  Province, ClimateID,Proximity (km)]
            
            # staTable structure:

            # ('', 'Weather Stations', 'Proximity \n (km)', 'From \n Year', 
            #  'To \n Year', 'Prov.', 'Climate ID', 'Station ID') 

            NItems = self.cellWidget(row, 4).count()
                            
            sta2add = [self.item(row, 1).text(),
                       self.item(row, 7).text(),
                       self.cellWidget(row, 3).itemText(0),
                       self.cellWidget(row, 4).itemText(NItems-1),                       
                       self.item(row, 5).text(),                       
                       self.item(row, 6).text(),
                       self.item(row, 2).text()]
                       
            staList.append(sta2add)  
        
        #--------------------------------------------------- saving results ----        
        
        with open(filename, 'wb') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(staList)
            
        
        
              
#===============================================================================
class search4stations(QtGui.QWidget):
    '''
    Widget that allows the user to search for weather stations on the
    Government of Canada website.
    '''
#===============================================================================
    
    ConsoleSignal = QtCore.Signal(str)
    staListSignal = QtCore.Signal(list)

    def __init__(self, parent=None):
        super(search4stations, self).__init__(parent)
        
        self.initUI()
              
    def initUI(self):

        #--------------------------------------------------- INIT VARIABLES ----
        
        iconDB = db.icons()
        StyleDB = db.styleUI()
#        ttipDB = Tooltips('English')
        
        now = datetime.now()
        
        self.workdir = getcwd()
        
        #------------------------------------------------------- Left Panel ----
        
        #---- Widgets ----
        
        label_Lat = QtGui.QLabel('Latitude :')
        label_Lat2 = QtGui.QLabel('N')
        label_Lon = QtGui.QLabel('Longitude :')
        label_Lon2 = QtGui.QLabel('W')
        label_radius = QtGui.QLabel('Radius :')
        
        self.lat_spinBox = QtGui.QDoubleSpinBox()
        self.lat_spinBox.setAlignment(QtCore.Qt.AlignCenter)        
        self.lat_spinBox.setSingleStep(0.1)
        self.lat_spinBox.setValue(0)
        self.lat_spinBox.setMinimum(0)
        self.lat_spinBox.setMaximum(180)
        self.lat_spinBox.setSuffix(u' °')
        
        self.lon_spinBox = QtGui.QDoubleSpinBox()
        self.lon_spinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.lon_spinBox.setSingleStep(0.1)
        self.lon_spinBox.setValue(0)
        self.lon_spinBox.setMinimum(0)
        self.lon_spinBox.setMaximum(180)
        self.lon_spinBox.setSuffix(u' °')
        
        self.radius_SpinBox = QtGui.QSpinBox()
        self.radius_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.radius_SpinBox.setSingleStep(5)
        self.radius_SpinBox.setMinimum(5)
        self.radius_SpinBox.setMaximum(500)
        self.radius_SpinBox.setSuffix(' km')
        
        #---- Grid ----
        
        widget_leftPanel = QtGui.QWidget()
        grid_leftPanel = QtGui.QGridLayout()
        
        row = 0
        grid_leftPanel.addWidget(label_Lat, row, 0)
        grid_leftPanel.addWidget(self.lat_spinBox, row, 1)
        grid_leftPanel.addWidget(label_Lat2, row, 2)
        row += 1
        grid_leftPanel.addWidget(label_Lon, row, 0)
        grid_leftPanel.addWidget(self.lon_spinBox, row, 1)
        grid_leftPanel.addWidget(label_Lon2, row, 2)
        row += 1
        grid_leftPanel.addWidget(label_radius, row, 0)
        grid_leftPanel.addWidget(self.radius_SpinBox, row, 1)
        
        grid_leftPanel.setSpacing(5)
        grid_leftPanel.setColumnStretch(1, 100)
        grid_leftPanel.setRowStretch(row + 1, 100)
        grid_leftPanel.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)
        
        widget_leftPanel.setLayout(grid_leftPanel)
        
        #------------------------------------------------------ Right Panel ----
        
        label_date = QtGui.QLabel('Stations with data between')
        
        self.minYear = QtGui.QSpinBox()
        self.minYear.setAlignment(QtCore.Qt.AlignCenter)
        self.minYear.setSingleStep(1)
        self.minYear.setMinimum(1840)
        self.minYear.setMaximum(now.year)
        self.minYear.setValue(1840)
        
        label_and = QtGui.QLabel('and')
        label_and.setAlignment(QtCore.Qt.AlignCenter)
        
        self.maxYear = QtGui.QSpinBox()
        self.maxYear.setAlignment(QtCore.Qt.AlignCenter)
        self.maxYear.setSingleStep(1)
        self.maxYear.setMinimum(1840)
        self.maxYear.setMaximum(now.year)
        self.maxYear.setValue(now.year)
        
        #---- subgrid1 ----
        
        label_4atleast = QtGui.QLabel('for at least')
        label_years = QtGui.QLabel('years')
        
        self.nbrYear = QtGui.QSpinBox()
        self.nbrYear.setAlignment(QtCore.Qt.AlignCenter)
        self.nbrYear.setSingleStep(1)
        self.nbrYear.setMinimum(0)
        self.nbrYear.setValue(3)
        
        subwidg1 = QtGui.QWidget()
        subgrid1 = QtGui.QGridLayout()
        
        col = 0
        subgrid1.addWidget(label_4atleast, 0, col)
        col += 1
        subgrid1.addWidget(self.nbrYear, 0, col)
        col += 1
        subgrid1.addWidget(label_years, 0, col)
        
        subgrid1.setSpacing(10)
        subgrid1.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)
        subgrid1.setColumnStretch(col+1, 100)
        
        subwidg1.setLayout(subgrid1)
        
        #---- maingrid ----
        
        widget_rightPanel = QtGui.QWidget()
        grid_rightPanel = QtGui.QGridLayout()
        
        row = 0
        grid_rightPanel.addWidget(label_date, row, 0, 1, 3)
        row += 1
        grid_rightPanel.addWidget(self.minYear, row, 0)
        grid_rightPanel.addWidget(label_and, row, 1)
        grid_rightPanel.addWidget(self.maxYear, row, 2)
        row += 1
        grid_rightPanel.addWidget(subwidg1, row, 0, 1, 3)
        
        grid_rightPanel.setSpacing(10)
        grid_rightPanel.setColumnStretch(0, 100)
        grid_rightPanel.setColumnStretch(2, 100)
        grid_rightPanel.setRowStretch(row + 1, 100)
        grid_rightPanel.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)
        
        widget_rightPanel.setLayout(grid_rightPanel)
        
        #-------------------------------------------------------- MAIN GRID ----
        
        #---- Widgets ----
        
        line1 = QtGui.QFrame()
        line1.setFrameStyle(StyleDB.VLine)
        
        self.btn_search = QtGui.QPushButton('Search')
        self.btn_search.setIcon(iconDB.search)
        self.btn_search.setIconSize(StyleDB.iconSize2)
        
        #---- GRID ----
                        
        grid_search4stations = QtGui.QGridLayout()
        
        row = 1
        col = 1        
        grid_search4stations.addWidget(widget_leftPanel, row, col)
        col += 1
        grid_search4stations.addWidget(line1, row, col)
        col += 1
        grid_search4stations.addWidget(widget_rightPanel, row, col)
        row += 1
        grid_search4stations.addWidget(self.btn_search, row, 1, 1, 3)
                        
        grid_search4stations.setContentsMargins(15, 15, 15, 15) # (L, T, R, B) 
        grid_search4stations.setSpacing(10)
        grid_search4stations.setColumnStretch(0, 100)
        grid_search4stations.setColumnStretch(col+1, 100)
        grid_search4stations.setRowStretch(0, 100)
        grid_search4stations.setRowStretch(row + 1, 100)
        
        self.setLayout(grid_search4stations)
        self.setFont(StyleDB.font1)
        
        #------------------------------------------------------ MAIN WINDOW ----
        
        self.setWindowTitle('Search for Weather Stations')
        self.setWindowIcon(iconDB.WHAT)
#        self.widget_search4stations.setFixedSize(500, 200)
        
        #----------------------------------------------------------- EVENTS ----
        
        self.minYear.valueChanged.connect(self.minYear_changed)
        self.maxYear.valueChanged.connect(self.maxYear_changed)
        self.btn_search.clicked.connect(self.btn_search_isClicked)
                                            
    def minYear_changed(self):
        
        min_yr = min_yr = max(self.minYear.value(), 1840)
        
        now = datetime.now()
        max_yr = now.year
                
        self.maxYear.setRange(min_yr, max_yr)
        
    def maxYear_changed(self):
        
        min_yr = 1840
        
        now = datetime.now()
        max_yr = min(self.maxYear.value(), now.year)
                
        self.minYear.setRange(min_yr, max_yr)
        

    def btn_search_isClicked(self):

        """
        Initiate the seach for weather stations. It grabs the info from the
        interface and send it to the method "search_envirocan".
        """
        
        #---- Close window ----
        
        self.close()

        #---- Generate New List ----
        # http://doc.qt.io/qt-5/qt.html#CursorShape-enum
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        self.ConsoleSignal.emit('''<font color=black>
                                     Searching for weather stations. Please
                                     wait...
                                   </font>''')
                
        print("")
        print("---- SEARCHING FOR STATIONS ----")       
        print("")
                                     
        QtCore.QCoreApplication.processEvents()
        QtCore.QCoreApplication.processEvents()
        
        LAT = self.lat_spinBox.value()
        LON = self.lon_spinBox.value()
        RADIUS = self.radius_SpinBox.value()
        startYear = self.minYear.value()
        endYear = self.maxYear.value()
        nbrYear = self.nbrYear.value()
      
        self.search_envirocan(LAT, LON, RADIUS, startYear, endYear, nbrYear)
            
        QtGui.QApplication.restoreOverrideCursor()
        
        print("")
        print("-------------- FIN -------------")
        print("")
  
    #===========================================================================
    def search_envirocan(self, LAT, LON, RADIUS, YearMin, YearMax, nbrYear):
        """
        Search on the Government of Canada website for weather stations with
        daily meteo data around a decimal degree Lat & Lon coordinate with a
        radius given in km.
        
        The results are returned in a list formatted ready to be
        read by WHAT UI. A signal is emitted with the list if the process is
        completed successfully.
        
        If no results are found, only the header is return with an empty
        list of station.
        
        If an error is raised, an empty list is returned. 
        """
    #===========================================================================
        
        Nmax = 100. # Number of results per page (maximum possible is 100)
            
#        StationID = np.array(['stationId']) # to download the data from server
#        Prov = np.array(['Province'])
#        StartYear = np.array(['StartYear'])
#        EndYear = np.array(['EndYear'])
#        staName = np.array(['staName'])
#        ClimateID = np.array(['ClimateID'])
#        staProxim = np.array(['Proximity (km)'])
        
        StationID = np.array([]).astype(str) # to download the data from server
        Prov = np.array([]).astype(str)
        StartYear = np.array([]).astype(str)
        EndYear = np.array([]).astype(str)
        staName = np.array([]).astype(str)
        ClimateID = np.array([]).astype(str)
        staProxim = np.array([]).astype(str)
        
        #-------------------------------------------------------------- url ----
        
        url =  'http://climate.weather.gc.ca/advanceSearch/'
        url += 'searchHistoricDataStations_e.html?'
        url += 'searchType=stnProx&timeframe=1&txtRadius=%d' % RADIUS
        url += '&selCity=&selPark=&optProxType=custom'
    
        deg, mnt, sec = decdeg2dms(np.abs(LAT))
        url += '&txtCentralLatDeg=%d' % deg
        url += '&txtCentralLatMin=%d' % mnt
        url += '&txtCentralLatSec=%d' % sec
    
        deg, mnt, sec = decdeg2dms(np.abs(LON))
        url += '&txtCentralLongDeg=%d' % deg
        url += '&txtCentralLongMin=%d' % mnt
        url += '&txtCentralLongSec=%d' % sec
    
        url += '&optLimit=yearRange'
        url += '&StartYear=%d' % YearMin
        url += '&EndYear=%d' % YearMax
        url += '&Year=2013&Month=6&Day=4'
        url += '&selRowPerPage=%d' % Nmax
        url += '&cmdProxSubmit=Search' 
        
        try:
            
            # write downloaded content to local file for debugging purpose
            f = urlopen(url)
            with open("url.txt", "wb") as local_file:
                local_file.write(f.read())
        
            #------------------------------------------- Results Extraction ----
            
            f = urlopen(url)
            stnresults = f.read()
            
            #---- Number of Stations Found ----
        
            txt2find = ' stations found'
            indx_e = stnresults.find(txt2find, 0)
            if indx_e == -1:
                print 'No weather station found.'            
                msg = '<font color=red>No weather station found.</font>'                
                self.ConsoleSignal.emit(msg)
                
                Nsta = 0
                
            else:
                indx_0 = stnresults.find('<p>', indx_e-10)
                Nsta = int(stnresults[indx_0+3:indx_e])
                print '%d weather stations found.' % Nsta
                
                Npage = int(np.ceil(Nsta / Nmax))
                
                for page in range(Npage):
                    
                    print 'Page :', page
                    
                    startRow = (Nmax * page) + 1
                    url4page = url + '&startRow=%d' % startRow
                    f = urlopen(url4page)
                        
                    stnresults = f.read()
                    
                    indx_e = 0
                   
                    for row in range(int(Nmax)): # Scan each row of the
                                                 # current page
    
                        #---- StartDate and EndDate ----
                        
                        txt2find  =  '<input type="hidden" name='
                        txt2find +=  '"dlyRange" value="'
                        n = len(txt2find)
                        indx_0 = stnresults.find(txt2find, indx_e)
                        if indx_0 == -1: # No result left on this page                       
                            break
                        else:
                            pass
                        indx_e = stnresults.find('|', indx_0)
                        
                        start_year = stnresults[indx_0+n:indx_0+n+4]
                        end_year = stnresults[indx_e+1:indx_e+1+4]
                        
                        #---- StationID ----
                        
                        txt2find  = '<input type="hidden" name='
                        txt2find += '"StationID" value="'
                        n = len(txt2find)
                        indx_0 = stnresults.find(txt2find, indx_e)
                        indx_e = stnresults.find('" />', indx_0)
                        
                        station_id = stnresults[indx_0+n:indx_e]
                        
                        #---- Province ----
                        
                        txt2find = '<input type="hidden" name="Prov" value="'
                        n = len(txt2find)
                        indx_0 = stnresults.find(txt2find, indx_e)
                        indx_e = stnresults.find('" />', indx_0)
                        
                        province = stnresults[indx_0+n:indx_e]
                        
                        #---- Name ----
                        
                        txt2find  = '<div class="span-2 row-end row-start marg'
                        txt2find += 'in-bottom-none station wordWrap stnWidth">'
                        n = len(txt2find)
                        indx_0 = stnresults.find(txt2find, indx_e)
                        indx_e = stnresults.find('</div>', indx_0)
                        
                        station_name = stnresults[indx_0+n:indx_e]
                        station_name = station_name.strip()
                        
                        #---- Proximity ----
                        
                        txt2find  = '<div class="span-1 row-end row-start '
                        txt2find += 'margin-bottom-none day_mth_yr wordWrap">'
                        n = len(txt2find)
                        indx_0 = stnresults.find(txt2find, indx_e)
                        indx_e = stnresults.find('</div>', indx_0)
                        
                        station_proxim = stnresults[indx_0+n:indx_e]
                        station_proxim = station_proxim.strip()
                        
                        if start_year.isdigit(): # daily data exist
                             
                            if (int(end_year) - int(start_year)) >= nbrYear:
                           
                                print("adding %s"  % station_name)
        
                                StartYear = np.append(StartYear, start_year)
                                EndYear = np.append(EndYear, end_year)
                                StationID = np.append(StationID, station_id)
                                Prov = np.append(Prov, province)
                                staName = np.append(staName, station_name)
                                staProxim = np.append(staProxim, station_proxim)
                                
                                
                            else:                                
                                print("not adding %s (not enough data)" 
                                      % station_name)
                                
                        else:
                            print("not adding %s (no daily data)" 
                                  % station_name)
                                    
                msg  = '%d weather stations with daily data' % (len(staName))
                msg += ' for at least %d years' % nbrYear
                msg += ' between %d and %d' % (YearMin, YearMax)
                print(msg) 
                msg = '<font color=green>' + msg + '</font>'
                self.ConsoleSignal.emit(msg)         
                QtCore.QCoreApplication.processEvents()
                QtCore.QCoreApplication.processEvents()
                   
                #------------------------------------------- Get Climate ID ----
                
                print('Fetching info for each station...')
                self.ConsoleSignal.emit('''<font color=black>
                                             Fetching info for each station...
                                           </font>''')  
                QtCore.QCoreApplication.processEvents()
                QtCore.QCoreApplication.processEvents()
                         
                for sta in range(len(staName)):
                    climate_id = get_climate_ID(Prov[sta], StationID[sta])
                    ClimateID = np.append(ClimateID, climate_id)
                    
                print('Info fetched for each station successfully.')
                self.ConsoleSignal.emit('''<font color=black>Info fetched for
                each station successfully.</font>''') 
                
                #----------------------------- SORT STATIONS ALPHABETICALLY ----
    
#                sort_indx = np.argsort(staName[1:])
#                sort_indx += 1
#                
#                StartYear[1:] = StartYear[sort_indx]
#                EndYear[1:] = EndYear[sort_indx]
#                StationID[1:] = StationID[sort_indx]
#                Prov[1:] = Prov[sort_indx]
#                staName[1:] = staName[sort_indx]
#                ClimateID[1:] = ClimateID[sort_indx]
#                staProxim[1:] = staProxim[sort_indx]
                
                sort_indx = np.argsort(staName)

                StartYear = StartYear[sort_indx]
                EndYear = EndYear[sort_indx]
                StationID = StationID[sort_indx]
                Prov = Prov[sort_indx]
                staName = staName[sort_indx]
                ClimateID = ClimateID[sort_indx]
                staProxim = staProxim[sort_indx]
                
                #-------------------------------------------- Save Results ----
                
                staList = [staName, StationID, StartYear, EndYear, Prov,
                   ClimateID, staProxim]
                staList = np.transpose(staList)
            
#                fname = self.workdir + '/weather_stations.lst'    
#                with open(fname, 'wb') as f:
#                    writer = csv.writer(f, delimiter='\t')
#                    writer.writerows(staList)
#                    
#                print("Saving results in %s" % fname)
#                self.ConsoleSignal.emit('''<font color=black>
#                                             Saving results in %s 
#                                           </font>''' % fname)
                                   
                #------------------------- Send Signal to load list into UI ----
                
                self.staListSignal.emit(staList)
            
        except URLError as e:
            
            staList = []
            
            if hasattr(e, 'reason'):
                print('Failed to reach a server.')
                print('Reason: ', e.reason)
                print
                
                self.ConsoleSignal.emit("""<font color=red>
                                             Failed to reach the server.
                                           </font>""")
                
            elif hasattr(e, 'code'):
                print('The server couldn\'t fulfill the request.')
                print('Error code: ', e.code)
                print
                
                self.ConsoleSignal.emit(
                '''<font color=red>
                     The server couldn\'t fulfill the request.
                   </font>''')
        
        return staList
            
#===============================================================================
def decdeg2dms(dd):
    '''
    Convert decimal degree lat/lon coordinate to decimal, minute, second format.
    '''    
#===============================================================================
    
    mnt,sec = divmod(dd*3600, 60)
    deg,mnt = divmod(mnt, 60)
    
    return deg, mnt, sec


#===============================================================================   
def dms2decdeg(deg, mnt, sec):
    '''
    Convert decimal, minute, second format lat/lon coordinate to decimal degree.
    '''
#===============================================================================
    
    dd = deg + mnt/60. + sec/3600.    
    
    return dd
    
    
#===============================================================================
def get_climate_ID(Prov, StationID):
    """
    Fetch the Climate Id for a given station. This ID is used to identified
    the station in the CDCD, but not for downloading the data from the server.
    
    This information is not available when doing a search for stations and need
    to be fetch for each station individually.
    """
#===============================================================================    

    url = ("http://climate.weather.gc.ca/climateData/dailydata_e.html?" + 
           "timeframe=2&Prov=%s&StationID=%s") % (Prov, StationID)
          
    f = urlopen(url)                    
    urlread = f.read()

    indx_e = 0
    
    # Need to navigate the result in 2 steps to be sure
   
    txt2find = ('<a href="http://climate.weather.gc.ca/' + 
                'glossary_e.html#climate_ID">Climate ID</a>:')
    n = len(txt2find)
    indx_0 = urlread.find(txt2find, indx_e) + n
    
    txt2find = ('<td>')
    n = len(txt2find)
    indx_0 = urlread.find(txt2find, indx_0)

    indx_e = urlread.find('</td>', indx_0)
    
    climate_id = urlread[indx_0+n:indx_e]
    climate_id = climate_id.strip()
          
    return climate_id


#===============================================================================        
class DownloadRawDataFiles(QtCore.QThread):        
    '''
    This thread is used to download the raw data files from
    www.climate.weather.gc.ca and saves them automatically in
    <Project_directory>/Meteo/Raw/<station_name (Climate ID)>.

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
    
    EndSignal = QtCore.Signal(bool)
    MergeSignal = QtCore.Signal(list)
    ProgBarSignal = QtCore.Signal(int)
    ConsoleSignal = QtCore.Signal(str)
    
    def __init__(self, parent=None):
        super(DownloadRawDataFiles, self).__init__(parent)
        
        self.STOP = False  
        
        self.ERRFLAG = []
        
        # These values need to be pushed from the parent.
        
        self.dirname = []   # Directory where the downloaded files are saved
        self.stationID = [] # Unique identifier for the station used for
                            # downloading the data from the server
        self.climateID = [] # Unique identifier for the station
        self.yr_start = []
        self.yr_end = []
        self.StaName = [] # Common name given to the station (not unique)
          
    def run(self): 
        
    #---------------------------------------------------------------- INIT -----
        
        dirname = self.dirname
        
        staID = self.stationID   
        yr_start = int(self.yr_start)
        yr_end = int(self.yr_end)
        StaName = self.StaName
        climateID = self.climateID
        
        self.ERRFLAG = np.ones(yr_end - yr_start + 1)
             
        self.ConsoleSignal.emit(
        '''<font color=black>Downloading data from </font>
           <font color=blue>www.climate.weather.gc.ca</font>
           <font color=black> for station %s</font>''' % StaName)
        self.ProgBarSignal.emit(0)         
        
        dirname += '/%s (%s)' % (StaName, climateID)
        if not path.exists(dirname):
            makedirs(dirname)
            
        #-------------------------------------------------------- DOWNLOAD -----
            
        # Data are downloaded on a yearly basis from yStart to yEnd
         
        fname4merge = [] # list of paths of the yearly raw data files that will
                         # be pass to contatenate and merge function.
        i = 0
        for year in range(yr_start, yr_end+1):
            
            if self.STOP == True : # User stopped the downloading process.                
                break
            
            #----- File and URL Paths -----
            
            fname = dirname + '/eng-daily-0101%s-1231%s.csv' % (year, year) 
            
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
                
                sleep(0.1)
                
                self.ConsoleSignal.emit(
                '''<font color=green>A weather data file already existed for
                     station %s for year %d. Downloading is skipped.
                   </font>''' % (StaName, year))
                fname4merge.append(fname)
                            
            i += 1
            
        #----------------------------------------------------- End of Task -----
        
        if self.STOP == True:
            
            self.STOP = False
            print("Downloading process for station %s stopped." % StaName)
            self.ConsoleSignal.emit('''<font color=red>Downloading process for
                                         station %s stopped.
                                       </font>''' % StaName)
        else:
            
            cmt  = "All raw  data files downloaded sucessfully for "
            cmt += "station %s." % StaName
            print(cmt)
            self.ConsoleSignal.emit('<font color=black>%s</font>' % cmt)

            self.EndSignal.emit(True)
            self.MergeSignal.emit(fname4merge)
            self.ProgBarSignal.emit(0)
                
    def dwndfile(self, url, fname):
        
        # http://stackoverflow.com/questions/4028697
        # https://docs.python.org/3/howto/urllib2.html
        
        try:
            
            ERRFLAG = 0
            
            f = urlopen(url)
            print "downloading " + fname

            # write downloaded content to local file
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
        
        with open(fname[i], 'rb') as f:
            reader = list(csv.reader(f, delimiter=','))
                  
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
    
    FIELDS = ['Tmax', 'Tmin', 'Tmean', 'Ptot', 'Total']
    
    ndata = float(len(ALLDATA[:, 0]))
#    Ndata = float(len(ALLDATA[:, 0]) * 4) 
    
    LOG = '''
          <p>
            Number of days with missing data from %d to %d for station %s :
          </p>
          <br>
          <table border="0" cellpadding="2" cellspacing="0" align="left">
          ''' % (np.min(ALLDATA[:,0]), np.max(ALLDATA[:,0]), StaName[0])
    for i in range(0, len(FIELDS)-1):
         nonan = sum(np.isnan(ALLDATA[:, i+3]))
         LOG += '''
                <tr>
                  <td align="left">%s</td>
                  <td align="left" width=20>:</td>          
                  <td align="right">%d/%d</td>
                  <td align="center">(%0.1f%%)</td>
                </tr>
                ''' % (FIELDS[i], nonan, ndata, nonan/ndata*100)
               
#    nonan = np.sum(np.isnan(ALLDATA[:, 3:]))
#    LOG += '''
#             <tr></tr>
#             <tr>
#               <td align="left">%s</td>
#               <td align="left" width=10>:</td>
#               <td align="right">%d/%d</td>
#               <td align="center">(%0.1f%%)</td>
#             </tr>
#           </table>
#           ''' % (FIELDS[-1], nonan, Ndata, nonan/Ndata*100)
    
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
        
if __name__ == '__main__':
    
    app = QtGui.QApplication(argv) 
    
    instance1 = dwnldWeather()   

    instance1.set_workdir("../Projects/Project4Testing")
    instance1.search4stations.lat_spinBox.setValue(45.4)
    instance1.search4stations.lon_spinBox.setValue(73.13)
    
    instance1.show()
    
#    instance1.load_stationList("../Projects/Project4Testing/weather_stations.lst")
        
    app.exec_()