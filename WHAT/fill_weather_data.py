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

#---- STANDARD LIBRARY IMPORTS ----

import csv

#---- THIRD PARTY IMPORTS ----

import numpy as np
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

#---- PERSONAL IMPORTS ----

from meteo import make_timeserie_continuous

#===============================================================================
class Weather_File_Info():
    """
    <Input_File_Info> class contains all the weather data of multiple stations
    conveniently organized in a 3D matrix [i, j, k] to be easily manipulated
    inside a loop.

    layer k=1 : Maximum Daily Temperature
    layer k=2 : Minimum Daily Temperature
    layer k=3 : Daily Mean Temperature
    layer k=4 : Total Daily Precipitation
    row i are the observations
    col j are the station listed in STANAME
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
        
    def load_and_format_data(self, fnames):  
        # fname = list of paths of weater data files
    
        nSTA = len(fnames) # Number of weather data file
        
    #------------------------------------------------ INITIALIZED VARIABLES ----
        
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
        
        #---------------------------------------------- WEATHER DATA IMPORT ----
        
            reader = open(fnames[i], 'rb')
            reader = csv.reader(reader, delimiter='\t')
            reader = list(reader)
            
            STADAT = np.array(reader[8:]).astype('float')
            
            self.DATE_START[i, :] = STADAT[0, :3]
            self.DATE_END[i, :] = STADAT[-1, :3]
            
        #-------------------------------------------- TIME CONTINUITY CHECK ----
            
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
            
        #----------------------------------------------- FIRST TIME ROUTINE ----
            
            if i == 0:
                self.VARNAME = reader[7][3:]
                nVAR = len(self.VARNAME) # number of meteorological variable
                self.TIME = np.copy(time_new)
                self.DATA = np.zeros((len(STADAT[:, 0]), nSTA, nVAR)) * np.nan
                self.DATE = STADAT[:, :3]
                self.NUMMISS = np.zeros((nSTA, nVAR)).astype('int')
            else:
                pass
                
        #---------------------------------------- <DATA> & <TIME> RESHAPING ----
            
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
            
    #------------------------------------------ SORT STATION ALPHABETICALLY ----

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
        
    #-------------------------------------------------- GENERATE DATE SERIE ----
    
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

    #===========================================================================
    def generate_summary(self, project_folder):
    # This method will generate a summary of the weather records including all
    # the data files contained in the <Data directory>, including dates when the
    # records begin and end, total number of data, and total number of
    # data missing for each meteorological variable, and more.
    #===========================================================================
    
        nVAR = len(self.VARNAME)
        nSTA = len(self.STANAME)
        
        CONTENT = [['#', 'STATION NAMES', 'DATE START', 'DATE END',
                    'Nbr YEARS' , 'TOTAL DATA', 'MISSING Tmax',
                    'MISSING Tmin', 'MISSING Tmean',
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
            
            CONTENT.append([i+1 , self.STANAME[i], record_date_start,
                            record_date_end, '%0.1f' % (number_data / 365.25),
                            number_data])
                            
            # Missing data information for each meteorological variables   
            for var in range(len(self.VARNAME)):
                txt1 = self.NUMMISS[i, var]
                txt2 = self.NUMMISS[i, var] / number_data * 100
                CONTENT[-1].extend(['%d (%0.1f %%)' % (txt1, txt2)])
            
            # Total missing data information.
            txt1 = np.sum(self.NUMMISS[i, :])
            txt2 = txt1 / (number_data * nVAR) * 100
            CONTENT[-1].extend(['%d (%0.1f %%)' % (txt1, txt2)])
        
        output_path = project_folder + '/STATION_SUMMARY.log'
                
        with open(output_path, 'wb') as f:
            writer = csv.writer(f,delimiter='\t')
            writer.writerows(CONTENT)