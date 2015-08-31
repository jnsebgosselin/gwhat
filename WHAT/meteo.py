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
along with this program.  If not, see <http://www.gnu.org/licenses/>.

last_modification = 15/06/2015
"""
      
#----- STANDARD LIBRARY IMPORTS -----
       
import csv
from calendar import monthrange
from sys import argv
import os
from os import path
from datetime import date
#import copy
#import time


#----- THIRD PARTY IMPORTS -----

from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

import numpy as np
from PySide import QtGui, QtCore

import matplotlib as mpl
mpl.rcParams['backend.qt4']='PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
#import matplotlib.pyplot as plt

#---- PERSONAL IMPORTS ----

import database as db

class LabelDataBase():  
    
    
    def __init__(self, language):
        
        self.ANPRECIP = 'Annual Total Precipitation (mm)'
        self.ANTEMP = u'Average Annual Air Temperature (°C)'
        
        self.month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        
        if language == 'French':
            'Option not available at the moment'
            
class Tooltips():
    
    def __init__(self, language): #--------------------------------- ENGLISH --
        
        self.save = 'Save graph'
        self.open = "Open a valid '.out' weather data file"
        self.addTitle = 'Add A Title To The Figure Here (Option not yet available)'
        
        if language == 'French': #----------------------------------- FRENCH --
            
            pass

#==============================================================================
class WeatherAvgGraph(QtGui.QWidget):                       # WeatherAvgGraph #
#==============================================================================

    """
    GUI that allows to plot weather normals, save the graphs to file, see
    various stats about the dataset, etc...
    """
    
    def __init__(self, parent=None):
        super(WeatherAvgGraph, self).__init__(parent)        
        self.setWindowFlags(QtCore.Qt.Window)
#        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.initUI()
        
    def initUI(self): #========================================================
        
        iconDB = db.Icons()
        StyleDB = db.styleUI()
        ttipDB = Tooltips('English')
        self.station_name = []
        self.save_fig_dir = os.getcwd()
        self.meteo_dir = os.getcwd()
        
        self.setWindowTitle('Weather Averages')
        self.setFont(StyleDB.font1)
        self.setWindowIcon(iconDB.WHAT)
             
        #--------------------------------------------------------- TOOLBAR ----
        
        btn_save = QtGui.QToolButton()
        btn_save.setAutoRaise(True)
        btn_save.setIcon(iconDB.save)
        btn_save.setToolTip(ttipDB.save)
        btn_save.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_save.setIconSize(StyleDB.iconSize)
        btn_save.clicked.connect(self.save_graph)
        
        btn_open = QtGui.QToolButton()
        btn_open.setAutoRaise(True)
        btn_open.setIcon(iconDB.openFile)
        btn_open.setToolTip(ttipDB.open)
        btn_open.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_open.setIconSize(StyleDB.iconSize)
        btn_open.clicked.connect(self.select_meteo_file)
        
#        self.graph_title = QtGui.QLineEdit()
#        self.graph_title.setMaxLength(65)
#        self.graph_title.setEnabled(False)
#        self.graph_title.setText('Add A Title To The Figure Here')
#        self.graph_title.setToolTip(ttipDB.addTitle)
#        self.graph_title.setFixedHeight(StyleDB.size1)
#        
#        self.graph_status = QtGui.QCheckBox()
#        self.graph_status.setEnabled(False)
        
#        separator1 = QtGui.QFrame()
#        separator1.setFrameStyle(StyleDB.VLine)
        
        subgrid_toolbar = QtGui.QGridLayout()
        toolbar_widget = QtGui.QWidget()
        
        row = 0
        col = 0
        subgrid_toolbar.addWidget(btn_save, row, col)
        col += 1
        subgrid_toolbar.setColumnStretch(col, 4)
                
        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)
            
        toolbar_widget.setLayout(subgrid_toolbar)
        
        #--------------------------------------------------------- MAIN GRID --
        
        #-- widgets --
        
        self.fig_weather_normals = FigWeatherNormals()
        
        #-- layout --
        
        mainGrid = QtGui.QGridLayout()
        
        row = 0 
        mainGrid.addWidget(toolbar_widget, row, 0)
        row += 1
        mainGrid.addWidget(self.fig_weather_normals, row, 0)
                
        mainGrid.setContentsMargins(10, 10, 10, 10) # Left, Top, Right, Bottom 
        mainGrid.setSpacing(10)
        mainGrid.setRowStretch(1, 500)
        mainGrid.setColumnStretch(0, 500)
        
        self.setLayout(mainGrid)
                
    def generate_graph(self, filename): #==================== generate_graph ==
        
        #-- load data from data file --
        
        METEO = MeteoObj()
        METEO.load_and_format(filename)
        
        #-- set window name --
        
        self.station_name = METEO.STA
        self.setWindowTitle('Weather Averages for %s' % self.station_name)
        
        #-- calulate and plot weather normals --
        
        # DATA = [YEAR, MONTH, DAY, TMAX, TMIN, TMEAN, PTOT, {ETP}, {RAIN}]
 
        NORMALS = calculate_normals(METEO.DATA, METEO.datatypes)
        
        self.fig_weather_normals.plot_monthly_normals(NORMALS)                
        self.fig_weather_normals.draw()

    def save_graph(self): #====================================== save_graph ==
        
        dialog_dir = self.save_fig_dir
        dialog_dir += '/WeatherAverages_%s' % self.station_name
        
        dialog = QtGui.QFileDialog()
        dialog.setConfirmOverwrite(True)
        filename, ftype = dialog.getSaveFileName(caption="Save Figure",
                                                 dir=dialog_dir,
                                                 filter=('*.pdf'))
                                  
        if filename:
            if filename[-4:] != ftype[1:]: 
                # Add a file extension if there is none.
                filename = filename + ftype[1:]
                
            self.save_fig_dir = path.dirname(filename)    
            self.fig_weather_normals.figure.savefig(filename)   

    def select_meteo_file(self):
        dialog_dir = self.meteo_dir
        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                            'Select a valid weather data file', 
                                            dialog_dir, '*.out') 
                                   
        if filename:
            self.generate_graph(filename)
            self.meteo_dir = path.dirname(filename)
            
    def show(self): #================================================== show ==
        super(WeatherAvgGraph, self).show()    
        self.raise_()
        # self.activateWindow()
        
        qr = self.frameGeometry()
        if self.parentWidget():
            print('coucou')
            wp = self.parentWidget().frameGeometry().width()
            hp = self.parentWidget().frameGeometry().height()
            cp = self.parentWidget().mapToGlobal(QtCore.QPoint(wp/2., hp/2.))        
        else:
            cp = QtGui.QDesktopWidget().availableGeometry().center()            
        qr.moveCenter(cp)                    
        self.move(qr.topLeft())           
        self.setFixedSize(self.size())
        
            
#==============================================================================        
class MeteoObj():    
    """
    This is a class to load and manipulate weather data.
    
    nan are assigned a value of 0 for Ptot and for air Temp, the value is 
    calculated with an in-station interpolation.
    """
#==============================================================================    

    def __init__(self):
        
        self.filename = ''
        
        self.STA = 'Station Name'
        self.LAT = 'Latitude'
        self.LON = 'Longitude'
        self.PRO = 'Province'
        self.ALT = 'Elevation'
        self.CID = 'Climate Identifier'
                
        self.STADESC = [[None] * 6, [None] * 6] # station description

        self.STADESC[0] = ['Station Name', 'Latitude', 'Longitude', 
                           'Province', 'Elevation', 'Climate Identifier']
        
        self.INFO = []
        
        self.varnames = []
        
        self.datatypes = []        
        # 0 -> not cumulative data:
        #      ex.: Air Temperature
        #           Air humidity)
        # 1 -> cumulative data:
        #      ex.: Precipitation, ETP
        
        self.HEADER = []        
        self.DATA = []
        
        self.TIME = [] # Time in numeric format.

        
    def load_and_format(self, filename): #=====================================
        
        #---- load data from file ----
        
        self.load(filename)
        self.build_HTML_table()
        
        #---- clean data ----
        
        self.clean_endsof_file()
        self.check_time_continuity()
        self.get_TIME(self.DATA[:, :3])        
        self.fill_nan()
        
        #---- add ETP and RAIN ----
        
        self.add_ETP_to_data()
        self.add_rain_to_data()
                
                
    def load(self, filename): #================================================
        
        """
        Load the info related to the weather station, the date and weather
        datasets 'as is' from the file.
        """
        
        self.filename = filename
        
        labels = np.array(self.STADESC[0])

        with open(filename, 'r') as f:
            reader = list(csv.reader(f, delimiter='\t'))
        
        #---- get info from header and find row where data starts ----
        
        for i in range(len(reader)):
            
            if len(reader[i]) > 0 :
                
                if  reader[i][0] == 'Year':
                    self.varnames = reader[i]
                    data_indx = i + 1
                    self.HEADER = reader[:data_indx]
                    break
                
                if np.any(labels == reader[i][0]):
                    indx = np.where(labels == reader[i][0])[0]
                    self.STADESC[1][indx] = reader[i][1]
        
        #---- Update class variables ----
       
        [self.STA, self.LAT, self.LON,
         self.PRO, self.ALT, self.CID] = self.STADESC[1]
                    
        # DATA = [Year, Month, Day, Tmax, Tmin, Tmean, PTOT, {ETP}, {RAIN}]
        self.DATA = np.array(reader[data_indx:]).astype('float')
        
        #---- assign a datatype to each variables ----
        
        datatype0 = ['Max Temp (deg C)', 'Min Temp (deg C)',
                     'Mean Temp (deg C)']
        datatype1 = ['Total Precip (mm)', 'Rain (mm)', 'ETP (mm)']
        
        nvar = len(self.DATA[0, 3:])
        self.datatypes = [0] * nvar
        varname = self.varnames[3:]
        
        for i in range(nvar):
            if varname[i] in datatype0:
                self.datatypes[i] = 0
            elif varname[i] in datatype1:
                self.datatypes[i] = 1
            else:
                self.datatypes[i] = 0
        
            
    def clean_endsof_file(self): #============================================
        
        """
        Remove nan values at the beginning and end of the record if any. Must
        not be run before the 'TIME' array is generated.
        """
        
        #---- Beginning ----
        
        n = len(self.DATA[:, 0])
        for i in range(len(self.DATA[:, 0])):
            if np.all(np.isnan(self.DATA[i, 3:])):
                self.DATA = np.delete(self.DATA, i, axis=0)                 
            else:
                break
            
        if n < len(self.DATA[:, 0]):
            print('%d empty' % (n - len(self.DATA[:, 0])) +
                  ' rows of data removed at the beginning of the dataset.')
            
        #---- End ----
        
        n = len(self.DATA[:, 0])
        for i in (n - np.arange(n) - 1):  
            if np.all(np.isnan(self.DATA[i, 3:])):
                self.DATA = np.delete(self.DATA, i, axis=0)
            else:
                break 
            
        if n < len(self.DATA[:, 0]):
            print('%d empty' % (n - len(self.DATA[:, 0])) +
                  ' rows of data removed at the end of the dataset.')
        
        
    def check_time_continuity(self): #========================================
            
        #------------------------------------------ check time continuity ----
        
        # Check if the data series is continuous over time and 
        # correct it if not
        
        time_start = xldate_from_date_tuple((self.DATA[0, 0].astype('int'),
                                             self.DATA[0, 1].astype('int'),
                                             self.DATA[0, 2].astype('int')), 0)

        time_end = xldate_from_date_tuple((self.DATA[-1, 0].astype('int'),
                                           self.DATA[-1, 1].astype('int'),
                                           self.DATA[-1, 2].astype('int')), 0)
        
        if time_end - time_start + 1 != len(self.DATA[:,0]):
            print('%s is not continuous, correcting...' % self.STA)
            self.DATA = make_timeserie_continuous(self.DATA)        
    
    
    def get_TIME(self, DATE): #================================================
        
        # Generate a 1D array with date in numeric format because it is not
        # provided in the '.out' files.        
        
        N = len(DATE[:, 0])
        TIME = np.zeros(N)
        for i in range (N):
            TIME[i] = xldate_from_date_tuple((DATE[i, 0].astype('int'),
                                              DATE[i, 1].astype('int'),
                                              DATE[i, 2].astype('int')), 0)
        self.TIME = TIME
        
        return TIME
        
    def fill_nan(self): #======================================================
        
        datatypes = self.datatypes
        varnames = self.varnames[3:]
        nvar = len(varnames)
        X = np.copy(self.DATA[:, 3:])
        TIME = np.copy(self.TIME)
       
        # preferable to be run before ETP or RAIN is estimated, So that 
        # there is no missing value in both of these estimated time series. 
        # However, it needs to be ran after but after 'check_time_continuity'.
        
        #---- Fill Temperature based variables ----
        
        print(datatypes)
        
        for var in range(nvar):
        
            nanindx = np.where(np.isnan(X[:, var]))[0]
            if len(nanindx) > 0:        
                                      
                if datatypes[var] == 0:
                    
                    nonanindx = np.where(~np.isnan(X[:, var]))[0]
                    X[:, var] = np.interp(TIME, TIME[nonanindx], 
                                          X[:, var][nonanindx]) 
                                          
                    print('There was %d nan values' % len(nanindx) +
                          ' in %s series.' % varnames[var]  +
                          ' Missing values estimated through a' +
                          ' linear interpolation.')
                      
                elif datatypes[var] == 1:
                    
                    X[:, var][nanindx] = 0   
                    
                    print('There was %d nan values' % len(nanindx) +
                          ' in %s series.' % varnames[var] +
                          ' Missing values are assigned a 0 value.')
                                           
        self.DATA[:, 3:] = X
        
        
    def add_rain_to_data(self): #==============================================
       
        varnames = np.array(self.varnames)
        if np.any(varnames == 'Rain (mm)'):
            print('Already a Rain time series in the datasets.')
            return
        
        #---- get PTOT and TAVG from data ----
        
        indx = np.where(varnames == 'Total Precip (mm)')[0][0]
        PTOT = np.copy(self.DATA[:, indx])
        
        indx = np.where(varnames == 'Mean Temp (deg C)')[0][0]
        TAVG = np.copy(self.DATA[:, indx])
        
        #---- estimate rain ----
        
        RAIN = np.copy(PTOT)
        RAIN[np.where(TAVG < 0)[0]] = 0
        RAIN = RAIN[:, np.newaxis]
        
        #---- extend data ----
        
        self.DATA = np.hstack([self.DATA, RAIN])        
        self.varnames.append('Rain (mm)')
        self.datatypes.append(1)


    def add_ETP_to_data(self): #===============================================
        
        varnames = np.array(self.varnames)
        if np.any(varnames == 'ETP (mm)'):
            print('Already a ETP time series in the datasets.')
            return
        
        #---- assign local variable ----
        
        DATE = np.copy(self.DATA[:, :3])
        LAT = np.copy(float(self.LAT))

        indx = np.where(varnames == 'Mean Temp (deg C)')[0][0]
        TAVG = np.copy(self.DATA[:, indx])
        
        #---- compute normals ----
        
        NORMALS = calculate_normals(self.DATA, self.datatypes)        
        Ta = NORMALS[:, 2] # monthly air temperature averages (deg Celcius)
        
        ETP = calculate_ETP(DATE, TAVG, LAT, Ta)
        ETP = ETP[:, np.newaxis]

        #---- extend data ----

        self.DATA = np.hstack([self.DATA, ETP])                
        self.varnames.append('ETP (mm)')
        self.datatypes.append(1)
        
    def build_HTML_table(self): #==============================================
        
        # HTML table with the info related to the weather station.
        
        
        FIELDS = self.STADESC[0]
        VALIST = self.STADESC[1]
        UNITS =  ['', '&deg;', '&deg;','', ' m', '']
                          
        info = '<table border="0" cellpadding="2" cellspacing="0" align="left">'
        for i in range(len(FIELDS)):
            
            try:                 
                VAL = '%0.1f' % float(VALIST[i])
            except:
                VAL = VALIST[i]
                 
            info += '''<tr>
                         <td width=10></td>
                         <td align="left">%s</td>
                         <td align="left" width=20>:</td>
                         <td align="left">%s%s</td>
                       </tr>''' % (FIELDS[i], VAL, UNITS[i])
        info += '</table>'
        
        self.INFO = info
        
        return info
        
           
#    def daily2weekly(self): #=================================================        
#        
#        # THIS METHOD NEEDS UPDATING! Currently, it seems it it not used at all.
#        
#        bwidth = 7.
#        nbin = np.floor(len(TIME) / bwidth)
#        
#        TIMEbin = TIME[:nbin*bwidth].reshape(nbin, bwidth)
#        TIMEbin = np.mean(TIMEbin, axis=1)
#      
#        TMAXbin = TMAX[:nbin*bwidth].reshape(nbin, bwidth)
#        TMAXbin = np.mean(TMAXbin, axis=1)
#        
#        PTOTbin = PTOT[:nbin*bwidth].reshape(nbin, bwidth)
#        PTOTbin = np.sum(PTOTbin, axis=1)
#        
#        RAINbin = RAIN[:nbin*bwidth].reshape(nbin, bwidth)
#        RAINbin = np.sum(RAINbin, axis=1)
#        
#        nres = len(TIME) - (nbin * bwidth)
#        print 'Nbin residual =', nres
#                
#        #---------------------------------------- update class variables ----
#
#        self.TIMEwk = TIMEbin
#        self.TMAXwk = TMAXbin
#        self.PTOTwk = PTOTbin
#        self.RAINwk = RAINbin
        
        
#=============================================================================
def make_timeserie_continuous(DATA):
    """
    This function is called when a time serie of a daily meteorological record
    is found to be discontinuous over time.

    <make_timeserie_continuous> will scan the entire time serie and will insert
    a row with nan values whenever there is a gap in the data and will return
    the continuous data set.
   
    DATA = [YEAR, MONTH, DAY, VAR1, VAR2 ... VARn]

           2D matrix containing the dates and the corresponding daily 
           meteorological data of a given weather station arranged in 
           chronological order. 
    """
#=============================================================================    
    
    nVAR = len(DATA[0,:]) - 3 # nVAR = number of meteorological variables
    nan2insert = np.zeros(nVAR) * np.nan    
   
    i = 0
    date1 = xldate_from_date_tuple((DATA[i, 0].astype('int'),
                                    DATA[i, 1].astype('int'),
                                    DATA[i, 2].astype('int')), 0)
    
                                   
    while i < len(DATA[:, 0]) - 1:
        
        date2 = xldate_from_date_tuple((DATA[i+1, 0].astype('int'),
                                        DATA[i+1, 1].astype('int'),
                                        DATA[i+1, 2].astype('int')), 0)
        
        # If dates 1 and 2 are not consecutive, add a nan row to DATA
        # after date 1.                                
        if date2 - date1 > 1:            
            date2insert = np.array(xldate_as_tuple(date1 + 1, 0))[:3]
            row2insert = np.append(date2insert, nan2insert)          
            DATA = np.insert(DATA, i + 1, row2insert, 0)
        
        date1 += 1            
        i += 1

    return DATA
                

#=============================================================================
def calculate_normals(DATA, datatypes):    
    """
    Calculates monthly normals from daily average air temperature and
    total daily precipitation time series. 
    
    It is assumed that the datased passed through DATA is complete, in 
    chronological order, without ANY missing value.
    
    {2d numpy matrix} DATA = Rows are the time and columns are the variables.
    
                             The first three should be a time series containing
                             the year, month, an day of the month, respectively.
                             
                             The remaining columns should contains the weather 
                             data. 1 columnd -> 1 weather variable. 
    
    {1d list} datatype = This is the type of data for which normals are being
                         calculated. It defines the operation that is goind to
                         be done to compute the normals. If this value is 
                         None, all variable are assumed to be of type 0.
    
                         0 -> need to be averaged over a month 
                              (e.g. Air Temperature, air humidity)
                               
                         1 -> need to be summed over a month 
                              (e.g. Precipitation, ETP)
    """
#===============================================================================    
        
    print('---- calculating normals ----') 
     
    #---- assign new variables from input ----

    nvar = len(DATA[0, 3:]) # number of weather variables
    
    if datatypes == None or len(datatypes) < nvar:
        print('datatype incorrect or non existent. Assuming all variables to ' +
              'be of type 0')
        datatypes = [0] * nvar
    
    YEAR = DATA[:, 0].astype(int)
    MONTH = DATA[:, 1].astype(int)
    X = DATA[:, 3:]
   
    #---------------------------------------- Do each month, for every year ----
    
    # Calculate the average value for each months of each year
    
    nyear = np.ptp(YEAR) + 1
      
    XMONTH = np.zeros((nyear, 12, nvar)) * np.nan
    for k in range(nvar):  
        Xk = X[:, k]
        for j in range(nyear):
            for i in range(12):
            
                indx = np.where((YEAR == j+YEAR[0]) & (MONTH == i+1))[0]
                Nday = monthrange(j+YEAR[0], i+1)[1] 
           
                if len(indx) < Nday:
                    # Default nan value will be kept in XMONTH. 
                
                    print('Month %d of year %d is incomplete'
                          % (i+1, j+YEAR[0]))
                  
                else:
                    
                    if datatypes[k] == 0:
                        XMONTH[j, i, k] = np.mean(Xk[indx])
                    elif datatypes[k] == 1:
                        XMONTH[j, i, k] = np.sum(Xk[indx])

    #---------------------------------------------- compute monthly normals ----
    
    # Calculate the normals for each month. This is done by calculating the
    # mean of the monthly value computed in the above section.
    
    XNORM = np.zeros((12, nvar)) * np.nan
    
    for k in range(nvar):
        for i in range(12):
        
            indx = np.where(~np.isnan(XMONTH[:, i, k]))[0]
        
            if len(indx) > 0:
            
                XNORM[i, k] = np.mean(XMONTH[indx, i, k])
            
            else:

                # Default nan value is kept in the array.
        
                print('WARNING, some months are empty because of lack of data.')
    
    return XNORM
        

#===============================================================================
def calculate_ETP(DATE, TAVG, LAT, Ta):
    """
    Daily potential evapotranspiration (mm) is calculated with a method adapted
    from Thornwaite (1948).
    
    Requires at least a year of data.
    
    #----- INPUT -----
    
    {1d numpy array} TIME = Numeric time in days
    {1d numpy array} TAVG = Daily temperature average (deg C)
    {float}          LAT = Latitude in degrees
    {1d numpy array} Ta = Monthly air temperature normals
    
    #----- OUTPUT -----

    {1d numpy array} ETP: Daily Potential Evapotranspiration (mm)    
    
    #----- SOURCE -----
    
    Pereira, A.R. and W.O. Pruitt. 2004. Adaptation of the Thornthwaite scheme
        for estimating daily reference evapotranspiration. Agricultural Water
        Management, 66, 251-257.
    """
#===============================================================================

    Ta[Ta < 0] = 0   
    
    I = np.sum((0.2 * Ta) ** 1.514) # Heat index
    a = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.7912e-2 * I) + 0.49239
    
    TAVG[TAVG < 0] = 0
    
    DAYLEN = calculate_daylength(DATE, LAT) # Photoperiod in hr
    
    ETP = 16 * (10 * TAVG / I)**a * (DAYLEN / (12. * 30))
       
    return ETP
    
    
#===============================================================================   
def calculate_daylength(DATE, LAT):
    """
    Calculate the photoperiod for the given latitude at the given time.
    
    #----- INPUT -----
    
    {1D array} TIME = Numeric time in days.
    {float}     LAT = latitude in decimal degrees.
    
    #----- OUTPUT -----
    
    {1D array} DAYLEN = photoperiod in hr.    
    """
#===============================================================================
    
    DATE = DATE.astype(int)
    pi = np.pi    
    LAT = np.radians(LAT) # Latitude in rad
    
    #----- CONVERT DAY FORMAT -----
    
    # http://stackoverflow.com/questions/13943062
    
    N = len(DATE[:, 0])
    DAY = np.zeros(N)    
    for i in range(N):
        DAY[i] = int(date(DATE[i, 0], DATE[i, 1],DATE[i, 2]).timetuple().tm_yday)
        DAY[i] = int(DAY[i])
        
    #------------------------------------------------ DECLINATION OF THE SUN --    
    
    # http://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations

    N = DAY - 1
    
    A = 2 * pi / 365.24 * (N - 2)
    B = 2 * pi / pi * 0.0167
    C = 2 * pi / 365.24 * (N + 10)
    
    D = -23.44 * pi / 180.
            
    SUNDEC = np.arcsin(np.sin(D) * np.cos(C + B * np.sin(A)))
    
    #------------------------------------------------------ SUNRISE EQUATION --

    # http:/Omega/en.wikipedia.org/wiki/Sunrise_equation

    OMEGA = np.arccos(-np.tan(LAT) * np.tan(SUNDEC))
    
    #-------------------------------------------------------- HOURS OF LIGHT --
    
    # http://physics.stackexchange.com/questions/28563/
    #        hours-of-light-per-day-based-on-latitude-longitude-formula
    
    DAYLEN = OMEGA * 2 * 24 / (2 * np.pi) # Day length in hours
    
    return DAYLEN

#==============================================================================
class FigWeatherNormals(FigureCanvasQTAgg):               # FigWeatherNormals #
#==============================================================================
    def __init__(self):
        
        fw, fh = 8.5, 5.
        fig = mpl.figure.Figure(figsize=(fw, fh), facecolor='white')
        
        super(FigWeatherNormals, self).__init__(fig)
                
        #---------------------------------------------------- Define Margins --
       
        labelDB = LabelDataBase('English')        
        month_names = labelDB.month_names
        
        left_margin = 1 / fw
        right_margin = 1 / fw
        bottom_margin = 0.35 / fh
        top_margin = 0.1 / fh
                     
        #--------------------------------------------- Yearly Avg Labels Axe --
        
        ax3 = fig.add_axes([0, 0, 1, 1], zorder=1)     
        ax3.patch.set_visible(False)
        ax3.tick_params(axis='both', bottom='off', top='off',
                                     labelbottom='off', labeltop='off',
                                     left='off', right='off',
                                     labelleft='off', labelright='off')
        ax3.spines['bottom'].set_visible(False)
        
        #-- Mean Annual Avg Labels --
        
        # place first label at the top left corner of ax1 with a horizontal
        # and vertical padding of 3 points.
        
        padding = mpl.transforms.ScaledTranslation(5/72., -3/72., 
                                                   fig.dpi_scale_trans)        
        transform = ax3.transAxes + padding
        
        ax3.text(0., 1., 'Mean Annual Air Temperature', 
                 fontsize=13, va='top', transform=transform)
                                  
        # place second label below the first label with a vertical padding
        # of 3 points.
                                  
        renderer = self.get_renderer()                     
        bbox = ax3.texts[0].get_window_extent(renderer)
        bbox = bbox.transformed(ax3.transAxes.inverted())
                                  
        ax3.text(0., bbox.y0, 'Mean Annual Precipitation', 
                 fontsize=13, va='top', transform=transform)
        
        bbox = ax3.texts[1].get_window_extent(renderer)
        bbox = bbox.transformed(fig.transFigure.inverted())
        
        #-- update geometry --

        x0 = left_margin
        w0 = 1 - (left_margin + right_margin)
        h0 = 1 - bbox.y0 + (3/72. / fw)
        y0 = 1 - h0 - top_margin
        
        ax3.set_position([x0, y0, w0, h0])
        
        #--------------------------------------------------------- Data Axes --
        
        h0 = y0 - bottom_margin
        y0 = y0 - h0
        
        #-- Precip --
        
        ax0  = fig.add_axes([x0, y0, w0, h0], zorder=1)
        ax0.patch.set_visible(False)
        ax0.spines['top'].set_visible(False)
        ax0.set_axisbelow(True)
        
        #-- Air Temp. --
        
        ax1 = fig.add_axes(ax0.get_position(), frameon=False, zorder=5, 
                           sharex=ax0)
                                                           
        #------------------------------------------------------ INIT ARTISTS --
                
        XPOS = np.arange(-0.5, 12.51, 1) 
        y = range(len(XPOS))
        colors = ['#990000', '#FF0000', '#FF6666']
        
        #-- Tmax --
        
        ax1.plot(XPOS, y, color=colors[0], clip_on=True, ls='--', lw=1.5,
                          zorder=100)
                                
        #-- Tmean --
        
        ax1.plot(XPOS, y, color=colors[1], clip_on=True, marker='o', ls='--',
                          ms=6, zorder=100, mec=colors[1], mfc='white',
                          mew=1.5, lw=1.5)
        
        
        #-- Tmin --
                                
        ax1.plot(XPOS, y, color=colors[2], clip_on=True, ls='--', lw=1.5,
                          zorder=100)
        
        #-------------------------------------------------- XTICKS FORMATING -- 
    
        Xmin0 = 0
        Xmax0 = 12.001
        
        #-- major --
        
        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x',direction='out')
        ax0.xaxis.set_ticklabels([])
        ax0.set_xticks(np.arange(Xmin0, Xmax0))
        
        ax1.tick_params(axis='x', which='both', bottom='off', top='off',
                        labelbottom='off')
        
        #-- minor --
        
        ax0.set_xticks(np.arange(Xmin0+0.5, Xmax0+0.49, 1), minor=True)
        ax0.tick_params(axis='x', which='minor', direction='out',
                        length=0, labelsize=13)
        ax0.xaxis.set_ticklabels(month_names, minor=True)
        
        #-------------------------------------------------------------- GRID --
        
    #    ax0.grid(axis='y', color=[0.5, 0.5, 0.5], linestyle=':', linewidth=1,
    #             dashes=[1, 5])
    #    ax0.grid(axis='y', color=[0.75, 0.75, 0.75], linestyle='-',
#                 linewidth=0.5)
        
        #------------------------------------------------------------- XLIMS --
                             
        ax0.set_xlim(Xmin0, Xmax0)
        
        #------------------------------------------------------- Plot Legend --
        
        self.plot_legend()
                             
    def plot_monthly_normals(self, NORMALS, COLOR=['black', 'black']):
        
        #-------------------------------------------- assign local variables --
    
        Tmax_norm = NORMALS[:, 0]
        Tmin_norm = NORMALS[:, 1]
        TNORM = NORMALS[:, 2]
        PNORM = NORMALS[:, 3]
        RNORM = NORMALS[:, -1]        
        SNORM = PNORM - RNORM
    
        #------------------------------------------------- DEFINE AXIS RANGE --
    
        if np.sum(PNORM) < 500:
            Yscale0 = 10 # Precipitation (mm)
        else:
            Yscale0 = 20
            
        Yscale1 = 5 # Temperature (deg C)
        
        SCA0 = np.arange(0, 10000, Yscale0)
        SCA1 = np.arange(-100, 100, Yscale1)
        
        #-- Precipitation --
        
        indx = np.where(SCA0 > np.max(PNORM))[0][0]   
        Ymax0 = SCA0[indx+1]
        
        indx = np.where(SCA0 <= np.min(SNORM))[0][-1]
        Ymin0 = SCA0[indx]
        
        NZGrid0 = (Ymax0 - Ymin0) / Yscale0
        
        #-- Temperature --
        
        indx = np.where(SCA1 > np.max(Tmax_norm))[0][0]
        Ymax1 = SCA1[indx]
        
        indx = np.where(SCA1 < np.min(Tmin_norm))[0][-1]
        Ymin1 = SCA1[indx]
        
        NZGrid1 = (Ymax1 - Ymin1) / Yscale1
        
        #-- Uniformization Of The Grids --
        
        if NZGrid0 > NZGrid1:    
            Ymin1 = Ymax1 - NZGrid0 * Yscale1
        elif NZGrid0 < NZGrid1:
            Ymax0 = Ymin0 + NZGrid1 * Yscale0
        elif NZGrid0 == NZGrid1:
            pass
        
        #-- Adjust Space For Text --
        
#        # In case there is a need to force the value
#        #----
#        Ymax0 = 180 
#        Ymax1 = 25 ; Ymin1 = -20
#        #----
        
        #-------------------------------------------------- YTICKS FORMATING --

        ax0 = self.figure.axes[1]
        ax1 = self.figure.axes[2]
        
        #-- Precip (host) --
               
        yticks = np.arange(Ymin0, Ymax0 + Yscale0/10., Yscale0)
        ax0.yaxis.set_ticks_position('right') 
        ax0.set_yticks(yticks)
        ax0.tick_params(axis='y', direction='out', labelcolor=COLOR[1],
                        labelsize=13)
        
        yticks_minor = np.arange(yticks[0], yticks[-1], 5)
        ax0.set_yticks(yticks_minor, minor=True)
        ax0.tick_params(axis='y', which='minor', direction='out')
        ax0.yaxis.set_ticklabels([], minor=True)
        
        #-- Air Temp --
        
        yticks1 = np.arange(Ymin1, Ymax1 + Yscale1/10., Yscale1)    
        ax1.yaxis.set_ticks_position('left')
        ax1.set_yticks(yticks1)
        ax1.tick_params(axis='y', direction='out', labelcolor=COLOR[0],
                        labelsize=13)
        
        yticks1_minor = np.arange(yticks1[0], yticks1[-1], Yscale1/5.)
        ax1.set_yticks(yticks1_minor, minor=True)
        ax1.tick_params(axis='y', which='minor', direction='out')
        ax1.yaxis.set_ticklabels([], minor=True)
        
        #---------------------------------------------------- SET AXIS RANGE -- 

        ax0.set_ylim(Ymin0, Ymax0)
        ax1.set_ylim(Ymin1, Ymax1)
        
        #------------------------------------------------------------ LABELS --

        ax0.set_ylabel('Monthly Total Precipication (mm)', va='bottom',
                       fontsize=16, color=COLOR[1], rotation=270)                            
        ax0.yaxis.set_label_coords(1.09, 0.5)
        
        ax1.set_ylabel(u'Monthly Mean Air Temperature (°C)', va='bottom',
                       fontsize=16, color=COLOR[0])        
        ax1.yaxis.set_label_coords(-0.09, 0.5)
        
        #---------------------------------------------------------- PLOTTING --
        
        self.plot_precip(PNORM, SNORM)
        self.plot_air_temp(Tmax_norm, Tmin_norm, TNORM)
        self.update_yearly_avg(TNORM, PNORM)
        
    def plot_precip(self, PNORM, SNORM): #====================== plot_precip ==
        
        #-- define vertices manually --
        
        Xmid = np.arange(0.5, 12.5, 1)                
        n = 0.5
        f = 0.65 # Space between individual bar.
        
        Xpos = np.vstack((Xmid - n * f,
                          Xmid - n * f,
                          Xmid + n * f,
                          Xmid + n * f)).transpose().flatten()
        
        Ptot = np.vstack((PNORM * 0,
                          PNORM,
                          PNORM,
                          PNORM * 0)).transpose().flatten()
        
        Snow = np.vstack((SNORM * 0,
                          SNORM,
                          SNORM,
                          SNORM * 0)).transpose().flatten()
        
        #-- plot data --
        
        ax = self.figure.axes[1]
        
        for collection in reversed(ax.collections):
            collection.remove()
            
        ax.fill_between(Xpos, 0., Ptot, edgecolor='none', 
                        color=db.styleUI().rain)
        ax.fill_between(Xpos, 0., Snow, edgecolor='none',
                        color=db.styleUI().snow)
            
    def plot_air_temp(self, Tmax_norm, Tmin_norm, Tmean_norm): #===============
                        
        #---- Air Temperature ----
        
        Tmean_norm = np.hstack((Tmean_norm[-1], Tmean_norm, Tmean_norm[0]))
        Tmin_norm = np.hstack((Tmin_norm[-1], Tmin_norm, Tmin_norm[0]))
        Tmax_norm = np.hstack((Tmax_norm[-1], Tmax_norm, Tmax_norm[0]))
        TNORM = [Tmax_norm, Tmean_norm, Tmin_norm]
        
        for i in range(3):        
        
            self.figure.axes[2].lines[i].set_ydata(TNORM[i])
#        
#        self.Tplot2.set_ydata(Tmax_norm)
#        self.Tplot1.set_ydata(Tmean_norm)      
#        self.Tplot3.set_ydata(Tmin_norm)
        
    def update_yearly_avg(self, TNORM, PNORM): #========== update_yearly_avg ==
        
        ax = self.figure.axes[0]
        
        #-- update position --
        
        bbox = ax.texts[0].get_window_extent(self.get_renderer())
        bbox = bbox.transformed(ax.transAxes.inverted())
        
        ax.texts[1].set_position((0, bbox.y0))
        
        #-- update labels --
        
        ax.texts[0].set_text(u'Mean Annual Air Temperature = %0.1f °C' % 
                             np.mean(TNORM))
                         
        ax.texts[1].set_text(u'Mean Annual Precipitation = %0.1f mm' % 
                             np.sum(PNORM))
                             
    def plot_legend(self): #==================================== plot_legend ==
        
        ax = self.figure.axes[2] # Axe on which the legend is hosted
        
        #-- bbox transform --
        
        padding = mpl.transforms.ScaledTranslation(5/72., -5/72., 
                                                   self.figure.dpi_scale_trans)        
        transform = ax.transAxes + padding
        
        #-- proxy artists --
        
        rec1 = mpl.patches.Rectangle((0, 0), 1, 1, fc=db.styleUI().snow, 
                                                   ec='none')
        rec2 = mpl.patches.Rectangle((0, 0), 1, 1, fc=db.styleUI().rain,
                                                   ec='none')
        
        #-- legend entry --
                
        lines = [ax.lines[0], ax.lines[1], ax.lines[2], rec2, rec1]
        labels = ['Max Temp.', 'Mean Temp.', 'Min. Temp.', 'Rain', 'Snow']
        
        #-- plot legend --
        
        leg = ax.legend(lines, labels, numpoints=1, fontsize=13,
                        borderaxespad=0, loc='upper left', borderpad=0,
                        bbox_to_anchor=(0, 1), bbox_transform=transform)                   
        leg.draw_frame(False)        

    
if __name__ == '__main__':
#    plt.rc('font',family='Arial')
    
    app = QtGui.QApplication(argv)   
                
#    fmeteo = "Files4testing/Daily - SASKATOON DIEFENBAKER & RCS_1980-2014.out"
#    fmeteo = "Files4testing/TORONTO LESTER B. PEARSON INT'L _1980-2010.out"
    fmeteo = "Files4testing/QUEBEC-JEAN LESAGE INTL A_1985-2005.out"
    
    w = WeatherAvgGraph()
    w.save_fig_dir =  '../Projects/Project4Testing'        
    w.show()
    w.generate_graph(fmeteo)
#    for i in range(250):
#        w.generate_graph(fmeteo)
#        QtCore.QCoreApplication.processEvents()
#        QtCore.QCoreApplication.processEvents()
    
    app.exec_()