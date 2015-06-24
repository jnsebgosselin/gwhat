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
from os import getcwd
import csv

#----- THIRD PARTY IMPORTS -----

import numpy as np
from PySide import QtGui, QtCore

#---- PERSONAL IMPORTS ----

import database as db

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
        
        self.savedir = getcwd()
        
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
        
        label_date = QtGui.QLabel('Stations with data between :')
        
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
        
        widget_rightPanel = QtGui.QWidget()
        grid_rightPanel = QtGui.QGridLayout()
        
        row = 0
        grid_rightPanel.addWidget(label_date, row, 0, 1, 3)
        row += 1
        grid_rightPanel.addWidget(self.minYear, row, 0)
        grid_rightPanel.addWidget(label_and, row, 1)
        grid_rightPanel.addWidget(self.maxYear, row, 2)
        
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
        
    #===========================================================================
    def btn_search_isClicked(self):
        '''
        Initiate the seach for weather stations. It grabs the info from the
        interface and send it to the method "search_envirocan".
        '''
    #===========================================================================
        
        #---- Close window ----
        
        self.close()

        #---- Generate New List ----
        # http://doc.qt.io/qt-5/qt.html#CursorShape-enum
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        self.ConsoleSignal.emit('''<font color=black>
                                     Searching for weather stations. Please
                                     wait...
                                   </font>''')
        print("Searching for weather stations. Please wait...")
                                     
        QtCore.QCoreApplication.processEvents()
        QtCore.QCoreApplication.processEvents()
        
        LAT = self.lat_spinBox.value()
        LON = self.lon_spinBox.value()
        RADIUS = self.radius_SpinBox.value()
        startYear = self.minYear.value()
        endYear = self.maxYear.value()
      
        self.search_envirocan(LAT, LON, RADIUS, startYear, endYear)
            
        QtGui.QApplication.restoreOverrideCursor()
  
    #===========================================================================
    def search_envirocan(self, LAT, LON, RADIUS, YearMin, YearMax):
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
            
        StationID = np.array(['stationId']) # to download the data from server
        Prov = np.array(['Province'])
        StartYear = np.array(['StartYear'])
        EndYear = np.array(['EndYear'])
        staName = np.array(['staName'])
        ClimateID = np.array(['ClimateID'])
        staProxim = np.array(['Proximity (km)'])
        
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
                print 'No weather stations found.'            
                cmt = '<font color=red>No weather stations found.</font>'
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
                        
                        if start_year.isdigit(): # Daily data exist
                           
                            print 'adding', station_name
    
                            StartYear = np.append(StartYear, start_year)
                            EndYear = np.append(EndYear, end_year)
                            StationID = np.append(StationID, station_id)
                            Prov = np.append(Prov, province)
                            staName = np.append(staName, station_name)
                            staProxim = np.append(staProxim, station_proxim)
                        else: # No Daily data  
                            pass
                
                print('%d weather stations with daily data.' % (len(staName)-1))                
                cmt = '''<font color=green>%d weather stations found with daily 
                           data.</font>''' % (len(staName) - 1)
                self.ConsoleSignal.emit(cmt)         
                QtCore.QCoreApplication.processEvents()
                QtCore.QCoreApplication.processEvents()
                   
                #------------------------------------------- Get Climate ID ----
                
                print('Fetching info for each station...')
                self.ConsoleSignal.emit('''<font color=black>
                                             Fetching info for each station...
                                           </font>''')  
                QtCore.QCoreApplication.processEvents()
                QtCore.QCoreApplication.processEvents()
                         
                for sta in range(1, len(staName)):
                    climate_id = get_climate_ID(Prov[sta], StationID[sta])
                    ClimateID = np.append(ClimateID, climate_id)
                
                #----------------------------- SORT STATIONS ALPHABETICALLY ----
    
                sort_indx = np.argsort(staName[1:])
                sort_indx += 1
                
                StartYear[1:] = StartYear[sort_indx]
                EndYear[1:] = EndYear[sort_indx]
                StationID[1:] = StationID[sort_indx]
                Prov[1:] = Prov[sort_indx]
                staName[1:] = staName[sort_indx]
                ClimateID[1:] = ClimateID[sort_indx]
                staProxim[1:] = staProxim[sort_indx]
                
                #-------------------------------------------- Save Results ----
                
                staList = [staName, StationID, StartYear, EndYear, Prov,
                   ClimateID, staProxim]
                staList = np.transpose(staList)
            
                fname = self.savedir + '/weather_stations.lst'    
                with open(fname, 'wb') as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerows(staList)
                    
                print("Saving results in %s" % fname)
                self.ConsoleSignal.emit('''<font color=black>
                                             Saving results in %s 
                                           </font>''' % fname)
                                   
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

if __name__ == '__main__':
    
    app = QtGui.QApplication(argv)  
    instance_1 = search4stations() 
    instance_1.show()
    instance_1.lat_spinBox.setValue(45.4)
    instance_1.lon_spinBox.setValue(73.13)
    app.exec_()