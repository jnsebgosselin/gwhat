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
"""

#-- STANDARD LIBRARY IMPORTS --

import csv
from time import strftime, sleep
import os
from copy import copy
from time import clock

#-- THIRD PARTY IMPORTS --

import numpy as np
from numpy.linalg import lstsq as linalg_lstsq
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple
from PySide import QtCore

#-- PERSONAL IMPORTS --

import meteo
import database as db
from hydrograph3 import LatLong2Dist

#==============================================================================
class GapFillWeather(QtCore.QObject):
    """
    This functions is started on the GUI side when the *Fill* or *Fill All*
    button of the Tab named *Fill Data* is clicked on. It is the main routine
    that fill the missing data in the weather record.
    
    Parameters
    ----------
    Nbr_Sta_max : int
    limitDist : float
    limitAlt : float
    regression_mode : int
    add_ETP : bool
    full_error_analysis : bool
    """
#==============================================================================
   
    # Definition of signals that can be used to easily add a Graphical User
    # Interface with Qt on top of this algorithm and to start some of the
    # method from an independent thread.
    
    ProgBarSignal = QtCore.Signal(int)
    ConsoleSignal = QtCore.Signal(str)
    GapFillFinished = QtCore.Signal(bool)
    FillDataSignal = QtCore.Signal(bool)
    
    def __init__(self, parent=None):
        super(GapFillWeather, self).__init__(parent)
        
        #--------------------------------------------------- Required Inputs --
        
        self.time_start = None
        self.time_end = None
        
        self.WEATHER = WeatherData()        
        self.TARGET = TargetStationInfo()

        self.outputDir = None
        self.inputDir = None
        
        self.STOP = False # Flag used to stop the algorithm from a GUI
        self.isParamsValid = False
        
        #----------------------------------------- Define Parameters Default --
        
        # if *regression_mode* = 1: Ordinary Least Square
        # if *regression_mode* = 0: Least Absolute Deviations
        
        # if *add_ETP* is *True*: computes ETP from daily mean temperature              
        # time series with the function *calculate_ETP* from module *meteo*
        # and adds the results to the output datafile.
                      
        # if *full_error_analysis* is *True*: a complete analysis of the
        # estimation errors is conducted with a cross-validation procedure.
                       
        self.Nbr_Sta_max = 4
        self.limitDist = 100
        self.limitAlt = 350        
        self.regression_mode = 1
        self.add_ETP = False
        self.full_error_analysis = False
        
        #------------------------------------------------- Signals and Slots --
        
        # This is only used if managed from a UI.
        
        self.FillDataSignal.connect(self.fill_data)
        
    def load_data(self): #======================================== Load Data ==
        
        if self.inputDir == None:
            print('Please specify a valid input data file directory.')
            return []
            
        if not os.path.exists(self.inputDir):
            print('Data Directory path does not exists.')
            return []
                        
        #-- Generate a list of data file paths --
                        
        Sta_path = []
        for files in os.listdir(self.inputDir):
            if files.endswith(".csv"):
                Sta_path.append(self.inputDir + '/' + files)
                
        if len(Sta_path) == 0:
            print('Data Directory is empty.')
            return []
                
        self.WEATHER.load_and_format_data(Sta_path)        
        self.WEATHER.generate_summary(self.outputDir)
        
        self.TARGET.index = -1
        
        return self.WEATHER.STANAME
        
    def set_target_station(self, index):

        # Update information for the target station.
        self.TARGET.index = index
        self.TARGET.name = self.WEATHER.STANAME[index]
        
        # calculate correlation coefficient between data series of the
        # target station and each neighboring station for every
        # meteorological variable
        self.TARGET.CORCOEF = correlation_worker(self.WEATHER, index)
        
        # Calculate horizontal distance and altitude difference between
        # the target station and each neighboring station.
        self.TARGET.HORDIST, self.TARGET.ALTDIFF = \
                                         alt_and_dist_calc(self.WEATHER, index)
        
    def read_summary(self):
        return self.WEATHER.read_summary(self.outputDir)
        
    def fill_data(self): #====================== Fill Weather Data Algorithm ==

        tstart = clock()
        
        #-------------------------------------------- Assign Local Variables --
        
        #---- Time Related Variables ----
        
        DATE = np.copy(self.WEATHER.DATE)        
        YEAR, MONTH, DAY = DATE[:, 0], DATE[:, 1], DATE[:, 2]
        
        TIME = np.copy(self.WEATHER.TIME)
        index_start = np.where(TIME == self.time_start)[0][0]
        index_end = np.where(TIME == self.time_end)[0][0]
        
        #---- Weather Stations Related Variables ----
        
        DATA = np.copy(self.WEATHER.DATA)       # Daily Weather Data
        VARNAME = np.copy(self.WEATHER.VARNAME) # Name of the weather variables      
        STANAME = np.copy(self.WEATHER.STANAME) # Name of the weather stations
        CORCOEF = np.copy(self.TARGET.CORCOEF)  # Correlation Coefficients
        
        nVAR = len(VARNAME)  # Number of weather variables
        
        #---- Method Parameters ----
        
        limitDist = self.limitDist
        limitAlt = self.limitAlt
        
        #--------------------------------------------- Target Station Header --
        
        tarStaIndx = self.TARGET.index
        target_station_name = self.TARGET.name
        target_station_prov = self.WEATHER.PROVINCE[tarStaIndx]
        target_station_lat = self.WEATHER.LAT[tarStaIndx]
        target_station_lat = round(target_station_lat, 2)
        target_station_lon = self.WEATHER.LON[tarStaIndx]
        target_station_lon = round(target_station_lon, 2)
        target_station_alt = self.WEATHER.ALT[tarStaIndx]
        target_station_alt = round(target_station_alt, 2)
        target_station_clim = self.WEATHER.ClimateID[tarStaIndx]
        
        #----------------------------------------------------------------------
        
        msg = 'Data completion for station %s started' % target_station_name
        print('--------------------------------------------------')
        print(msg)
        print('--------------------------------------------------')
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)
        
        #------------------------------------------- Init Container Matrices --
        
        # Save the weather data series of the target station in a new 
        # 2D matrix named <Y2fill>. The NaN values contained in this matrix
        # will be filled during the data completion process
        
        # When *full_error_analysis* is activated, an additional empty
        # 2D matrix named <YpFULL> is created. This matrix will be completely
        # filled with estimated data during the gap-filling process. The
        # content of this matrix will be used to produce *.err* file.
        
        Y2fill = np.copy(DATA[:, tarStaIndx, :])
        YXmFILL = np.zeros(np.shape(DATA)) * np.nan
        log_RMSE = np.zeros(np.shape(Y2fill))
        
        if self.full_error_analysis == True:
            print('\n!A full error analysis will be performed!\n')
            YpFULL = np.copy(Y2fill) * np.nan
            YXmFULL = np.zeros(np.shape(DATA)) * np.nan
        
        #--------------------------------------------- CHECK CUTOFF CRITERIA --        
        
        # Remove the neighboring stations that do not respect the distance
        # or altitude difference cutoff criteria.
        
        # Note : If cutoff limits are set to a negative number, all stations
        #        are kept regardless of their distance or altitude difference
        #        with the target station.
        
        HORDIST = self.TARGET.HORDIST
        ALTDIFF = np.abs(self.TARGET.ALTDIFF)
        
        if limitDist > 0:
            check_HORDIST = HORDIST < limitDist
        else:
            check_HORDIST = np.zeros(len(HORDIST)) == 0 
            
        if limitAlt > 0:
            check_ALTDIFF = ALTDIFF < limitAlt
        else:
            check_ALTDIFF = np.zeros(len(ALTDIFF)) == 0
           
        check_ALL = check_HORDIST * check_ALTDIFF
        index_ALL = np.where(check_ALL == True)[0]                                  
       
        # Keeps only the stations that respect all the treshold values        
        
        STANAME = STANAME[index_ALL]
        DATA = DATA[:, index_ALL, :]
        CORCOEF = CORCOEF[:, index_ALL]
        
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # WARNING : From here on, STANAME has changed. A new index must
        #           be determined.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        tarStaIndx = np.where(STANAME == self.TARGET.name)[0][0]

        #--------------------------------- Checks Variables With Enough Data --
        
        # NOTE: When a station does not have enough data for a given variable,
        #       its correlation coefficient is set to NaN in CORCOEF. If all
        #       the stations have a value of nan in the correlation table for
        #       a given variable, it means there is not enough data available
        #       overall to estimate and fill missing data for it.
        
        var2fill = np.sum(~np.isnan(CORCOEF[:, :]), axis=1)
        var2fill = np.where(var2fill > 1)[0]
        
        for var in range(nVAR):
            if var not in var2fill:            
                msg = ('!Variable %d/%d won''t be filled because there ' +
                       'is not enough data!') % (var+1, nVAR)
                print(msg)
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
        
        #------------------------------------------------ Init Gap-Fill Loop --

        FLAG_nan = False # If some missing data can't be completed because 
                         # all the neighboring stations are empty, a flag is
                         # raised and a comment is issued at the end of the 
                         # completion process.
        
        nbr_nan_total = np.isnan(Y2fill[index_start:index_end+1, var2fill])
        nbr_nan_total = np.sum(nbr_nan_total)
        
        #---- Variable for the progression of the routine ----
        
        # *progress_total* and *fill_progress* are used to display the
        # progression of the gap-filling procedure on a UI progression bar.
        
        if self.full_error_analysis == True:
            progress_total = np.size(Y2fill[:, var2fill])
        else:
            progress_total = np.copy(nbr_nan_total)
            
        fill_progress = 0
        
        #---- Init. variable for .log file ----
        
        AVG_RMSE = np.zeros(nVAR).astype('float')
        AVG_NSTA = np.zeros(nVAR).astype('float')
        
        #--------------------------------------------------------- FILL LOOP --
        
        # OUTER LOOP: iterates over all the weather variables with enough 
        #             measured data.
        
        for var in var2fill:
                                        
            print('Data completion for variable %d/%d in progress...' %
                  (var+1, nVAR))
            
            #---- Memory Variables ----
            
            colm_memory = np.array([]) # Column sequence memory matrix
            RegCoeff_memory = []       # Regression coefficient memory matrix
            RMSE_memory = []           # RMSE memory matrix
            
            # Sort station in descending correlation coefficient order.
            # The index of the *target station* is pulled at index 0.
            
            # <Sta_index> refers to the indices of the columns of the matrices
            # <DATA>, <STANAME>, and <CORCOEF>.
            
            Sta_index = sort_stations_correlation_order(CORCOEF[var, :],
                                                        tarStaIndx)
            
            # Data for the current weather variable <var> are stored in a 
            # 2D matrix where the rows are the daily weather data and the
            # columns are the weather stations, ordered in descending
            # correlation order. The data series of the *target station* is
            # contained at j = 0.
            
            YX = np.copy(DATA[:, Sta_index, var])              
            
            # Finds rows where data are missing between the date limits
            # at the time indexes <index_start> and <index_end>.
            
            row_nan = np.where(np.isnan(YX[:, 0]))[0]
            row_nan = row_nan[row_nan >= index_start]
            row_nan = row_nan[row_nan <= index_end]
            
            it_avg = 0 # counter used in the calculation of average RMSE
                       # and NSTA values.
            
            if self.full_error_analysis == True :
                # All the data of the time series between the specified 
                # time indexes will be estimated. 
                row2fill = range(index_start, index_end+1)
            else:
                row2fill = row_nan                
           
            # INNER LOOP: iterates over all the days with missing values.
            
            for row in row2fill:
                
                sleep(0.000001) #If no sleep, the UI becomes whacked
                
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!                
                
                # This block of code is used only to stop the gap-filling 
                # routine from a UI by setting the <STOP> flag attributes to
                # *True*.
                
                if self.STOP == True:
                    
                    msg = ('Completion process for station %s stopped.' %
                           target_station_name)
                    print(msg)
                    self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)                    
                    self.STOP = False
                    self.GapFillFinished.emit(False) 
                    
                    return   
                    
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                  
                # Find neighboring stations with valid entries at 
                # row <row> in <YX>. The *Target station* is stored at index 0.
                
                # WARNING: Note that the target station is not considered in
                #          the `np.where` call. It will be added back later
                #          on in the code.
                
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
                else:
                
                    # Determines the number of neighboring station to include 
                    # in the regression model.
                    
                    NSTA = min(len(colm), self.Nbr_Sta_max)
                    
                    # Remove superflux station from <colm>.
                    
                    colm = colm[:NSTA]
                    
                    # Adds back an index 0 at index 0 to include the target
                    # station and add 1 to the indexes of the neighboring
                    # stations
                    
                    colm = colm + 1
                    colm = np.insert(colm, 0, 0)
                    
                    # Stores the values of the independent variables 
                    # (neighboring stations) for this row in a new array.
                    # An intercept term is added if <var> is temperature type
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
                        
                        if self.full_error_analysis == False: 
                            colm_memory = np.append(colm_memory, colm_seq)
                    
                        # Columns of DATA for the variable VAR are sorted
                        # in descending correlation coefficient and the 
                        # information is stored in a 2D matrix (The data for 
                        # the target station are included at index j=0).
                    
                        YXcolm = np.copy(YX)       
                        YXcolm = YXcolm[:, colm]
                        
                        # Force the value of the target station to a NaN value
                        # for this row. This should only have an impact when 
                        # the option "full_error_analysis" is activated. This 
                        # is to actually remove the data being estimated 
                        # from the dataset like it should properly be done 
                        # in a cross-validation procedure.
                        
                        YXcolm[row, 0] = np.nan
                        
                        # All rows containing NaN entries are removed.
                        
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
                            
                        #-------------------------------------- Compute RMSE --
                        
                        # Calculate a RMSE between the estimated and
                        # measured values of the target station.
                        # RMSE with 0 value are not accounted for
                        # in the calcultation.                        
                        
                        Yp = np.dot(A, X.transpose())
                        
                        RMSE = (Y - Yp)**2          # MAE = np.abs(Y - Yp)
                        RMSE = RMSE[RMSE != 0]      # MAE = MAE[MAE!=0]
                        RMSE = np.mean(RMSE)**0.5   # MAE = np.mean(MAE)
                        
                        #------------------------------------- Add to Memory --
                        
                        RegCoeff_memory.append(A)
                        RMSE_memory.append(RMSE)
                    
                    else:                        
                        # Regression coefficients and RSME are recalled
                        # from the memory matrices.

                        A = RegCoeff_memory[index_memory]
                        RMSE = RMSE_memory[index_memory]
                                            
                    #------------------------------ MISSING VALUE ESTIMATION --
                    
                    # Calculate missing value of Y at row <row>.
                    
                    Y_row = np.dot(A, X_row)
                    
                    # Limit precipitation based variable to positive values.
                    # This may happens when there is one or more negative 
                    # regression coefficients in A

                    if var in (3, 4, 5):
                        Y_row = max(Y_row, 0)
                    
                    #----------------------------------------- STORE RESULTS --
                  
                    if self.full_error_analysis == True:
                        YpFULL[row, var] = Y_row
                        
                        # Gets the indexes of the stations that were used for
                        # estimating the data at <row>. <Sta_index_row> relates
                        # to the colums of <DATA>, <STANAME>, and <CORCOEF>.
                        # Note also that the first index corresponds to the
                        # target station, in other words:
                        #                        
                        #     tarStaIndx == Sta_index_row[0]
                        
                        Sta_index_row = Sta_index[colm]
                        
                        # Gets the measured value for the target station for
                        # <var> at <row>.
                        
                        ym_row  = DATA[row, Sta_index_row[0], var] 
                        
                        # There is a need to take into account that a intercept
                        # term has been added for temperature-like variables.
                        
                        if var in (0, 1, 2):
                            YXmFULL[row, Sta_index_row[0], var] = ym_row                                               
                            YXmFULL[row, Sta_index_row[1:], var] = X_row[1:]
                        else:
                            YXmFULL[row, Sta_index_row[0], var] = ym_row
                            YXmFULL[row, Sta_index_row[1:], var] = X_row
                                              
                    if row in row_nan:
                        Y2fill[row, var] = Y_row                        
                        log_RMSE[row, var] = RMSE
                        
                        AVG_RMSE[var] += RMSE
                        AVG_NSTA[var] += NSTA
                        it_avg += 1
                        
                        Sta_index_row = Sta_index[colm]
                        if var in (0, 1, 2):                            
                            YXmFILL[row, Sta_index_row[0], var] = Y_row                                               
                            YXmFILL[row, Sta_index_row[1:], var] = X_row[1:]
                        else:
                            YXmFILL[row, Sta_index_row[0], var] = Y_row
                            YXmFILL[row, Sta_index_row[1:], var] = X_row
                    
                fill_progress += 1.
                self.ProgBarSignal.emit(fill_progress/progress_total * 100)
                
            #------------------ Calculate Estimation Error for this variable --
            
            if it_avg > 0:
                AVG_RMSE[var] /= it_avg
                AVG_NSTA[var] /= it_avg
            else:
                AVG_RMSE[var] = np.nan
                AVG_NSTA[var] = np.nan

            print('Data completion for variable %d/%d completed.' %
                  (var+1, nVAR))
            
        #---------------------------------------------------- End of Routine --
            
        msg = ('Data completion for station %s completed successfully ' +
               'in %0.2f sec.') % (target_station_name, (clock() - tstart))
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)
        print('\n' + msg)
        print('Saving data to files...')
        print('--------------------------------------------------')
        
        if FLAG_nan == True:
            self.ConsoleSignal.emit(
                '<font color=red>WARNING: Some missing data were not ' +
                'completed because all neighboring station were empty ' +
                'for that period</font>')
        
        #================================================ WRITE DATA TO FILE ==
        
        #------------------------------------------------------------ Header --
              
        HEADER = [['Station Name', target_station_name],
                  ['Province', target_station_prov],
                  ['Latitude', target_station_lat],
                  ['Longitude', target_station_lon],
                  ['Elevation', target_station_alt],
                  ['Climate Identifier', target_station_clim],
                  [],
                  ['Created by', db.software_version],
                  ['Created on', strftime("%d/%m/%Y")],
                  []]
        
        #--------------------------------------------------------- .log file --
    
        #---- Info Data Post-Processing ----
        
        XYinfo = self.postprocess_fillinfo(STANAME, YXmFILL, tarStaIndx)
        Yname, Yp = XYinfo[0], XYinfo[1]
        Xnames, Xm = XYinfo[2], XYinfo[3]
        Xcount_var, Xcount_tot = XYinfo[4], XYinfo[5]

        #---- Gap-Fill Info Summary ----   
        
        record_date_start = '%04d/%02d/%02d' % (YEAR[index_start],
                                                MONTH[index_start],
                                                DAY[index_start]) 
                                            
        record_date_end = '%04d/%02d/%02d' % (YEAR[index_end],
                                              MONTH[index_end],
                                              DAY[index_end])
        
        fcontent = copy(HEADER)        
        fcontent.extend([['*** FILL PROCEDURE INFO ***'],[]])
        if self.regression_mode == True:
            fcontent.append(['MLR model', 'Ordinary Least Square'])
        elif self.regression_mode == False:
            fcontent.append(['MLR model', 'Least Absolute Deviations'])
        fcontent.extend([['Precip correction', 'Not Available'],
                         ['Wet days correction', 'Not Available'],
                         ['Max number of stations', str(self.Nbr_Sta_max)],
                         ['Cutoff distance (km)', str(limitDist)],
                         ['Cutoff altitude difference (m)', str(limitAlt)],
                         ['Date Start', record_date_start],
                         ['Date End', record_date_end],
                         [], [],
                         ['*** SUMMARY TABLE ***'],
                         [],
                         ['CLIMATE VARIABLE', 'TOTAL MISSING',
                          'TOTAL FILLED', '', 'AVG. NBR STA.', 'AVG. RMSE',
                          '']])      
        fcontent[-1].extend(Xnames)
        
        #---- Missing Data Summary ----   
        
        total_nbr_data = index_end - index_start + 1
        nbr_fill_total = 0
        nbr_nan_total = 0
        for var in range(nVAR):
            
            nbr_nan = np.isnan(DATA[index_start:index_end+1, tarStaIndx, var])
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
       
            fcontent.append([VARNAME[var], nbr_nan, nbr_fill_txt, '',
                             '%0.1f' % AVG_NSTA[var],
                             '%0.2f' % AVG_RMSE[var], ''])
            
            for i in range(len(Xnames)):                
                if nbr_fill == 0:
                    pc = 0
                else:
                    pc = Xcount_var[i, var] / float(nbr_fill) * 100                
                fcontent[-1].append('%d (%0.1f %% of filled)' % 
                                    (Xcount_var[i, var], pc))

        #---- Total Missing ----
        
        pc = nbr_nan_total / (total_nbr_data * nVAR) * 100        
        nbr_nan_total = '%d (%0.1f %% of total)' % (nbr_nan_total, pc)
        
        #---- Total Filled ----
        
        try:
            pc = nbr_fill_total / nbr_nan_total * 100
        except:
            pc = 0            
        nbr_fill_total_txt = '%d (%0.1f %% of missing)' % (nbr_fill_total, pc)
        
        fcontent.extend([[],
                         ['TOTAL', nbr_nan_total, nbr_fill_total_txt, 
                          '', '---', '---', '']])
        
        for i in range(len(Xnames)):
            pc = Xcount_tot[i] / nbr_fill_total * 100
            text2add = '%d (%0.1f %% of filled)' % (Xcount_tot[i], pc)
            fcontent[-1].append(text2add)
                    
        #---- Info Detailed ----
        
        fcontent.extend([[],[],
                         ['*** DETAILED REPORT ***'],
                         [],
                         ['VARIABLE', 'YEAR', 'MONTH', 'DAY', 'NBR STA.',
                          'RMSE', Yname]])        
        fcontent[-1].extend(Xnames)        
                        
        for var in var2fill:
            for row in range(index_start, index_end+1):
                
                yp = Yp[row, var]
                ym = DATA[row, tarStaIndx, var]                                  
                xm = ['' if np.isnan(i) else '%0.1f' % i for i in 
                      Xm[row, :, var]]                
                nsta = len(np.where(~np.isnan(Xm[row, :, var]))[0])
                
                # Write the info only if there is a missing value in
                # the data series of the target station.
                
                if np.isnan(ym):
                    fcontent.append([VARNAME[var],
                                     '%d' % YEAR[row],
                                     '%d' % MONTH[row],
                                     '%d' % DAY[row],
                                     '%d' % nsta,
                                     '%0.2f' % log_RMSE[row, var],
                                     '%0.1f' % yp])
                    fcontent[-1].extend(xm)
        
        #---- Save File ----
                                  
        YearStart = str(int(YEAR[index_start])) 
        YearEnd = str(int(YEAR[index_end]))

        # Check if the characters "/" or "\" are present in the station 
        # name and replace these characters by "-" if applicable.
        
        target_station_name = target_station_name.replace('\\', '_')
        target_station_name = target_station_name.replace('/', '_')

        output_path = '%s/%s (%s)_%s-%s.log' % (self.outputDir, 
                                                target_station_name,
                                                target_station_clim,
                                                YearStart,
                                                YearEnd)

        self.save_content_to_file(output_path, fcontent)
        
        self.ConsoleSignal.emit(
               '<font color=black>Info file saved in %s.</font>' % output_path)
            
        #--------------------------------------------------------- .out file --
        
        #---- Prepare Header ----
        
        fcontent = copy(HEADER)
        fcontent.append(['Year', 'Month', 'Day'])
        fcontent[-1].extend(VARNAME)
        
        #---- Add Data ----
            
        for row in range(index_start, index_end+1):            
            fcontent.append(['%d' % YEAR[row],
                             '%d' % MONTH[row],
                             '%d' % DAY[row]])
                             
            y = ['%0.1f' % i for i in Y2fill[row, :]]
            fcontent[-1].extend(y)
            
        #---- Save Data ----
        
        output_path = '%s/%s (%s)_%s-%s.out' % (self.outputDir, 
                                                target_station_name,
                                                target_station_clim,
                                                YearStart,
                                                YearEnd)
        
        self.save_content_to_file(output_path, fcontent)
            
        msg = 'Meteo data saved in %s.' % output_path
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)
        
        #---- Add ETP to File ----
        
        if self.add_ETP:
            meteo.add_ETP_to_weather_data_file(output_path)            
        
        #--------------------------------------------------------- .err file --
        
        if self.full_error_analysis == True:
            
            #---- Info Data Post-Processing ----
                
            XYinfo = self.postprocess_fillinfo(STANAME, YXmFULL, tarStaIndx)
            Yname, Ym = XYinfo[0], XYinfo[1]
            Xnames, Xm = XYinfo[2], XYinfo[3]
            
            #---- Prepare Header ----
            
            fcontent = copy(HEADER)
            fcontent.append(['', '', '', '', 'Est. Err.', Yname, Yname])
            fcontent[-1].extend(Xnames)
            fcontent.append(['VARIABLE', 'YEAR', 'MONTH', 'DAY', 'Ypre-Ymes',
                             'Ypre', 'Ymes'])
            for i in range(len(Xnames)):
                fcontent[-1].append('X%d' % i)
            
            #---- Add Data to fcontent ----
                
            for var in range(nVAR):
                for row in range(index_start, index_end+1):
                    
                    yp = YpFULL[row, var]  
                    ym = Ym[row, var]                                      
                    xm = ['' if np.isnan(i) else '%0.1f' % i for i in 
                          Xm[row, :, var]]
                    
                    # Write the info only if there is a measured value in
                    # the data series of the target station.
                    
                    if not np.isnan(ym):
                        fcontent.append([VARNAME[var],
                                        '%d' % YEAR[row],
                                        '%d' % MONTH[row],
                                        '%d' % DAY[row],                                        
                                        '%0.1f' % (yp - ym),
                                        '%0.1f' % yp,
                                        '%0.1f' % ym])
                        fcontent[-1].extend(xm)
            
            #---- Save File ----
            
            output_path = '%s/%s (%s)_%s-%s.err' % (self.outputDir, 
                                                    target_station_name,
                                                    target_station_clim,
                                                    YearStart,
                                                    YearEnd)                                               
            
            self.save_content_to_file(output_path, fcontent)
        
            #---- SOME CALCULATIONS ----
            
            RMSE = np.zeros(nVAR)
            ERRMAX  = np.zeros(nVAR)
            ERRSUM = np.zeros(nVAR)
            for i in range(nVAR):
                
                errors = YpFULL[:, i] - Y2fill[:, i]
                errors = errors[~np.isnan(errors)]
                
                rmse = errors**2 
                rmse = rmse[rmse != 0]                  
                rmse = np.mean(rmse)**0.5
                
                errmax = np.abs(errors)
                errmax = np.max(errmax)
                
                errsum = np.sum(errors)
                                
                RMSE[i] = rmse
                ERRMAX[i] = errmax
                ERRSUM[i] = errsum
            
            print('RMSE :')
            print(np.round(RMSE, 2))
            print('Maximum Error :')
            print(ERRMAX)
            print('Cumulative Error :')
            print(ERRSUM)

        #------------------------------------------------------- End Routine --            
        
        self.STOP = False # Just in case. This is a precaution override.          
        self.GapFillFinished.emit(True)        
        
        return
    
    @staticmethod                                           
    def postprocess_fillinfo(staName, YXmFULL, tarStaIndx): #==================
                
        # Extracts info related to the target station from the
        # <YXmFull> matrix.
        Yname = staName[tarStaIndx]
        Xnames = np.delete(staName, tarStaIndx)
      
        Ym = YXmFULL[:, tarStaIndx, :]
        Xm = np.delete(YXmFULL, tarStaIndx, axis=1)
        
        # Counts how many times each neigboring station was used for
        # estimating the data of the target stations.
        
        Xcount_var = np.sum(~np.isnan(Xm), axis=0)
        Xcount_tot = np.sum(Xcount_var, axis=1)
        
        # Removes the neighboring stations that were not used
        
        indx = np.where(Xcount_tot > 0)[0]
        Xnames = Xnames[indx]
        Xm = Xm[:, indx]
        
        Xcount_var = Xcount_var[indx, :]
        Xcount_tot = Xcount_tot[indx]
                
        # Sort the neighboring stations by importance :

        indx = np.argsort(Xcount_tot * -1)

        Xnames = Xnames[indx]
        Xm = Xm[:, indx]

        return Yname, Ym, Xnames, Xm, Xcount_var, Xcount_tot
    
    @staticmethod
    def save_content_to_file(fname, fcontent): #======= Save Content to File ==
        
        with open(fname, 'w') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(fcontent)
       
       
#==============================================================================
def correlation_worker(WEATHER, tarStaIndx):
    """
    This function computes the correlation coefficients between the target
    station and the neighboring stations for each meteorological variable.
 
    Results are stored in the 2D matrix *CORCOEF*, where:
        rows :    meteorological variables
        columns : weather stations
    """
#==============================================================================

    DATA = WEATHER.DATA
    
    nVAR = len(DATA[0, 0, :])  # number of meteorological variables
    nSTA = len(DATA[0, :, 0])  # number of stations including target
   
    print('\ncorrelation coefficients computation in progress')
    
    CORCOEF = np.zeros((nVAR, nSTA)) * np.nan
    
    Ndata_limit = int(365 / 2.) # Minimum number of pair of data necessary
                                # between the target and a neighboring station
                                # to compute a correlation coefficient.

    for i in range(nVAR): 
        for j in range(nSTA):
                        
            # Rows with nan entries are removed from the data matrix.
            DATA_nonan = np.copy(DATA[:, (tarStaIndx, j), i])
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
        
    print('correlation coefficients computation completed\n')

    return CORCOEF
     
     
#==============================================================================
class TargetStationInfo():
    """
    Class that contains all the information relative the target station, 
    including correlation coefficient 2d matrix, altitude difference and 
    horizontal distances arrays.
    """
#==============================================================================

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

#==============================================================================
def alt_and_dist_calc(WEATHER, index):
    """
    Computes the horizontal distance in km and the altitude difference
    in m between the target station and each neighboring stations
    
    index: Target Station Index
    """
#==============================================================================
   
    ALT = WEATHER.ALT
    LAT = WEATHER.LAT
    LON = WEATHER.LON

    nSTA = len(ALT) # number of stations including target
    
    HORDIST = np.zeros(nSTA) # distances of neighboring station from target
    ALTDIFF = np.zeros(nSTA) # altitude differences
    
    for i in range(nSTA): 
        HORDIST[i]  = LatLong2Dist(LAT[index], 
                                   LON[index],
                                   LAT[i], LON[i])
                                           
        ALTDIFF[i] = ALT[i] - ALT[index]
    
    HORDIST = np.round(HORDIST, 1)
    ALTDIFF = np.round(ALTDIFF, 1)
    
    return HORDIST, ALTDIFF        

        
#==============================================================================
class WeatherData():
    """
    This class contains all the weather data and weather station info
    that are needed for the gapfilling algorithm that is defined in the
    *GapFillWeather* class.
    
    Class Attributes
    ----------------    
    DATA: Numpy matrix [i, j, k] contraining the weather data where:
        - layer k=0 is Maximum Daily Temperature
        - layer k=1 is Minimum Daily Temperature
        - layer k=2 is Daily Mean Temperature
        - layer k=3 is Total Daily Precipitation
        - rows i are the time
        - columns j are the stations listed in STANAME
    STANAME: Numpy Array
        Contains the name of the weather stations. If a station name already
        exists in the list when adding a new station, a number is added at
        the end of the new name.
    """
#============================================================================== 
        
    def __init__(self):
        
        self.DATA = []       # Weather data
        self.DATE = []       # Date in tuple format [YEAR, MONTH, DAY]
        self.TIME = []       # Date in numeric format
        
        self.DATE_START = [] # Date on which the data record begins
        self.DATE_END = []   # Date on which data record ends
        
        self.STANAME = []    # Station names
        self.ALT = []        # Station elevation in m
        self.LAT = []        # Station latitude in decimal degree
        self.LON = []        # Station longitude in decimal degree
        self.VARNAME = []    # Names of the meteorological variables
        self.ClimateID = []  # Climate Identifiers of weather station
        self.PROVINCE = []   # Provinces where weater station are located 

        self.NUMMISS = []    # Number of missing data
        
    def load_and_format_data(self, fnames):  #=================================
        
        # fnames = list of paths of weater data files
    
        nSTA = len(fnames) # Number of weather data file
        
        #---------------------------------------------------- VARIABLES INIT --
        
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
        
            #------------------------------------------- WEATHER DATA IMPORT --
        
            with open(fnames[i], 'r') as f:
                reader = list(csv.reader(f, delimiter='\t'))
            
            STADAT = np.array(reader[8:]).astype('float')
            
            self.DATE_START[i, :] = STADAT[0, :3]
            self.DATE_END[i, :] = STADAT[-1, :3]
            
            #----------------------------------------- TIME CONTINUITY CHECK --
            
            # Check if data are continuous over time. If not, the serie will be
            # made continuous and the gaps will be filled with nan values.
            
            time_start = xldate_from_date_tuple((STADAT[0, 0].astype('int'),
                                                 STADAT[0, 1].astype('int'),
                                                 STADAT[0, 2].astype('int')),
                                                0)

            time_end = xldate_from_date_tuple((STADAT[-1, 0].astype('int'),
                                               STADAT[-1, 1].astype('int'),
                                               STADAT[-1, 2].astype('int')), 0)
            
            if (time_end - time_start + 1) != len(STADAT[:,0]):
                print
                print('%s is not continuous, correcting...' % reader[0][1])            
                STADAT = meteo.make_timeserie_continuous(STADAT)            
                print ('%s is now continuous.' % reader[0][1])
            
            time_new = np.arange(time_start, time_end + 1)
            
            #-------------------------------------------- FIRST TIME ROUTINE --
            
            if i == 0:
                self.VARNAME = reader[7][3:]
                nVAR = len(self.VARNAME) # number of meteorological variable
                self.TIME = np.copy(time_new)
                self.DATA = np.zeros((len(STADAT[:, 0]), nSTA, nVAR)) * np.nan
                self.DATE = STADAT[:, :3]
                self.NUMMISS = np.zeros((nSTA, nVAR)).astype('int')
                
            #------------------------------------- <DATA> & <TIME> RESHAPING --
            
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
                  
            ifirst = np.where(self.TIME == time_new[0])[0][0]
            ilast = np.where(self.TIME == time_new[-1])[0][0]            
            self.DATA[ifirst:ilast+1, i, :] = STADAT[:, 3:]
            
            #---------------------------------------------------- Other Info --
            
            #-- Nbr. of Missing Data --
            
            isnan = np.isnan(STADAT[:, 3:])
            self.NUMMISS[i, :] = np.sum(isnan, axis=0)
            
            #-- station name --
            
            # Check if a station with this name already exist in the list. 
            # If so, a number at the end of the name is added so it is 
            # possible to differentiate them in the list.
            
            isNameExist = np.where(reader[0][1] == self.STANAME)[0]
            if len(isNameExist) > 0:
                
                print('Station name %s already exists. ' +
                      'Added a number at the end.') % reader[0][1]
                
                count = 1
                while len(isNameExist) > 0:
                    newname = '%s (%d)' % (reader[0][1], count)
                    isNameExist = np.where(newname == self.STANAME)[0]
                    count += 1
                
                self.STANAME[i] = newname
                
            else:
                self.STANAME[i] = reader[0][1]
            
            #-- other station info --
            
            self.PROVINCE[i] = str(reader[1][1])
            self.LAT[i] = float(reader[2][1])
            self.LON[i] = float(reader[3][1])
            self.ALT[i] = float(reader[4][1])
            self.ClimateID[i] = str(reader[5][1])
            
        #--------------------------------------- SORT STATION ALPHABETICALLY --

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
        
        #----------------------------------------------- GENERATE DATE SERIE --
    
        # Rebuild a date matrix if <DATA> size changed. Otherwise, do nothing
        # and keep *Date* as is.
    
        if FLAG_date == True:
            self.DATE = np.zeros((len(self.TIME), 3))
            for i in range(len(self.TIME)):
                date_tuple = xldate_as_tuple(self.TIME[i], 0)
                self.DATE[i, 0] = date_tuple[0]
                self.DATE[i, 1] = date_tuple[1]
                self.DATE[i, 2] = date_tuple[2]
    
    def generate_summary(self, project_folder): #==============================

        """
        This method generates a summary of the weather records including
        all the data files contained in */<project_folder>/Meteo/Input*,
        including dates when the records begin and end, total number of data,
        and total number of data missing for each meteorological variable, and
        more.
        """
        
        CONTENT = [['#', 'STATION NAMES', 'ClimateID',
                    'Lat. (dd)', 'Lon. (dd)', 'Alt. (m)',
                    'DATE START', 'DATE END', 'Nbr YEARS' , 'TOTAL DATA',
                    'MISSING Tmax', 'MISSING Tmin', 'MISSING Tmean',
                    'Missing Precip']]
                                
        for i in range(len(self.STANAME)):
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
            
            CONTENT.append([i+1 , self.STANAME[i],
                            self.ClimateID[i],
                            '%0.2f' % self.LAT[i],
                            '%0.2f' % self.LON[i],
                            '%0.2f' % self.ALT[i],
                            record_date_start,
                            record_date_end,
                            '%0.1f' % (number_data / 365.25),
                            number_data])
                            
            # Missing data information for each meteorological variables   
            for var in range(len(self.VARNAME)):
                CONTENT[-1].extend(['%d' % (self.NUMMISS[i, var])])
                
#                txt1 = self.NUMMISS[i, var]
#                txt2 = self.NUMMISS[i, var] / number_data * 100
#                CONTENT[-1].extend(['%d (%0.1f %%)' % (txt1, txt2)])
            
#            # Total missing data information.
#            txt1 = np.sum(self.NUMMISS[i, :])
#            txt2 = txt1 / (number_data * nVAR) * 100
#            CONTENT[-1].extend(['%d (%0.1f %%)' % (txt1, txt2)])
        
        output_path = project_folder + '/weather_datasets_summary.log'
                
        with open(output_path, 'w') as f:
            writer = csv.writer(f,delimiter='\t')
            writer.writerows(CONTENT)
            
    def read_summary(self, project_folder): #==================================

        """
        This method read the content of the file generated by the method
        <generate_summary> and will return the content of the file in a HTML
        formatted table
        """
                
        #--------------------------------------------------------- read data --
        
        filename = project_folder + '/weather_datasets_summary.log'
        with open(filename, 'r') as f:
            reader = list(csv.reader(f, delimiter='\t'))
            reader = reader[1:]
        
#        FIELDS = ['&#916;Alt.<br>(m)', 'Dist.<br>(km)', 'Tmax', 
#                  'Tmin', 'Tmean', 'Ptot']
        
        #-------------------------------------------- generate table summary --
        
        table = '''
                <table border="0" cellpadding="3" cellspacing="0" 
                 align="center">  
                  <tr>
                    <td colspan="10"><hr></td>
                  </tr>                             
                  <tr> 
                    <td align="center" valign="bottom"  width=30 rowspan="3">
                      #
                    </td>
                    <td align="left" valign="bottom" rowspan="3">
                      Station
                    </td>
                    <td align="center" valign="bottom" rowspan="3">
                      Climate<br>ID
                    </td>
                    <td align="center" valign="bottom" rowspan="3">
                      From<br>year
                    </td>
                    <td align="center" valign="bottom" rowspan="3">
                      To<br>year
                    </td>
                    <td align="center" valign="bottom" rowspan="3">
                      Nbr.<br>of<br>years
                    <td align="center" valign="middle" colspan="4">
                      % of missing data for
                    </td>
                  </tr>
                  <tr>
                    <td colspan="4"><hr></td>
                  </tr>
                  <tr>                    
                    <td align="center" valign="middle">
                      T<sub>max</sub>
                    </td>
                    <td align="center" valign="middle">
                      T<sub>min</sub>
                    </td>
                    <td align="center" valign="middle">
                      T<sub>mean</sub>
                    </td>
                    <td align="center" valign="middle">
                      P<sub>tot</sub>
                    </td>
                  </tr>
                  <tr>
                    <td colspan="10"><hr></td>
                  </tr> 
                '''
        for i in range(len(reader)):
            
            color = ['transparent', '#E6E6E6']
            
            Ntotal = float(reader[i][9])
            TMAX = float(reader[i][10]) / Ntotal * 100
            TMIN = float(reader[i][11]) / Ntotal * 100
            TMEAN = float(reader[i][12]) / Ntotal * 100
            PTOT = float(reader[i][13]) / Ntotal * 100
            firstyear = reader[i][6][:4]
            lastyear = reader[i][7][:4]
            nyears = float(lastyear) - float(firstyear)
            
            table += '''
                     <tr bgcolor="%s">
                       <td align="center" valign="middle">
                         %02d
                       </td>
                       <td align="left" valign="middle">
                         <font size="3">%s</font>
                       </td>
                       <td align="center" valign="middle">
                         <font size="3">%s</font>
                       </td>
                       <td align="center" valign="middle">
                         <font size="3">%s</font>
                       </td>
                       <td align="center" valign="middle">
                         <font size="3">%s</font>
                       </td>
                       <td align="center" valign="middle">
                         <font size="3">%0.0f</font>
                       </td>
                       <td align="center" valign="middle">%0.0f</td>
                       <td align="center" valign="middle">%0.0f</td>
                       <td align="center" valign="middle">%0.0f</td>
                       <td align="center" valign="middle">%0.0f</td>
                     </tr>
                     ''' % (color[i%2], i+1, reader[i][1], reader[i][2],
                            firstyear, lastyear, nyears, 
                            TMAX, TMIN, TMEAN, PTOT)
        
        table += """
                   <tr>
                     <td colspan="10"><hr></td>
                   </tr>
                 </table>
                 """
        
        return table
        
#==============================================================================
def sort_stations_correlation_order(CORCOEF, tarStaIndx): 
#==============================================================================
        
    # An index is associated with each value of the CORCOEF array.
        
    CORCOEF = np.vstack((range(len(CORCOEF)), CORCOEF)).transpose()
    
    # Remove target station from the stack. This is necessary in case there is
    # some data that belong to the same station, but without the same length.
    
    CORCOEF = np.delete(CORCOEF, tarStaIndx, axis=0)
    
    # Stations for which the correlation coefficient is nan are removed.
    
    CORCOEF = CORCOEF[~np.isnan(CORCOEF).any(axis=1)] 
               
    # The station indexes are sorted in descending order of their
    # correlation coefficient.
               
    CORCOEF = CORCOEF[np.flipud(np.argsort(CORCOEF[:, 1])), :]
    
    # The sorted station indexes are extracted from the *CORCOEF* matrix and
    # the target station index is added back at the beginning of the
    # *Sta_index* array. 
    
    Sta_index = np.copy(CORCOEF[:, 0].astype('int'))
    Sta_index = np.insert(Sta_index, 0, tarStaIndx)
    
    return Sta_index
        
#==============================================================================   
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
#==============================================================================
 
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
    
    #---- create an instance of the class *GapFillWeather* ----
    
    gapfill_weather = GapFillWeather()
    
    #---- setup input and output directory ----
    
    workdir = "../Projects/Project4Testing"    
    gapfill_weather.outputDir = workdir + '/Meteo/Output'
    gapfill_weather.inputDir = workdir + '/Meteo/Input'
    
    #---- load weather data files ----
    
    stanames = gapfill_weather.load_data()
    print(stanames) 
    
    #---- setup target station and do some calculation ----
    
    gapfill_weather.set_target_station(0)    
          
    #---- define the time plage over which data will be gap-filled ----
    
    gapfill_weather.time_start = gapfill_weather.WEATHER.TIME[0]
    gapfill_weather.time_end = gapfill_weather.WEATHER.TIME[-1] 
      
    #---- setup method parameters ----
        
    gapfill_weather.Nbr_Sta_max = 4
    gapfill_weather.limitDist = 100
    gapfill_weather.limitAlt = 350                                  
    gapfill_weather.regression_mode = 0
    
    #---- define additional options ----
    
    gapfill_weather.full_error_analysis = False
    gapfill_weather.add_ETP = False
    
    #---- fill data ----
      
    gapfill_weather.fill_data()