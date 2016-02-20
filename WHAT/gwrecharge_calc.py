# -*- coding: utf-8 -*-
"""
Copyright 2014-2016 Jean-Sebastien Gosselin
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

#----- STANDARD LIBRARY IMPORTS -----
      
#from datetime import date
import csv
import datetime

#----- THIRD PARTY IMPORTS -----

import numpy as np
#from xlrd import xldate_as_tuple
#from xlrd.xldate import xldate_from_date_tuple
import matplotlib.pyplot as plt

#----- PERSONAL LIBRARY IMPORTS -----

from meteo import MeteoObj
from waterlvldata import WaterlvlData
from gwrecharge_post import plot_water_budget_yearly

#==============================================================================

class SynthHydrograph(object):                              # SynthHydrograph #
    
#==============================================================================
    
    def __init__(self, fmeteo, fwaterlvl):
    
        #---- Load Data ----
    
        print('--------')
        self.meteoObj = MeteoObj()
        self.meteoObj.load_and_format(fmeteo) # Includes the estimation of ETP
                                              # if not already present in file.
        print('--------')
        self.waterlvlObj = WaterlvlData()
        self.waterlvlObj.load(fwaterlvl)
        print('--------')
        
        self.twlvl = self.waterlvlObj.time
        self.WLVLobs = self.waterlvlObj.lvl
        self.NaNindx = np.where(~np.isnan(self.WLVLobs))
        
        #---- Make the water level time series continuous ----
        
        # Not needed anymore since this is done within the *load* method of
        # the *WaterlvlData* class.
        
        # ts, te = self.waterlvlObj.time[0], self.waterlvlObj.time[-1]
        # self.twlvl = np.arange(ts, te+1)
        # self.WLVLobs = np.interp(self.twlvl, self.waterlvlObj.time,
        #                          self.waterlvlObj.lvl)
        
        #---- Prepare DATE time series ----
        
        # Converting time in a date format readable by matplotlib and also make
        # the weather and water level time series synchroneous.
               
        tweatr = self.meteoObj.TIME
        
        ts = self.ts = np.where(self.twlvl[0] == tweatr)[0][0]
        te = self.te = np.where(self.twlvl[-1] == tweatr)[0][0] 
        
        self.YEAR = self.meteoObj.DATA[ts:te+1,0]
        self.MONTH = self.meteoObj.DATA[ts:te+1,1]
        DAY = self.meteoObj.DATA[ts:te+1,2]        
        self.TIME = self.meteoObj.TIME[ts:te+1]
        self.PRECIP = self.meteoObj.DATA[:, 6][ts:te+1]
        
        self.DATE = self.convert_time_to_date(self.YEAR, self.MONTH, DAY)
        
        #---- Multiple Fit ----
        
#        ax.set_ylabel('Water Level (mbgs)', fontsize=16) 
#        ax.grid(axis='x', color=[0.65, 0.65, 0.65], ls=':', lw=1)
#        ax.set_axisbelow(True)
#        
#        ax.legend(loc=[1.01, 0], ncol=1, fontsize=8)
#        ax.invert_yaxis()
        
#        fname = '%0.2f.pdf' % Sy
#        fig.savefig(fname)
        
    @staticmethod
    def convert_time_to_date(YEAR, MONTH, DAY): #============== Convert Date ==
                
        DATE = [0] * len(YEAR)
        for t in range(len(YEAR)):
            DATE[t] = datetime.datetime(int(YEAR[t]), int(MONTH[t]),
                                        int(DAY[t]), 0)
                                        
        return DATE
        
    def plot_best_fit(self, Sy): #============================ Plot Best Fit ==
        
        #---- Prepare Figure and Plot Obs. ----
        
        fwidth, fheight = 18, 6
        fig = plt.figure(figsize=(fwidth, fheight))        
        fig.suptitle('Synthetic hydrographs with Sy = %0.2f' % Sy, fontsize=20)
       
        lmarg  = 0.85 / fwidth
        rmarg = 1.75 / fwidth
        tmarg = 0.5 / fheight
        bmarg = 0.65 / fheight
        
        axwidth = 1 - (lmarg + rmarg)
        axheight = 1 - (bmarg + tmarg)
        
        ax = fig.add_axes([lmarg, bmarg, axwidth, axheight])
        
        #---- Produces Results (Optimization) ----
        
        Cru, RASmax, WLVLPRE, RECHG = self.opt_Cru(Sy)
        
        RMSE = self.calc_RMSE(self.WLVLobs[self.NaNindx]*1000,
                              WLVLPRE[self.NaNindx])                                 
        NSE = self.nash_sutcliffe(self.WLVLobs[self.NaNindx]*1000,
                                  WLVLPRE[self.NaNindx])
        rechg = np.mean(RECHG) * 365
        
        #---- plot results ----
        
        ax.plot(self.DATE, self.WLVLobs, '0.65', lw=1.5,
                label='Observed\nWater Levels')
        
        label = ('Cru = %0.2f\n' +
                 'RASmax = %0.0f mm\n' + 
                 'RMSE = %0.0f mm\n' +
                 'NSE = %0.2f\n' +
                 'Rechg = %0.0f mm/y'
                 ) % (Cru, RASmax, RMSE, NSE, rechg)
                 
        ax.plot(self.DATE, WLVLPRE/1000., alpha=0.65, lw=1.5, label=label)
        
        #---- Figure setup ----
        
        ax.set_ylabel('Water Level (mbgs)', fontsize=16) 
        ax.grid(axis='x', color=[0.65, 0.65, 0.65], ls=':', lw=1)
        ax.set_axisbelow(True)
        
        ax.legend(loc=[1.01, 0], ncol=1, fontsize=8)
        ax.invert_yaxis()
        
        fname = 'Bestfit_Sy=%0.2f.pdf' % Sy
        fig.savefig(fname)
        
        #---- Saving Data to File ----

        filename = 'Sy=%0.2f_data.csv' % Sy
        filecontent = [['*** Model Parameters ***'],
                       [],
                       ['Sy :', '%0.2f' % Sy],
                       ['RASmax (mm) :', '%0.0f' % RASmax],
                       ['Cru :', '%0.2f' % Cru],
                       [],
                       ['*** Model Results ***'],
                       [],
                       ['RMSE (mm) :', '%0.0f' % RMSE],
                       ['NSE :', '%0.2f' % NSE],
                       ['Rechg (mm/y) :', '%0.0f' % rechg],
                       [],
                       ['*** Observed and Predicted Water Level ***'],
                       [],
                       ['Time (d)', 'hobs(mbgs)', 'hpre(mbgs)', 'Rechg (mm/d)']]
        for i in range(len(self.twlvl)-1):
            filecontent.append([self.twlvl[i],
                                '%0.2f' % (WLVLPRE[i]/1000.),
                                '%0.2f' % self.WLVLobs[i],
                                '%0.0f' % RECHG[i]]) 

        filecontent.append([self.twlvl[-1],
                            '%0.2f' % (WLVLPRE[-1]/1000.),
                            '%0.2f' % self.WLVLobs[-1]])

        with open(filename, 'w') as f:
            writer = csv.writer(f,delimiter='\t')
            writer.writerows(filecontent)
        
        
    def plot_multiple_fit(self, Sy, CRU): #=================== Plot Multiple ==

        #---- Prepare Figure and Plot Obs. ----
        
        fwidth, fheight = 18, 6
        fig = plt.figure(figsize=(fwidth, fheight))        
        fig.suptitle('Synthetic hydrographs with Sy = %0.2f' % Sy, fontsize=20)
       
        lmarg  = 0.85 / fwidth
        rmarg = 1.75 / fwidth
        tmarg = 0.5 / fheight
        bmarg = 0.65 / fheight
        
        axwidth = 1 - (lmarg + rmarg)
        axheight = 1 - (bmarg + tmarg)
        
        ax = fig.add_axes([lmarg, bmarg, axwidth, axheight])
        
        #---- Produces Results ----
        
        RASMAX = [0] * len(CRU)
        WLVLPRE = [0] * len(CRU)
        RECHG = [0] * len(CRU)
        RU = [0] * len(CRU)
        ETR = [0] * len(CRU)
        RAS = [0] * len(CRU)
        PACC = [0] * len(CRU)
        for i in range(len(CRU)):
            RASMAX[i], WLVLPRE[i], RECHG[i], RU[i], ETR[i], RAS[i], PACC[i] = \
                self.opt_RASmax(Sy, CRU[i])
        
        #---- Plot Results ----
        
        ax.plot(self.DATE, self.WLVLobs, '0.5', lw=1.5,
                label='Observed\nWater Levels')
        
        for i in range(len(CRU)):
            
            RMSE = self.calc_RMSE(self.WLVLobs[self.NaNindx]*1000,
                                  WLVLPRE[i][self.NaNindx])                                 
            NSE = self.nash_sutcliffe(self.WLVLobs[self.NaNindx]*1000,
                                      WLVLPRE[i][self.NaNindx])
            rechg = np.mean(RECHG[i]) * 365
            
            label = ('Cru = %0.2f\nRASmax = %0.0f\n' + 
                     'RMSE = % 0.0f mm\nNSE = %0.2f\n' +
                     'Rechg = %0.0f mm/y'
                     ) % (CRU[i], RASMAX[i], RMSE, NSE, rechg)
                     
            ax.plot(self.DATE, WLVLPRE[i]/1000., alpha=0.65, lw=1.5,
                    label=label)        
        
        #---- Figure Setup ----
        
        ax.set_ylabel('Water Level (mbgs)', fontsize=16) 
        ax.grid(axis='x', color=[0.65, 0.65, 0.65], ls=':', lw=1)
        ax.set_axisbelow(True)
        
        ax.legend(loc=[1.01, 0], ncol=1, fontsize=8)
        ax.invert_yaxis()
        
        fname = 'Multi_Analysis/Sy=%0.2f_Cru=%0.3f.pdf' % (Sy, CRU[0])
        fig.savefig(fname)
        
        #---- Post Processing Results ----
        
        PRECIP = self.meteoObj.DATA[:, 6]
        YEAR = self.meteoObj.DATA[:, 0]
        MONTH = self.meteoObj.DATA[:, 1]
        DAY = self.meteoObj.DATA[:, 2]
        RECHG = RECHG[0]
        RU = RU[0]
        ETR = ETR[0]
        RAS = RAS[0]
        PACC = PACC[0]
        
#        plot_water_budget_yearly(PRECIP, RECHG, YEAR, RU, ETR)
        
        #---- Save Results in csv ----
        
        fname = 'water_budget.csv'
        fcontent = [['YEAR(mm)', 'MONTH', 'DAY', 'PRECIP(mm)', 'RU(mm)',
                     'ETR(mm)', 'RECHG(mm)', 'RAS(mm)', 'PACC(mm)']]
        for i in range(len(PRECIP)):      
            fcontent.append(['%d' % YEAR[i], 
                             '%d' % MONTH[i],
                             '%d' % DAY[i],
                             '%f' % PRECIP[i],
                             '%f' % RU[i],
                             '%f' % ETR[i],
                             '%f' % RECHG[i],
                             '%f' % RAS[i],
                             '%f' % PACC[i]])
                                
        with open(fname, 'w') as f:
            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
            writer.writerows(fcontent)
        
        
    @staticmethod
    def nash_sutcliffe(Xobs, Xpre): #======================== Nash-Sutcliffe ==
        # Source: Wikipedia
        # https://en.wikipedia.org/wiki/
        # Nash%E2%80%93Sutcliffe_model_efficiency_coefficient
        
        NSE = 1 - np.sum((Xobs - Xpre)**2) / np.sum((Xobs - np.mean(Xobs))**2)
        
        return NSE 
    
    @staticmethod
    def calc_RMSE(Xobs, Xpre): #======================================= RMSE ==
        
        RMSE = (np.mean((Xobs - Xpre)**2))**0.5

        return RMSE
        
    def GLUE(self, Sy, RASmax, Cro): #================================= GLUE ==
        self.Sy = Sy
        self.RASmax = RASmax
        self.Cro = Cro
        
        U_RAS = np.arange(RASmax[0], RASmax[1]+1, 5)
        U_Cro = np.arange(CRO[0], CRO[1]+0.05, 0.05)
        
        #---- weather observations ----
        
        ETP = self.meteoObj.DATA[:, 7]
        PTOT = self.meteoObj.DATA[:, 6]
        TAVG = self.meteoObj.DATA[:, 5]
        
        #---- Produce realization ----
        
        RMSE = []
        RECHG = []
        WLest = []
                
        Sy0 = np.mean(Sy)               
        for i, cro in enumerate(U_Cro):
            for j, rasmax in enumerate(U_RAS):
                rechg, _, _, _, _ = self.surf_water_budget(cro, rasmax,
                                                           ETP, PTOT, TAVG)
                Sy, RMSE = self.opt_Sy(cro, rasmax, Sy0, rechg)                
                Sy0 = Sy
                
                print('Cru = %0.3f ; RASmax = %0.0f mm ; ' +
                      'Sy = %0.3f ; RMSE = %0.1f' ) % (cro, rasmax, Sy, RMSE)
                
    def opt_Sy(self, cro, rasmax, Sy0, rechg):#================= Optimize Sy ==
        
        tweatr = self.meteoObj.TIME + 10 # Here we introduce the time lag
        
        #---- water lvl observations ----
        
        twlvl = self.twlvl
        WLVLobs = self.WLVLobs * 1000
        
        ts = np.where(twlvl[0] == tweatr)[0][0]
        te = np.where(twlvl[-1] == tweatr)[0][0]
        
        #---- MRC ----
        
        A, B = self.waterlvlObj.A, self.waterlvlObj.B
        
        #---- Gauss-Newton ----
        
        tolmax = 0.001      
        Sy = Sy0
        dSy = 0.01
                
        WLVLpre = self.calc_hydrograph(rechg[ts:te], A, B, WLVLobs,
                                       Sy, nscheme='forward')
        RMSE = self.calc_RMSE(WLVLobs[self.NaNindx], WLVLpre[self.NaNindx])
        
        it = 0
        while 1:            
            it += 1
            if it > 100:
                print('Not converging.')
                break                
            
            #---- Calculating Jacobian (X) Numerically ---- 
                                           
            wlvl = self.calc_hydrograph(rechg[ts:te], A, B, WLVLobs,
                                        Sy * (1+dSy), nscheme='forward')
            X = Xt = (wlvl[self.NaNindx] - WLVLpre[self.NaNindx]) / (Sy * dSy)       
            
            #---- Solving Linear System ----
            
            dh = WLVLobs[self.NaNindx] - WLVLpre[self.NaNindx]
            XtX = np.dot(Xt, X)                
            Xtdh = np.dot(Xt, dh)
            
            dr = np.linalg.tensorsolve(XtX, Xtdh, axes=None)
            
            #---- Storing old parameter values ----
            
            Syold = np.copy(Sy)
            RMSEold = np.copy(RMSE)

            while 1: # Loop for Damping (to prevent overshoot)

                #---- Calculating new paramter values ----

                Sy = Syold + dr
                    
                #---- Solving for new parameter values ----

                WLVLpre = self.calc_hydrograph(rechg[ts:te], A, B, WLVLobs,
                                               Sy, nscheme='forward')
                RMSE = self.calc_RMSE(WLVLobs[self.NaNindx],
                                      WLVLpre[self.NaNindx])

                #---- Checking overshoot ----
                
                if (RMSE - RMSEold) > 0.1:
                    dr = dr * 0.5
                else:
                    break
    
            #---- Checking tolerance ----
            
            tol = np.abs(Sy - Syold)            
            
            if tol < tolmax:
                return Sy, RMSE
            
        
    def opt_Cru(self, Sy): #=================================== Optimize Cru ==
        
        # Optimization is done with a robust approach where all posiblities are
        # tested and the one with the lowest RMSE is chosen as the optimal
        # solution. This was done because the conventional Gauss-Newton
        # approach was not converging well and there was problem with local
        # extremum.
        
        #---- Rough Optimization (0.05 step) ----
        
        Cru = np.arange(0.05, 0.7, 0.05)
        RMSE = np.zeros(len(Cru))
        RASMAX = np.zeros(len(Cru))
        RECHG = [0] * len(Cru)
        WLVLpre = [0] * len(Cru)
        
        for i, cru in enumerate(Cru):
            
            RASMAX[i], WLVLpre[i], RECHG[i] = self.opt_RASmax(Sy, cru)
            RMSE[i] = self.calc_RMSE(self.WLVLobs[self.NaNindx] * 1000, 
                                     WLVLpre[i][self.NaNindx])
        
        print('')
        
        #---- Fine Optimization (0.01 ste) ----
        
        indx = np.where(RMSE == np.min(RMSE))[0][0]
        
        Cru = np.arange(Cru[indx]-0.05, Cru[indx]+0.06, 0.01)        
        RMSE = np.zeros(len(Cru))
        RASMAX = np.zeros(len(Cru))
        RECHG = [0] * len(Cru)
        WLVLpre = [0] * len(Cru)
        
        for i, cru in enumerate(Cru):
            RASMAX[i], WLVLpre[i], RECHG[i] = self.opt_RASmax(Sy, cru)
            RMSE[i] = self.calc_RMSE(self.WLVLobs[self.NaNindx] * 1000, 
                                     WLVLpre[i][self.NaNindx])
        
        indx = np.where(RMSE == np.min(RMSE))[0][0]
       
        return Cru[indx], RASMAX[indx], WLVLpre[indx], RECHG[indx]        
        
                
    def opt_RASmax(self, Sy, CRU): #======================== Optimize RASmax ==
        
        #---- weather observations ----
        
        ETP = self.meteoObj.DATA[:, 7]
        PTOT = self.meteoObj.DATA[:, 6]
        TAVG = self.meteoObj.DATA[:, 5]
        tweatr = self.meteoObj.TIME + 10 # Here we introduce the time lag
        
        #---- water lvl observations ----
        
        twlvl = self.twlvl
        WLVLobs = self.WLVLobs * 1000
        
        ts = np.where(twlvl[0] == tweatr)[0][0]
        te = np.where(twlvl[-1] == tweatr)[0][0]     
        
        #---- MRC ----
        
        A, B = self.waterlvlObj.A, self.waterlvlObj.B

        #---- Gauss-Newton ----
        
        tolmax = 1.      
        RASMAX = 100.
        dRAS = 0.1
        
        RECHG, _, _, _, _ = self.surf_water_budget(CRU, RASMAX, ETP,
                                                   PTOT, TAVG)
        WLVLpre = self.calc_hydrograph(RECHG[ts:te], A, B, WLVLobs,
                                       Sy, nscheme='forward')
        RMSE = self.calc_RMSE(WLVLobs[self.NaNindx], WLVLpre[self.NaNindx])
        
        it = 0
        while 1:            
            it += 1
            if it > 100:
                print('Not converging.')
                break                
            
            #---- Calculating Jacobian (X) Numerically ---- 
            
            rechg, _, _, _, _ = self.surf_water_budget(CRU, RASMAX * (1+dRAS),
                                                       ETP, PTOT, TAVG) 
                                           
            wlvl = self.calc_hydrograph(rechg[ts:te], A, B, WLVLobs,
                                        Sy, nscheme='forward')
            X = Xt = (wlvl[self.NaNindx] - WLVLpre[self.NaNindx]) / (RASMAX * dRAS)       

            if np.sum(X) == 0:
                rechg_yearly = np.mean(RECHG) * 365
                RASMAX = np.inf
                print('Cru = %0.3f ; RASmax = %0.0f mm ; ' +
                      'RMSE = %0.1f mm ; Rechg = %0.0f mm' 
                      ) % (CRU, RASMAX, RMSE, rechg_yearly)              
                return RASMAX, WLVLpre, RECHG
            
            #---- Solving Linear System ----
            
            dh = WLVLobs[self.NaNindx] - WLVLpre[self.NaNindx]
            XtX = np.dot(Xt, X)                
            Xtdh = np.dot(Xt, dh)
            
            dr = np.linalg.tensorsolve(XtX, Xtdh, axes=None)
            
            #---- Storing old parameter values ----
            
            RASMAXold = np.copy(RASMAX)
            RMSEold = np.copy(RMSE)

            while 1: # Loop for Damping (to prevent overshoot)

                #---- Calculating new paramter values ----

                RASMAX = RASMAXold + dr
                    
                #---- Solving for new parameter values ----

                RECHG, RU, ETR, RAS, PACC = self.surf_water_budget(
                                                  CRU, RASMAX, ETP, PTOT, TAVG)
                WLVLpre = self.calc_hydrograph(RECHG[ts:te], A, B, WLVLobs,
                                               Sy, nscheme='forward')
                RMSE = self.calc_RMSE(WLVLobs[self.NaNindx],
                                      WLVLpre[self.NaNindx])

                #---- Checking overshoot ----
                
                if (RMSE - RMSEold) > 0.1:
                    dr = dr * 0.5
                else:
                    break
                
            #---- Applying parameter bound-constraints ----
            
            if RASMAX < 0:
                RASMAX = 0
                rechg_yearly = np.mean(RECHG) * 365
                print('Cru = %0.2f ; RASmax = %0.0f mm ; ' +
                      'RMSE = %0.1f mm ; Rechg = %0.0f mm' 
                      ) % (CRU, RASMAX, RMSE, rechg_yearly)
                      
                return RASMAX, WLVLpre, RECHG
    
            #---- Checking tolerance ----
#            print RASMAX
            
            tol = np.abs(RASMAX - RASMAXold)            
            
            if tol < tolmax:
#                out = np.correlate(WLVLobs, WLVLpre[:-100])
#                plt.plot(out)
                rechg_yearly = np.mean(RECHG) * 365
                print('Cru = %0.3f ; RASmax = %0.0f mm ; ' +
                      'RMSE = %0.1f mm ; Rechg = %0.0f mm' 
                      ) % (CRU, RASMAX, RMSE, rechg_yearly)
                return RASMAX, WLVLpre, RECHG, RU, ETR, RAS, PACC
        
    @staticmethod
    def surf_water_budget(CRU, RASmax, ETP, PTOT, TAVG, TMELT=1.5, CM=4 ):
        
        """    
        Input
        -----
        {float} CRU = Runoff coefficient
        {float} RASmax = Readily Available Storage Max in mm
        {1D array} ETP = Dailty evapotranspiration in mm
        {1D array} PTOT = Daily total precipitation in mm
        {1D array} TAVG = Daily average air temperature in deg. C.
        
        CM: Daily melt coefficient
        TMELT: Temperature treshold for snowmelt
        
        Output
        ------
        {1D array} RECHG = Daily groundwater recharge in mm    
        """
        
        N = len(ETP)

        PAVL = np.zeros(N)   # Available Precipitation
        PACC = np.zeros(N)   # Accumulated Precipitation
        RU = np.zeros(N)     # Runoff
        I = np.zeros(N)      # Infiltration
        ETR = np.zeros(N)    # Evapotranspiration Real
        dRAS = np.zeros(N)   # Variation of RAW
        RAS = np.zeros(N)    # Readily Available Storage
        RECHG = np.zeros(N)  # Recharge (mm)
                
        MP = CM * (TAVG - TMELT)  # Snow Melt Potential
        MP[MP < 0] = 0
        
        PACC[0] = 0
        RAS[0] = RASmax
        
        for i in range(N-1):
    
            #----- Precipitation, Accumulation, and Melt -----
            
            if TAVG[i] > TMELT:  # Rain
            
                if MP[i] >= PACC[i]: # Rain on Bareground (All snow is melted)
                    PAVL[i] = PACC[i] + PTOT[i]
                    PACC[i+1] = 0
                    
                elif MP[i] < PACC[i]: # Rain on Snow
                    PAVL[i] = MP[i]
                    PACC[i+1] = PACC[i] - MP[i] + PTOT[i]                
                    
            elif TAVG[i] <= TMELT: # Snow
                PAVL[i] = 0
                PACC[i+1] = PACC[i] + PTOT[i]
                
    
#            if TAVG[i] > TMELT:  # Rain
#            
#                if MP[i] >= PACC[i]: # Rain on Bareground
#                    PAVL[i+1] = PACC[i] + PTOT[i]
#                    PACC[i+1] = 0
#                    
#                elif MP[i] < PACC[i]: #Rain on Snow
#                    PAVL[i+1] = MP[i]
#                    PACC[i+1] = PACC[i] - MP[i] + PTOT[i]                
#                    
#            elif TAVG[i] <= TMELT: #Snow
#                PAVL[i+1] = 0
#                PACC[i+1] = PACC[i] + PTOT[i]
                
            #----- Infiltration and Runoff -----
            
            RU[i] = CRU * PAVL[i]
            I[i] = PAVL[i] - RU[i]
            
            #----- ETR, Recharge and Storage change -----
            
            #Intermediate Step
            dRAS[i] = min(I[i], RASmax - RAS[i])
            RAS[i+1] = RAS[i] + dRAS[i]
            
            #Final Step
            RECHG[i] = I[i] - dRAS[i]            
            ETR[i] = min(ETP[i], RAS[i])            
            RAS[i+1] = RAS[i+1] - ETR[i]
            
            # Evaportransporation is calculated after recharge. It is assumed
            # that recharge occurs on a time scale that is faster than
            # evapotranspiration in permeable soil.
            
#        print np.sum(PTOT - ETR - RECHG - RU) - (RAS[-1] - RAS[0])
        
        return RECHG, RU, ETR, RAS, PACC
    
    @staticmethod
    def calc_hydrograph(RECHG, A, B, WLobs, Sy, nscheme='forward'): #==========
        """
        This is a forward numerical explicit scheme for generating the
        synthetic well hydrograph.
        
        This is a backward explicit scheme to produce a synthetic well
        hydrograph. The water level starts at the last days in the observed
        water level time series and generate the hydrograph by going backward
        in time. This is very usefull when one which to produce water level
        for the period of time before water level measurements are
        available.
        
        Parameters
        ----------
        Wlpre: Predicted Water Level (mm)
        Sy: Specific Yield
        RECHG: Groundwater Recharge (mm)
        WLobs: Observed Water Level (mm)
        
        A, B: MRC Parameters, where: Recess(m/d) = -A * h + B
        nscheme: Option are "forward" or "downdward" depending if the 
                 hydrograph is being built forward in time or backward. 
                 Default is "forward".
        """
        
        # It should also be possible to do a Crank-Nicholson on this. I should
        # check this out.
        
        WLpre = np.zeros(len(RECHG)+1) * np.nan
        
        if nscheme == 'backward':
            
            WLpre[0] = WLobs[-1]
            
            for i in reversed(range(len(RECHG))):
                RECESS = (B - A * WLpre[i] / 1000.) * 1000
                RECESS = max(RECESS, 0)
                
                WLpre[i] = WLpre[i+1] + (RECHG[i] / Sy) - RECESS
            
        elif nscheme == 'forward':
            
            WLpre[0] = WLobs[0]
            
            for i in range(len(RECHG)):
#                if i%365 == 0:
#                    WLpre[i+1] = WLobs[i]
#                else:                
                RECESS = (B - A * WLpre[i] / 1000.) * 1000
                RECESS = max(RECESS, 0)
                        
                WLpre[i+1] = WLpre[i] - (RECHG[i] / Sy) + RECESS
        else:
            WLpre = []
            
        return WLpre
        
    
    @staticmethod
    def mrc2rechg(t, hobs, A, B, z, Sy): #=====================================
 
        """
        Calculate groundwater recharge from the Master Recession Curve (MRC)
        equation defined by the parameters A and B, the water level time series
        in mbgs (t and ho) and the soil column description (z and Sy), using
        the water-level fluctuation principle.
           
        INPUTS
        ------
        {1D array} t : Time in days 
        {1D array} hobs = Observed water level in mbgs
        {float}    A = Model parameter of the MRC
        {float}    B = Model parameter of the MRC
        {1D array} z = Depth of the soil layer limits
        {1D array} Sy = Specific yield for each soil layer
        {1D array} indx = Time index defining the periods over which recharge
                          is to be computed. Odd index numbers are for the
                          beginning of periods while even index numbers are for
                          the end of periods.
                             
        OUTPUTS
        -------       
        {1D array} RECHG = Groundwater recharge time series in m
    
        Note: This is documented in logbook #11, p.23.
        """
        
        #---- Check Data Integrity ----
        
        if np.min(hobs) < 0:
            print('Water level rise above ground surface. Please check your data.')
            return
    
        dz = np.diff(z) # Tickness of soil layer
        
        dt = np.diff(t)
        RECHG = np.zeros(len(dt))
        
        # !Do not forget it is mbgs. Everything is upside down!

        for i in range(len(dt)):
            
            # Calculate projected water level at i+1
            
            LUMP1 = 1 - A * dt[i] / 2
            LUMP2 = B * dt[i]
            LUMP3 = (1 + A * dt[i] / 2) ** -1
            
            hp = (LUMP1 * hobs[i] + LUMP2) * LUMP3
            
            # Calculate resulting recharge over dt (See logbook #11, p.23)
                    
            hup = min(hp, hobs[i+1])
            hlo = max(hp, hobs[i+1])
                    
            iup = np.where(hup >= z)[0][-1]
            ilo = np.where(hlo >= z)[0][-1]
            
            RECHG[i] = np.sum(dz[iup:ilo+1] * Sy[iup:ilo+1])        
            RECHG[i] -= (z[ilo+1] - hlo) * Sy[ilo]
            RECHG[i] -= (hup - z[iup]) * Sy[iup]
            
            # RECHG[i] will be positive in most cases. In theory, it should always
            # be positive, but error in the MRC and noise in the data can cause hp
            # to be above ho in some cases.
            
            RECHG[i] *= np.sign(hp - hobs[i+1])
               
        return RECHG 

    
if __name__ == '__main__':
   
    plt.close('all')
    
    #---- Pont-Rouge ----
    
    dirname = '../Projects/Pont-Rouge/'
    fmeteo = dirname + 'Meteo/Output/STE CHRISTINE (7017000)_1960-2015.out'
    fwaterlvl = dirname + 'Water Levels/5080001.xls'
      
    #---- Valcartier ----

#    dirname = '/home/jnsebgosselin/Dropbox/Valcartier/Valcartier'
#    fmeteo = dirname + '/Meteo/Output/Valcartier (9999999)/Valcartier (9999999)_1994-2015.out'
#    fwaterlvl = dirname + '/Water Levels/valcartier2.xls'      
    
    #---- Calculations ----
    
    synth_hydrograph = SynthHydrograph(fmeteo, fwaterlvl)
    
    Sy = [0.2, 0.3]
    RASmax = [25, 200]
    CRO = [0.2, 0.4]
    
    synth_hydrograph.GLUE(Sy, RASmax, CRO)
    
#    Sy = 0.25
#    synth_hydrograph.plot_best_fit(Sy)
    
#    CRU = np.arange(0.385, 0.365, 0.005)
#    CRU = [0.31]
#    CRU = np.arange(0, 0.65, 0.05)    
#    for cru in CRU:    
#        synth_hydrograph.plot_multiple_fit(Sy, [cru])
        
    print('Fin')
    
#    plt.show()
    
