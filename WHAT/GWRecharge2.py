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

#----- STANDARD LIBRARY IMPORTS -----
      
from datetime import date
import csv

#----- THIRD PARTY IMPORTS -----

import numpy as np
from xlrd import xldate_as_tuple
from xlrd.xldate import xldate_from_date_tuple
import matplotlib.pyplot as plt

#----- PERSONAL LIBRARY IMPORTS -----

from meteo import MeteoObj, calculate_normals
from waterlvldata import WaterlvlData


#==============================================================================
def calc_hydrograph_up(RECHG, RECESS, WLobs):
    """
    This is a forward numerical explicit scheme for generating the
    synthetic well hydrograph.
    """
#==============================================================================

    Sy = -sum(RECHG) / (-sum(RECESS) + WLobs[-1] - WLobs[0])
    
    WLsim = np.zeros(len(WLobs))
    print '%0.2f' % Sy
    if Sy > 0.4 or Sy < 0.3:
        WLsim[:] = np.nan
    else:
        WLsim[0] = WLobs[0]
         
        for i in range(0, len(WLobs) - 1):            
            WLsim[i+1] = WLsim[i] - (RECHG[i] / Sy) + RECESS[i]

    return WLsim, Sy
    


#==============================================================================

class SynthHydrograph(object):
    
#==============================================================================
    
    def __init__(self, fmeteo, fwaterlvl):
    
        #---- Load Data ----
    
        print('--------')
        self.meteoObj = MeteoObj()
        self.meteoObj.load_and_format(fmeteo)
        print('--------')
        self.waterlvlObj = WaterlvlData()
        self.waterlvlObj.load(fwaterlvl)
        
        #---- Do Some Stuff ----
        
        varnames = np.array(self.meteoObj.varnames)
        ETP = self.meteoObj.DATA[:, 7]
        PTOT = self.meteoObj.DATA[:, 6]
        TAVG = self.meteoObj.DATA[:, 6]
        
        WLVLobs = self.waterlvlObj.lvl * 1000
        A, B = self.waterlvlObj.A, self.waterlvlObj.B
        
        CRU = 0.39 
        RASmax = 90 
        Sy = 0.25
        
        RECHG = self.surf_water_budget(CRU, RASmax, ETP, PTOT, TAVG)
        WLVLpre = self.calc_hydrograph_down(RECHG, A, B, WLVLobs[-1], Sy)
        
        indx = np.where(self.waterlvlObj.time[-1] == self.meteoObj.TIME)[0]
        print indx 
        
        plt.close('all')
        fig, ax = plt.subplots()
        ax.plot(self.waterlvlObj.time, WLVLobs)
        ax.plot(self.meteoObj.TIME + 40, WLVLpre, 'r')
        ax.invert_yaxis()
        plt.show(block=False)
        
        Wsy = self.calc_hydrograph_down(RECHG, A, B, WLVLobs[-1], Sy * 1.05)
        ss_sy = (Wsy-WLVLpre) / 0.05

        Rcru = self.surf_water_budget(CRU * 1.05, RASmax, ETP, PTOT, TAVG)
        Wcru = self.calc_hydrograph_down(Rcru, A, B, WLVLobs[-1], Sy)
        ss_cru = (Wcru-WLVLpre) / 0.05
        
        Rras = self.surf_water_budget(CRU, RASmax * 1.05, ETP, PTOT, TAVG)
        Wras = self.calc_hydrograph_down(Rras, A, B, WLVLobs[-1], Sy)
        ss_ras = (Wras-WLVLpre) / 0.05
        
        ss_mat = np.vstack((ss_sy, ss_cru, ss_ras))
        
        VCo_mat = np.dot(ss_mat, ss_mat.T)
        
        pcc = np.zeros((3,3)) + np.diag([1,1,1])
        #qz and porosity
        pcc[0,1] = VCo_mat[0,1]/(VCo_mat[0,0]**0.5*VCo_mat[1,1]**0.5)
        pcc[1,0] = pcc[0,1]
        #qz and soil moisture
        pcc[0,2] = VCo_mat[0,2]/(VCo_mat[0,0]**0.5*VCo_mat[2,2]**0.5)
        pcc[2,0] = pcc[0,2]
        #porosity and soil moisture
        pcc[2,1] = VCo_mat[2,1]/(VCo_mat[2,2]**0.5*VCo_mat[1,1]**0.5)
        pcc[1,2] = pcc[2,1]
        
        print pcc

        
        
    @staticmethod
    def surf_water_budget(CRU, RASmax, ETP, PTOT, TAVG): #=====================
    
        """    
        Input
        -----
        {float} CRU = Runoff coefficient
        {float} RASmax = Maximal Readily Available Storage in mm
        {1D array} ETP = Dailty evapotranspiration in mm
        {1D array} PTOT = Daily total precipitation in mm
        {1D array} TAVG = Daily average air temperature in deg. C.
        
        Output
        ------
        {1D array} RECHG = Daily groundwater recharge in mm    
        """
        
        N = len(ETP)    
        PAVL = np.zeros(N)    # Available Precipitation
        PACC = np.zeros(N)    # Accumulated Precipitation
        RU = np.zeros(N)      # Runoff
        I = np.zeros(N)       # Infiltration
        ETR = np.zeros(N)     # Evapotranspiration Real
        dRAS = np.zeros(N)    # Variation of RAW
        RAS = np.zeros(N)     # Readily Available Storage
        RECHG = np.zeros(N)   # Recharge (mm)
        
        TMELT = 0 # Temperature treshold for snowmelt
        CM = 4 # Daily melt coefficient
        
        MP = CM * (TAVG - TMELT)  # Snow Melt Potential
        MP[MP < 0] = 0
        
        PACC[0] = 0
        RAS[0] = RASmax
        
        for i in range(0, N - 1):
    
            #----- Precipitation -----          
    
            if TAVG[i] > TMELT:  # Rain
            
                if MP[i] >= PACC[i]: # Rain on Bareground
                    PAVL[i+1] = PACC[i] + PTOT[i]
                    PACC[i+1] = 0
                    
                elif MP[i] < PACC[i]: #Rain on Snow
                    PAVL[i+1] = MP[i]
                    PACC[i+1] = PACC[i] - MP[i] + PTOT[i]                
                    
            elif TAVG[i] <= TMELT: #Snow
                PAVL[i+1] = 0
                PACC[i+1] = PACC[i] + PTOT[i]
                
            #----- Infiltration and Runoff -----
            
            RU[i] = CRU * PAVL[i]
            I[i] = PAVL[i] - RU[i]
            
            #----- ETR, Recharge and Storage change -----
            
            dRAS[i] = min(I[i], RASmax - RAS[i])
            RAS[i+1] = RAS[i] + dRAS[i] #intermediate step
            RECHG[i] = I[i] - dRAS[i]
            
            ETR[i] = min(ETP[i], RAS[i])
            
            RAS[i+1] = RAS[i+1] - ETR[i]
        
        return RECHG
    
    @staticmethod
    def calc_hydrograph_down(RECHG, A, B, WL0, Sy): #====== Calc. Hydrograph ==
    
        """
        Parameters
        ----------
        Wlpre: Predicted Water Level (mm)
        Sy: Specific Yield
        RECHG: Groundwater Recharge (mm)
        
        A, B: MRC Parameters, where: Recess(mm/d) = -A * h + B    
        """
    
        # This is a backward numerical explicit scheme. This was used to do
        # the interpretation of the hydrograph at Dundurn. I need to find 
        # where I've documented this.
        #
        # It should also be possible to do a Crank-Nicholson on this. I should
        # check this out.
        
        WLpre = np.zeros(len(RECHG)) * np.nan
        WLpre[-1] = WL0
        
        for i in reversed(range(1, len(RECHG))):
            RECESS = (B - A * WLpre[i] / 1000.) * 1000
            if RECESS < 0:
                RECESS = 0
            elif RECESS > B * 1000:
                RECESS = B * 1000
            
            WLpre[i-1] = WLpre[i] + (RECHG[i] / Sy) - RECESS
            
        return WLpre
    
#    #---- Assign Variables ----
#    
#    PTOT = meteoObj.PTOT # Daily total precipitation (mm)    
#    YEAR = meteoObj.YEAR
#    
#    PTOT = meteoObj.PTOT # Daily total precipitation (mm)
#    TAVG = meteoObj.TAVG # Daily mean temperature (deg C)
#    TIMEmeteo = meteoObj.TIME # Time (days)
#    LAT = float(meteoObj.LAT) # Latitude (deg)
#    
#    YEAR = meteoObj.YEAR
#    MONTH = meteoObj.MONTH
#    
#    RAIN = meteoObj.RAIN
#    
#    Ta, _, _, _ = calculate_normals(YEAR, MONTH, TAVG, PTOT, RAIN) # Monthly normals
#    
#    ETP = meteo.calculate_ETP(TIMEmeteo, TAVG, LAT, Ta) # Daily potential reference 
#                                                        # evapotranspiration (mm) 
        
    
#============================================================================== 
def bestfit_hydrograph(meteoObj, waterlvlObj):
#==============================================================================
   
    plt.close('all')
    
    #---- Load Meteo -----
    
    PTOT = meteoObj.PTOT # Daily total precipitation (mm)
    TAVG = meteoObj.TAVG # Daily mean temperature (deg C)
    TIMEmeteo = meteoObj.TIME # Time (days)
    LAT = float(meteoObj.LAT) # Latitude (deg)
    
    YEAR = meteoObj.YEAR
    MONTH = meteoObj.MONTH
    
    RAIN = meteoObj.RAIN
    
    Ta, _, _, _ = calculate_normals(YEAR, MONTH, TAVG, PTOT, RAIN) # Monthly normals
    
    ETP = meteo.calculate_ETP(TIMEmeteo, TAVG, LAT, Ta) # Daily potential reference 
                                                        # evapotranspiration (mm)
    
    print np.mean(ETP)
    
    #---- Load Waterlvl -----
    
    WLogger = waterlvlObj.lvl * 1000 # Observed groundwater level (mbgs)
    TIMEwater = waterlvlObj.time  # Time (days)
    
#  ----------------------------------------------------- LONG TREND ANALYSIS --
    
#    indx0 = np.where(TIMEmeteo <= TIMEwater[0])[0][-1]
#    indxE = np.where(TIMEmeteo >= TIMEwater[-1])[0][0]
    
#    Resample observed water level on a daily basis.
#    WLobs = np.interp(TIMEmeteo[indx0:indxE], TIMEwater, WLobs)
#    plt.plot(-WLobs)

    CRU = np.arange(0, 0.31, 0.05)
    RASmax = np.zeros(len(CRU))
    RMSE = np.zeros(len(CRU))
    RECHyr = np.zeros(len(CRU))
    
    RECESS = np.ones(len(TIMEmeteo)) * 0.69 # Water level recession (mm/d)
    WL0 = 6150 #np.mean(WLogger) #Initial water level (mm)
    Sy = 0.35 - 0.06
    
    #---- MANUAL OBS. WL ----
    
    TIMEobs = np.array([35034, 35400, 35674, 40878, 41214, 41609, 41876])
    
    WLobs = np.array([6.8+0.73, 6.8+0.59, 6.8+0.64, 6.8, 6.47, 6.29, 6.15]) * 1000
    
    plt.plot(TIMEobs, -WLobs, 'or')
    
    indx = np.zeros(len(TIMEobs))
    for i in range(len(TIMEobs)):
        indx[i] = np.where(TIMEobs[i] == TIMEmeteo)[0][0]        
    indx = indx.astype(int)
    
    # The program search for solutions with a long time trend that is close to
    # zero. There is no unique solution, but each solution gives mean recharge
    # rates that are equivalent and equal to the recession.
    
    for it in range(len(CRU)):
        
        RECHG = surf_water_budget(CRU[it], RASmax[it], ETP, PTOT, TAVG)
        WLsim = calc_hydrograph(RECHG, RECESS, WL0, Sy)
    
#        SLOPEnew = np.polyfit(TIMEmeteo, WLsim, 1)[0]        
#        delta_RAS = 10
#        while abs(delta_RAS) >= 0.001:
#            while 1:
#                SLOPEold = np.copy(SLOPEnew)
#                
#                RASmax[it] += delta_RAS
#                
#                RECHG = surf_water_budget(CRU[it], RASmax[it], ETP, PTOT, TAVG)
#                WLsim = calc_hydrograph(RECHG, RECESS, WL0, Sy)
#                
##                dWL = WLobs[0] - WL[indx[0]]
##                WLobs -= dWL
#                
#                print (np.mean(WLsim[indx] - WLobs)**2)**0.5
#                
#                SLOPEnew = np.polyfit(TIMEmeteo, WLsim, 1)[0]
#                
##                print SLOPEnew                
#                
#                if np.sign(SLOPEold) != np.sign(SLOPEnew):
#                    delta_RAS /= -10.
#                    break
#                
#                if abs(SLOPEold) < abs(SLOPEnew):
#                    delta_RAS *= -1
#                    break
                
                
        RMSEnew = 10**6
        delta_RAS = 10
        while abs(delta_RAS) >= 0.1:
            while 1:
                RMSEold = np.copy(RMSEnew)
                
                RASmax[it] += delta_RAS
                RMSE[it] = RMSEold
                
                RECHG = surf_water_budget(CRU[it], RASmax[it], ETP, PTOT, TAVG)
                WLsim = calc_hydrograph(RECHG, RECESS, WL0, Sy)
                
#                dWL = WLobs[-1] - WLsim[indx[-1]]
#                WLobs -= dWL
                
                RMSEnew = (np.mean((WLsim[indx] - WLobs)**2))**0.5
                
                print RMSEnew                
                
                if RMSEnew > RMSEold:
                    delta_RAS /= -10.
                    break
                
#                if abs(SLOPEold) < abs(SLOPEnew):
#                    delta_RAS *= -1
#                    break
                
        RECHyr[it] = np.mean(RECHG) * 365
        print 'NEW solution'
#        print RECHyr[it]
        plt.plot(TIMEmeteo, -WLsim, color='gray')
        
        plt.pause(0.1)
    
    print CRU
    print RASmax  
    print RECHyr
    print RMSE     
    
    WLintrp = np.interp(TIMEwater, TIMEmeteo, WLsim)
    dWL = np.mean(WLintrp) - np.mean(WLogger)
    WLogger += dWL
    print dWL
                
#    plt.plot(TIMEwater, -WLogger, color='r')
    
#    RECHG = surf_water_budget(0, 35.81, ETP, PTOT, TAVG)
#    WLsim = calc_hydrograph(RECHG, RECESS, WL0, Sy)
    
#    plt.figure()
#    plt.plot(TIMEmeteo, -WLsim, color='blue')
#    plt.plot(TIMEwater, -WLogger, 'r')

    indx = np.where(RMSE == np.min(RMSE))[0][0]
    
    RECHG = surf_water_budget(CRU[indx], RASmax[indx], ETP, PTOT, TAVG)
    WLsim = calc_hydrograph(RECHG, RECESS, WL0, Sy)
    
    return RECHG, WLsim
    
#==============================================================================
def plot_water_budget_yearly(PRECIP, RECHG, DATE_YEAR):
#==============================================================================
   
#    RUNOFF = SIMOUT.WBudget[:, 13]
#    ET = SIMOUT.WBudget[:, 6]
#    PRECIP = SIMOUT.WBudget[:, 3]
#    RECHG = SIMOUT.WBudget[:, 12]
#    Z = SIMOUT.Z

#    index = np.where(Z > 1)[0][0]    
        
#    QWSOIL = SIMOUT.QWSOIL[:, index] # Water Flux just below 1.0 m depth
    YEAR = np.arange(1970, 2015).astype('int')    
    NYear = len(YEAR)
    
#    DATE_YEAR = SIMOUT.DATE[1:, 2].astype('int')

    YEARLY_PRECIP = np.zeros(NYear) 
    YEARLY_RECHG = np.zeros(NYear) 
#    YEARLY_RUNOFF = np.zeros(NYear)
#    YEARLY_ET = np.zeros(NYear)
#    YEARLY_QWSOIL = np.zeros(NYear)
    
    for i in range(NYear):
        indexes = np.where(DATE_YEAR == YEAR[i])[0]
        
        YEARLY_PRECIP[i] = np.sum(PRECIP[indexes])
        YEARLY_RECHG[i] = np.sum(RECHG[indexes])
#        YEARLY_RUNOFF[i] = np.sum(RUNOFF[indexes])
#        YEARLY_ET[i] = np.sum(ET[indexes])
#        YEARLY_QWSOIL[i] = np.sum(QWSOIL[indexes])
    
    print
    print 'Mean Yearly Precip = ', np.mean(YEARLY_PRECIP), 'mm'
    print 'Mean Yearly Recharge = ', np.mean(YEARLY_RECHG), 'mm'
#    print 'Mean Yearly Runoff = ', np.mean(YEARLY_RUNOFF), 'mm'
#    print 'Mean Yearly ET = ', np.mean(YEARLY_ET), 'mm'
#    print 'Mean Yearly Recharge @ 1m = ', np.mean(YEARLY_QWSOIL), 'mm'
                    
    fig = plt.figure(figsize=(15, 7))
    fig.patch.set_facecolor('white')
    
    fheight = fig.get_figheight()
    fwidth = fig.get_figwidth()
    
    left_margin  = 1
    right_margin = 0.35
    bottom_margin = 0.75
    top_margin = 0.25
    
    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w0 = 1 - (left_margin + right_margin) / fwidth
    h0 = 1 - (bottom_margin + top_margin) / fheight
   
    #---------------------------------------------------------AXES CREATION-----

    ax0  = fig.add_axes([x0, y0, w0, h0])
    ax0.patch.set_visible(False)
        
    #------------------------------------------------------------AXIS RANGE-----       
    
    Ymin0 = 0
    Ymax0 = 650#1800
    
    Xmin0 = YEAR[0] - 1
    Xmax0 = YEAR[-1]
    
    #------------------------------------------------------XTICKS FORMATING----- 
   
    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x',direction='out', gridOn=False)
    ax0.set_xticks(YEAR)
    ax0.xaxis.set_ticklabels([])
    
    ax0.set_xticks(YEAR[::2]-0.4, minor=True)
    ax0.tick_params(axis='x', which='minor', length=0, gridOn=False, pad=5)
    ax0.xaxis.set_ticklabels(YEAR[::2], minor=True, rotation=90,
                             horizontalalignment='center')
    
    #------------------------------------------------------YTICKS FORMATING-----
 
    ax0.yaxis.set_ticks_position('left')
    ax0.tick_params(axis='y',direction='out', gridOn=True)
    
    ax0.set_yticks(np.arange(0, 700, 50), minor=True)
    ax0.tick_params(axis='y',direction='out', which='minor', gridOn=True)
    
    #------------------------------------------------------------AXIS RANGE-----
    
    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

    #----------------------------------------------------------------LABELS-----
    
    ax0.set_ylabel('Equivalent Water (mm)', fontsize=14,
                   verticalalignment='bottom')
    ax0.yaxis.set_label_coords(-0.04, 0.5)

#    
#    ax0.set_xlabel(LabelDB.years, fontsize=label_font_size,
#                   verticalalignment='top')
#    ax0.xaxis.set_label_coords(0.5, -0.075)
    
    #--------------------------------------------------------------PLOTTING-----
                         
    lspoint = '-'
    lstrend = '--'
    
    #----- PRECIP -----
    
    ax0.plot(YEAR-0.5, YEARLY_PRECIP,
             color='blue', markeredgecolor='None', marker='o',
             markersize=5, linestyle=lspoint, label='Precipitation',
             clip_on=False, zorder=100)
             
    A = np.polyfit(YEAR-0.5, YEARLY_PRECIP, 1)
    print 'Trend Precip =', A[0], ' mm/y'
    TREND1 = A[0]*(YEAR-0.5) + A[1]
    ax0.plot(YEAR-0.5, TREND1, color='blue', linestyle=lstrend,
             marker='None', label='Trend Line Precipitation', clip_on=False,
             zorder=100)
    

    ax0.text(YEAR[0] + 0.25, 515,
             'Mean Yearly Precipitation = %d mm' % np.mean(YEARLY_PRECIP),
             color='b', fontsize=14)
             
    ax0.text(YEAR[0] + 0.25, 165,
             'Mean Yearly Recharge = %d mm' % np.mean(YEARLY_RECHG),
             color='orange', fontsize=14)
    
    #----- RECHG -----
    
    ax0.plot(YEAR-0.5, YEARLY_RECHG,
             color='orange', markeredgecolor='None', marker='^',
             markersize=8, linestyle=lspoint, label='Recharge',
             clip_on=False, zorder=100)  
             
    A = np.polyfit(YEAR-0.5, YEARLY_RECHG, 1)
    print 'Trend Rechg =', A[0], ' mm/y'
    TREND1 = A[0]*(YEAR-0.5) + A[1]
    ax0.plot(YEAR-0.5, TREND1, color='orange', linestyle=lstrend,
             marker='None', label='Trend Line Recharge', clip_on=False,
             zorder=100)             
    
#    #----- RUNOF -----    
#    
#    ax0.plot(YEAR-0.5, YEARLY_RUNOFF,
#             color='red', markeredgecolor='None', marker='s',
#             markersize=5, linestyle=lspoint, label='Runoff',
#             clip_on=False, zorder=100)
#             
#    A = np.polyfit(YEAR-0.5, YEARLY_RUNOFF, 1)
#    print 'Trend Runoff =', A[0], ' mm/y'
#    TREND1 = A[0]*(YEAR-0.5) + A[1]
#    ax0.plot(YEAR-0.5, TREND1, color='red', linestyle=lstrend,
#             marker='None', label='Trend Line Runoff', clip_on=False,
#             zorder=100) 
#    
#    #----- ETP -----
#        
#    ax0.plot(YEAR-0.5, YEARLY_ET,
#             color='green', markeredgecolor='None', marker='D',
#             markersize=5, linestyle=lspoint, label='ETP',
#             clip_on=False, zorder=100)
#             
#    A = np.polyfit(YEAR-0.5, YEARLY_ET, 1)
#    print 'Trend ETP =', A[0], ' mm/y'
#    TREND1 = A[0]*(YEAR-0.5) + A[1]
#    ax0.plot(YEAR-0.5, TREND1, color='green', linestyle=lstrend,
#             marker='None', label='Trend Line ETP', clip_on=False,
#             zorder=100) 

    #----------------------------------------------------------------LEGEND-----   
    
    ax0.legend(loc=2, ncol=2, numpoints=1, fontsize=14)
    
    
#===============================================================================
def plot_water_budget_monthly(YEAR, MONTH, years2plot):
#===============================================================================
    
    # 0 = DAY                 8 = CANOPY (CHANGE IN STORAGE)
    # 1 = HR                  9 = SNOW (CHANGE IN STORAGE)
    # 2 = YR                 10 = RESIDUE (CHANGE IN STORAGE)
    # 3 = PRECIP             11 = SOIL (CHANGE IN STORAGE)
    # 4 = SNOWMELT           12 = DEEP PERC
    # 5 = PRECIP INTRCP      13 = RUNOFF
    # 6 = ET                 14 = PONDED
    # 7 = PLANT TRANSP       15 = CUMUL ET
    #                        16 = ERROR'
    
#    YEAR = SIMOUT.DATE[:-1, 2].astype('int')
    
    years_index = np.where(np.in1d(YEAR, years2plot))[0]
#    years_index = np.where(YEAR == years2plot)[0]
    
#    MONTH = SIMOUT.MONTH[years_index]
    
#    RUNOFF = SIMOUT.WBudget[years_index, 13]
#    ET = SIMOUT.WBudget[years_index, 6]
    PRECIP = SIMOUT.WBudget[years_index, 3]
    RECHG = SIMOUT.WBudget[years_index, 12]
    QWSOIL = SIMOUT.QWSOIL[years_index, 13] # Water Flux @ 1.1 m

    month_names = LabelDB.month_names
    
    NYear = len(years2plot)#1. #np.max(YEAR) - np.min(YEAR)
    
    MONTH_PRECIP = np.zeros(12) 
    MONTH_RECHG = np.zeros(12) 
    MONTH_RUNOFF = np.zeros(12)
    MONTH_ET = np.zeros(12)
    MONTH_QWSOIL = np.zeros(12)
    
    for i in range(12):
        indexes = np.where(MONTH[1:] == i+1)[0]
        
        MONTH_PRECIP[i] = np.sum(PRECIP[indexes]) / NYear
        MONTH_RECHG[i] = np.sum(RECHG[indexes]) / NYear
        MONTH_RUNOFF[i] = np.sum(RUNOFF[indexes]) / NYear
        MONTH_ET[i] = np.sum(ET[indexes]) / NYear
        MONTH_QWSOIL[i] = np.sum(QWSOIL[indexes]) / NYear
        
    #----------------------------------------------------- FIGURE CREATION -----   

    fig = plt.figure(figsize=(11*0.75, 6.5*0.75))
    fig.patch.set_facecolor('white')
    
    fheight = fig.get_figheight()
    fwidth = fig.get_figwidth()
    
    left_margin  = 1
    right_margin = 0.25
    bottom_margin = 0.5
    top_margin = 0.25
    
    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w0 = 1 - (left_margin + right_margin) / fwidth
    h0 = 1 - (bottom_margin + top_margin) / fheight
   
    #------------------------------------------------------- AXES CREATION -----

    ax0  = fig.add_axes([x0, y0, w0, h0])
    ax0.patch.set_visible(False)
        
    #---------------------------------------------------- XTICKS FORMATING ----- 
    
    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x',direction='out', gridOn=False)
    ax0.xaxis.set_ticklabels([])
    ax0.set_xticks(np.arange(0, 13))
    
    ax0.set_xticks(np.arange(0.5, 12.5), minor=True)
    ax0.tick_params(axis='x', which='minor', length=0, gridOn=False)
    ax0.xaxis.set_ticklabels(month_names, minor=True)
    
    #------------------------------------------------------YTICKS FORMATING-----
    
    Ymax0 = np.max([np.max(MONTH_PRECIP), np.max(MONTH_RECHG),
                   np.max(MONTH_RUNOFF), np.max(MONTH_ET),
                   np.max(MONTH_QWSOIL)])
    Ymax0 = np.ceil(Ymax0 / 10.) * 10

    Ymin0 = 0
   
    ax0.yaxis.set_ticks_position('left')
    ax0.tick_params(axis='y',direction='out', gridOn=True)
    
    #---------------------------------------------------------- AXIS RANGE -----

    ax0.axis([0, 12, Ymin0, Ymax0])

    #----------------------------------------------------------------LABELS-----
    
    ax0.set_ylabel('Equivalent Water (mm)', fontsize=label_font_size,
                   verticalalignment='bottom')
    ax0.yaxis.set_label_coords(-0.085, 0.5)
#    
#    ax0.set_xlabel(LabelDB.years, fontsize=label_font_size,
#                   verticalalignment='top')
#    ax0.xaxis.set_label_coords(0.5, -0.075)
    
    #--------------------------------------------------------------PLOTTING-----
   
    bar_width = 0.2
    
    XPOS = np.arange(0.2, 12.2, 1)
    ax0.bar(XPOS, MONTH_PRECIP, align='center', width=bar_width,
            color='blue', label='Precipitation')
    XPOS = np.arange(0.4, 12.4, 1)
    ax0.bar(XPOS, MONTH_QWSOIL, align='center', width=bar_width,
            color='orange', label='Recharge')
    XPOS = np.arange(0.8, 12.8, 1)   
    ax0.bar(XPOS, MONTH_RUNOFF, align='center', width=bar_width,
            color='red',  label='Surface Runoff')
    XPOS = np.arange(0.6, 12.6, 1)    
    ax0.bar(XPOS, MONTH_ET, align='center', width=bar_width,
            color='green', label='Evapotranspiration') 
            
    #----------------------------------------------------------------LEGEND-----   
    
    ax0.legend(loc=1, ncol=1)

    
if __name__ == '__main__':
    
    
    dirname = '../Projects/Pont-Rouge/'
    fmeteo = dirname + 'Meteo/Output/STE CHRISTINE (7017000)_1960-2015.out'
    fwaterlvl = dirname + 'Water Levels/5080001.xls'

    synth_hydrograph = SynthHydrograph(fmeteo, fwaterlvl)
    
#    plt.close('all')
#    # fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
#    fmeteo = "Files4testing/SASKATOON INT'L A and RCS_1950-2014.out"
##    fmeteo = 'Files4testing/OUTLOOK PFRA_1980-2014.out'
#    meteoObj = MeteoObj()
#    meteoObj.load(fmeteo)
#    
#    fwaterlvl = 'Files4testing/P19 2013-2014.xls'
#    waterlvlObj = WaterlvlData()
#    waterlvlObj.load(fwaterlvl)  
#    
#    PTOT = meteoObj.PTOT # Daily total precipitation (mm)
#    TAVG = meteoObj.TAVG # Daily mean temperature (deg C)
#    TIMEmeteo = meteoObj.TIME # Time (days)
#    LAT = float(meteoObj.LAT) # Latitude (deg)
#    
#    YEAR = meteoObj.YEAR
#    MONTH = meteoObj.MONTH
#    
#    RAIN = meteoObj.RAIN
#    
#    Ta, _, _, _ = calculate_normals(YEAR, MONTH, TAVG, PTOT, RAIN) # Monthly normals
#    ETP = calculate_ETP(TIMEmeteo, TAVG, LAT, Ta) # Daily potential reference 
                                                   # evapotranspiration (mm)
    
#    RECHG = calc_recharge(0.1, 25, ETP, PTOT, TAVG)
    
    #---- OLD VERSION WITH NO UNSATURATED TRANSPORT (used for Dundurn) ----
#        
#    plt.close('all')
#    
#    # fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
#    fmeteo = "Files4testing/SASKATOON INT'L A and RCS_1950-2014.out"
##    fmeteo = 'Files4testing/OUTLOOK PFRA_1980-2014.out'
#    meteoObj = MeteoObj()
#    meteoObj.load(fmeteo)
#    
#    fwaterlvl = 'Files4testing/P19 2013-2014.xls'
#    waterlvlObj = WaterlvlData()
#    waterlvlObj.load(fwaterlvl)
#        
#    PTOT = meteoObj.PTOT # Daily total precipitation (mm)    
#    YEAR = meteoObj.YEAR

#    RAIN = meteoObj.RAIN
#    TAVG = meteoObj.TAVG # Daily mean temperature (deg C)
#    TIMEmeteo = meteoObj.TIME # Time (days)
#    LAT = float(meteoObj.LAT) # Latitude (deg)
#    MONTH = meteoObj.MONTH
    
#    Ta, _, _, _ = calculate_normals(YEAR, MONTH, TAVG, PTOT, RAIN) # Monthly normals
#    ETP = calculate_ETP(TIMEmeteo, TAVG, LAT, Ta) # Daily potential reference 
#                                                  # evapotranspiration (mm)
    
    # The program search for solutions with a long time trend that is close to
    # zero. There is no unique solution, but each solution gives mean recharge
    # rates that are equivalent and equal to the recession.
    
#    RECHG, WL = bestfit_hydrograph(meteoObj, waterlvlObj)    
##    YEAR = np.arange(1986, 2006).astype('int')       
#    plot_water_budget_yearly(PTOT, RECHG, YEAR)
#    
#    WLogger = waterlvlObj.lvl * 1000 # Observed groundwater level (mbgs)
#    TIMELogger = waterlvlObj.time  # Time (days)
#    plot_synth_hydrograph(WL, meteoObj.TIME, WLogger, TIMELogger)
#    
#    #---- Save the data in file
#    
#    filename = 'recharge_Dundurn_daily.tsv'
#    
#    # We will keep results only from 1970 to the present.
#    tindx = np.where( YEAR == 1970)[0][0]
#    
#    fileout = np.array([['Time (day)', 'Recharge (mm/day)']])
#    
#    data = np.vstack((meteoObj.TIME[tindx:], RECHG[tindx:])).transpose()
#       
#    fileout = np.vstack((fileout, data))
#    
#    
#    with open(filename, 'wb') as f:
#        writer = csv.writer(f,delimiter='\t')
#        writer.writerows(fileout)
    
    #---- Other Calculus ----
   
    # Estimation of the wilting point for plants
    
#    SoilObj = SoilTypes(10)
#    VWC, _ = calc_VWC([-164573], SoilObj)
#    print VWC
    
#    SoilObj = SoilTypes(8)
#    Pc, K = calc_Pc([0.3], SoilObj)
#    print K
