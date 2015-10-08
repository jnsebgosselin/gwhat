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
from hydrograph3 import WaterlvlData

#==============================================================================
class SoilTypes():
    """
    Soil texture classes from Table 2 of Rawls et al. (1982).
    
    #----- INPUT -----
    
    indx:   0 - Sand
            1 - Loamy Sand
            2 - Sandy loam
            3 - Loam
            4 - Silt loam
            5 - Sandy clay loam
            6 - Clay loam
            7 - Silty clay loam
            8 - Sandy clay
            9 - Silty clay
           10 - Clay

    #----- OUTPUT -----
    
    TEXTURE: Texture Class Name    
    POREFF: Effective Porosity (mm**3/mm**3)
    VWCres: Volumetric residual water content (mm**3/mm**3)
    PSD: Pore Size Distribution - Geometric mean
    Pb: Pressure entry / Bubbling Pressure - Geometric mean (mm)
    Kw: Saturated Hydraulic Conductivity (mm/hr)
    
    #----- SOURCE -----
    
    Rawls, W.J., Brakensiek, D.L., and K.E. Saxton. 1982. Estimation of soil
        water properties.Transactions of the ASAE, 1316-1328.    
    """
#==============================================================================
    
    def __init__(self, indx):
        
        self.TEXTURE = ['Sand', 'Loamy sand', 'Sandy loam', 'Loam', 'Silt loam',
                        'Sandy clay loam', 'Clay loam', 'Silty clay loam',
                        'Sandy clay', 'Silty clay', 'Clay'][indx]
                         
        self.POREFF = [0.417, 0.401, 0.412, 0.434, 0.486, 0.330, 0.390, 0.432,
                       0.321, 0.423, 0.385][indx]
        self.POREFFmax = [0.480, 0.473, 0.541, 0.534, 0.578, 0.425, 0.501,
                          0.517, 0.435, 0.512, 0.501][indx]
        self.POREFFmin = [0.354, 0.329, 0.283, 0.334, 0.394, 0.235, 0.279,
                          0.347, 0.207, 0.334, 0.269][indx]
                        
        self.VWCres =  [0.020, 0.035, 0.041, 0.027, 0.015, 0.068, 0.075, 0.040,
                        0.109, 0.056, 0.090][indx]        
        self.VWCres_max = [0.039, 0.067, 0.106, 0.074, 0.058, 0.137, 0.174,
                          0.118, 0.205, 0.136, 0.195][indx]
        self.VWCres_min = [0.001, 0.003, 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        
        self.PSD = [0.592, 0.474, 0.322, 0.220, 0.211, 0.250, 0.194, 0.151,
                    0.168, 0.127, 0.131][indx]
        self.PSDmax = [1.051, 0.827, 0.558, 0.355, 0.326, 0.502, 0.377, 0.253,
                       0.364, 0.219, 0.253][indx]
        self.PSDmin = [0.334, 0.271, 0.186, 0.137, 0.136, 0.125, 0.100, 0.090,
                       0.078, 0.074, 0.068][indx]
                       
        self.Pb = -1 * [72.6, 86.9, 146.6, 111.5, 207.6, 280.8, 258.9, 325.6,
                        291.7, 341.9, 373.0][indx]
        self.Pb_max = [387.4, 418.5, 622.4, 764.0, 1204.0, 1415.0, 1157.0,
                       1587., 1716., 1662., 1872.][indx] * -1
        self.Pb_min = [13.6, 18.0, 34.5, 16.3, 35.8, 55.7, 58.0, 66.8, 49.6,
                       70.4, 74.3][indx] * -1
                      
        self.Kw = [210.0, 61.1, 25.9, 13.2, 6.8, 4.3, 2.3, 1.5, 1.2,
                   0.9, 0.6][indx]

#===============================================================================
def calc_Pc(VWC, SoilObj):
    '''
    Calculate soil matric potential and unsaturated hydraulic conductivity 
    from the water content after Brooks and Corey, 1964
    
    ----- Inputs -----
    
    VWC: Volumetric Water Content (mm**3/mm**3)
    
    PSD: Pore Size Distribution
    Kw: Saturated Hydraulic Conductivity for water (mm/hr)
    Pb: Pressure entry / Bubbling Pressure - Geometric mean (mm)
    Pc: Capillary pressure (mm)
    VWCres: Volumetric residual water content (cm**3/cm**3)
    
    ----- Outputs -----
    
    Pc: Capillary pressure (mm)
    Krw: Soil unsaturated hydraulic conductivity (mm/hr)
    '''
#===============================================================================
    
    N = len(VWC)
    
    #----- Soil Properties -----
    
    PSD = SoilObj.PSD
    Kw = SoilObj.Kw
    VWCsat = SoilObj.POREFF
    VWCres = SoilObj.VWCres
    Pb = SoilObj.Pb
    
    Pc = np.zeros(N)
    Krw = np.zeros(N)
    
    for i in range(N):
        if VWC[i] >= VWCsat:
            Pc[i] = Pb
            Krw[i] = Kw
        else:
            Se = (VWC[i] - VWCres) / (VWCsat - VWCres)
            Pc[i] = Pb / Se**(1/PSD)
            Krw[i] = Se**(2/PSD + 3)
            
    return Pc, Krw
    
#===============================================================================
def calc_VWC(Pc, SoilObj):
    '''
    Calculate soil water content and unsaturated hydraulic conductivity 
    from matric potential after Brooks and Corey, 1964
    
    ----- Inputs -----
    
    Pc: Capillary pressure (mm)
    
    PSD: Pore Size Distribution
    Kw: Saturated Hydraulic Conductivity for water (mm/hr)
    Pb: Pressure entry / Bubbling Pressure - Geometric mean (mm)
    Pc: Capillary pressure (mm)
    VWCres: Volumetric residual water content (cm**3/cm**3)
    
    ----- Outputs -----
    
    VWC: Volumetric Water Content (mm**3/mm**3)  
    Krw: Soil unsaturated hydraulic conductivity (mm/hr)
    '''
#===============================================================================
    
    N = len(Pc)
    
    #----- Soil Properties -----
    
    PSD = SoilObj.PSD
    Kw = SoilObj.Kw
    VWCsat = SoilObj.POREFF
    VWCres = SoilObj.VWCres
    Pb = SoilObj.Pb
    
    VWC = np.zeros(N)
    Krw = np.zeros(N)
    
    for i in range(N):
        if Pc[i] < Pb:
            VWC[i] = VWCres + (VWCsat - VWCres) * (Pb / Pc[i]) ** PSD
            Krw[i] = Kw * (Pb / Pc[i]) ** (2 + 3*PSD)
        else:
            VWC[i] = VWCsat
            Krw[i] = Kw
            
    return VWC, Krw
    
#===============================================================================
def plot_P_vs_VWC(Pc, VWC, VWCsat, VWCres):
    """
    Plot Volumetric Water Content(VWC) vs. Soil Matric Potential (Pc)
    
    Pc = Capillary pressure (m)
    
    """
#===============================================================================
    
    fig1 = plt.figure(figsize=(5, 6))
    fig1.patch.set_facecolor('white')
    
    fheight = fig1.get_figheight()
    fwidth = fig1.get_figwidth()
               
    left_margin  = 0.85
    right_margin = 0.25
    bottom_margin = 0.75
    top_margin = 0.25
    
    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w = 1 - (left_margin + right_margin) / fwidth
    h = 1 - (bottom_margin + top_margin) / fheight
    
    ax1  = fig1.add_axes([x0, y0, w, h], zorder=1)
    
    xticks_position = np.arange(0, 1, 0.1)
    
    ax1.set_xticks(xticks_position)
    ax1.xaxis.set_ticks_position('bottom')
    ax1.tick_params(axis='both',direction='out', gridOn=True)
    
    xticks_minor_position = np.arange(0, 1, 0.02)
    ax1.set_xticks(xticks_minor_position, minor=True)
    ax1.tick_params(axis='x', which='minor', direction='out', gridOn=False)
    
    yticks_position = np.arange(0, 3)
    ax1.set_yticks(yticks_position)
    ax1.yaxis.set_ticks_position('left')
    
    yticks_minor_position = np.arange(0, 3, 0.1)
    ax1.set_yticks(yticks_minor_position, minor=True)
    ax1.tick_params(axis='y', which='minor', direction='out', gridOn=False)
    
    ax1.axis([0, 0.5, 0.01, 100])
    
    ax1.set_yscale('log')
    
    ax1.set_ylabel(u'Soil matric potential, ψ (m)', fontsize=12,
                   verticalalignment='bottom')
    ax1.set_xlabel(u'Soil volumetric water content, θ (m³/m³)', fontsize=12,
                   verticalalignment='top')
                
    ax1.plot(VWC, Pc, '-')
    ax1.plot([VWCres, VWCres], [0.001, 1000], '--', color='blue')
    ax1.plot([VWCsat, VWCsat], [0.001, 1000], '--', color='blue')
    

    
#==============================================================================
def calc_recharge(CRU, RASmax, ETP, PTOT, TAVG):
    '''
    In this version, I tried to incorporate the flow of water in the
    unsaturated zone with a subrouting approach similar to HELP. It does not
    work yet.
    
    ----- Inputs -----
    
    VWCRES = Volumetric residual water content (mm**3 / mm**3)
    VWCSAT = Volumetric saturated water content - Porosity (mm**3 / mm**3)
    HROOTS = Thickness of the root zone (mm)
    
    ----- Outputs -----
    
    HWT = Water table depth (mmbgs)
    '''
#==============================================================================
    
    N = len(ETP)    
    PAVL = np.zeros(N)    # Available Precipitation
    PACC = np.zeros(N)    # Accumulated Precipitation
    RU = np.zeros(N)      # Runoff
    I = np.zeros(N)       # Infiltration
    ETR = np.zeros(N)     # Evapotranspiration Real
    dRAS = np.zeros(N)    # Variation of RAW
    RAS = np.zeros(N)     # Readily Available Storage
    RECHG = np.zeros(N-1) # Recharge (mm)
    HWT = np.zeros(N)
        
    #---- Soil Properties ----
    
    SoilObj = SoilTypes(0)
    VWCres = SoilObj.VWCres
    VWCsat = SoilObj.POREFF
    # Sy = VWCsat - VWCres
    # HROOTS = 300
    
#    Pc = -np.arange(0, 6000)
#    VWC, _ = calc_VWC(Pc, SoilObj)
    
#    plot_P_vs_VWC(-Pc/1000., VWC, VWCsat, VWCres)
    
    #---- Snow Melt ----
    
    TMELT = 0 # Temperature treshold for snowmelt
    CM = 4 # Daily melt coefficient
    
    MP = CM * (TAVG - TMELT)  # Potential Melt
    MP[MP < 0] = 0
    
    PACC[0] = 0
    RAS[0] = RASmax

    #-------------------------------------------------------- MESH CREATION ----
    
    HWT[0] = 6400
    
    # First layer thickness is equal to that of the root zone
    z = np.array([150, 650, 1150, 1650, 2150, 2650, 3150, 3650, 4150, 4650,
                  5150, 5650, 6150])
                  
    dz = z[1:] - z[:-1]
    dt = 1
                  
    nz = len(z)
    nt = len(ETP)
    
    VWC = np.zeros((nz, nt))
    
    #---------------------------------------------------- INITIAL CONDITIONS --
    
    Pc = z - HWT[0]
    VWC[:, 0], Krw = calc_VWC(Pc, SoilObj)
    
    #------------------------------------------------------------ SIMULATION --


    for i in range(10): #range(0, N-1):
        
        #---------------------------------- SURFACE STORAGE and INFILTRATION --

        #---- Precipitation and Snowmelt ----          

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
            
        #---- Infiltration and Runoff ----
        
        RU[i] = CRU * PAVL[i]
        PI = PAVL[i] - RU[i] # Potential Infiltration
        
        PI = 25
        
        #---- ETR, Recharge and Storage change ----
        
        # dRAS[i] = min(I[i], RASmax - RAS[i])
        # RAS[i+1] = RAS[i] + dRAS[i] #intermediate step
        # RECHG[i] = I[i] - dRAS[i]
        
        # ETR[i] = min(ETP[i], RAS[i])
        
        # RAS[i+1] = RAS[i+1] - ETR[i]
        
        VWCt = VWC[:, i]
        VWCdt = VWC[:, i]
        
        for t in range(24):
        
            #---------------------------------------------- POTENTIAL FLUXES --
#            print VWCt[0] 
            Pc, Krw = calc_Pc(VWCt, SoilObj)
            print '%0.2f, %0.2f, %0.2f, %0.2f' % (VWCt[0] , Krw[0], VWCt[1], Krw[1])
        
            dhw = ((Pc[1:] - Pc[:-1]) / dz) - 1  # vertical hydraulic gradient (mm)
        
#            qw = -(Krw[:-1] * Krw[1:])**0.5 * dhw  # vertical water flux (mm/hr)
            qw = -0.5*(Krw[:-1] + Krw[1:]) * dhw # vertical water flux (mm/hr)
        
            Krw1 = (Krw[0] * Krw[1])**0.5
            Krw2 = 0.5*(Krw[0] + Krw[1])
            _, Krw3 = calc_Pc([0.5*(VWCt[0]+VWCt[1])], SoilObj)
            
#            print Krw[0], Krw1, Krw2, Krw3[0]                     
        
            #---- SUP LIMIT ----
            VWCdt[0] = (PI/24. - qw[0]) / (2 * dz[0]) / VWCsat * dt + VWCt[0]

            #---- INNER CELLS ----     
            VWCdt[1:-1] = (qw[:-1] - qw[1:]) / (dz[1:]/2.+dz[:-1]/2.) / VWCsat * dt + VWCt[1:-1]
        
            #---- LOWER LIMIT ----        
            VWCdt[-1] = qw[-1] / (2 * dz[-1]) / VWCsat * dt + VWCt[-1]
            
            for j in range(len(VWCdt)):
                
                if VWCdt[j] < VWCres:
    #                print 'PATATE'
                    VWCdt[j] = VWCres
                elif VWCdt[j] > VWCsat:
    #                print 'Orange'
                    VWCdt[j] = VWCsat
       
        VWC[:, i+1]=  VWCdt
        
            #-------------------------------------------- SUBSURFACE ROUTING --

#            for j in range(len(z)):
#                
#                if VWC[j, i+1] < VWCres:
#    #                print 'PATATE'
#                    VWC[j, i+1] = VWCres
#                elif VWC[j, i+1] > VWCsat:
#    #                print 'Orange'
#                    VWC[j, i+1] = VWCsat
        
    #        #Residual water taking into account water table position
    #        VWCres_z, _ = calc_VWC(z - HWT[0], SoilObj)
                
#    print VWC[:, :8]
#        print dhw
    #        print Krw
    #        print Pc[1] - Pc[0]
    #        print (Krw[0] * Krw[1])**0.5
    #        print VWC[:, i+1]
#        print qw[0]
        
    plt.figure()            
    plt.plot(VWC[:, :i+1])
    
    #        qw_pot =  
    
    
    #            qw = Krw[] *     
            
    
    return RECHG
    
#==============================================================================
def calc_hydrograph_old(RECHG, RECESS, WLobs):
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
def surf_water_budget(CRU, RASmax, ETP, PTOT, TAVG):
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
#==============================================================================
    
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
    
def calc_hydrograph(RECHG, A, B, WL0, Sy): #===================================
    
    """
    Parameters
    ----------
    Wlpre: Predicted Water Level (mm)
    Sy: Specific Yield
    RECHG: Groundwater Recharge (mm)
    
    A, B: MRC Parameters, where: Recess(mm/d) = -A * h + B    
    """

    # This is a backward numerical explicit scheme. This was used to do the
    # interpretation of the hydrograph at Dundurn. I need to find where I've
    # documented this.
    #
    # It should also be possible to do a Crank-Nicholson on this. I should
    # check this out.
    
    WLpre = np.zeros(len(RECHG))
    WLpre[-1] = WL0
    for i in reversed(range(len(RECHG))):
        RECESS = (B - A * WLpre[i]) * 1000        
        WLpre[i-1] = WLpre[i] + (RECHG[i] / Sy) - RECESS[i]

    return WLsim

#==============================================================================

class BestFitHydrograph(object):
    
#==============================================================================
    
    def __init__(self, fmeteo, fwaterlvl):
    
    #---- Load Data ----
    
    self.meteoObj = MeteoObj()
    self.meteoObj.load(fmeteo)
    
    self.waterlvlObj = WaterlvlData()
    self.waterlvlObj.load(fwaterlvl)
    
    #---- Assign Variables ----
    
    PTOT = meteoObj.PTOT # Daily total precipitation (mm)    
    YEAR = meteoObj.YEAR
    
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
        
    plt.close('all')
    
    # fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
    fmeteo = "Files4testing/SASKATOON INT'L A and RCS_1950-2014.out"
#    fmeteo = 'Files4testing/OUTLOOK PFRA_1980-2014.out'
    meteoObj = MeteoObj()
    meteoObj.load(fmeteo)
    
    fwaterlvl = 'Files4testing/P19 2013-2014.xls'
    waterlvlObj = WaterlvlData()
    waterlvlObj.load(fwaterlvl)
        
    PTOT = meteoObj.PTOT # Daily total precipitation (mm)    
    YEAR = meteoObj.YEAR

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
    
    RECHG, WL = bestfit_hydrograph(meteoObj, waterlvlObj)    
#    YEAR = np.arange(1986, 2006).astype('int')       
    plot_water_budget_yearly(PTOT, RECHG, YEAR)
    
    WLogger = waterlvlObj.lvl * 1000 # Observed groundwater level (mbgs)
    TIMELogger = waterlvlObj.time  # Time (days)
    plot_synth_hydrograph(WL, meteoObj.TIME, WLogger, TIMELogger)
    
    #---- Save the data in file
    
    filename = 'recharge_Dundurn_daily.tsv'
    
    # We will keep results only from 1970 to the present.
    tindx = np.where( YEAR == 1970)[0][0]
    
    fileout = np.array([['Time (day)', 'Recharge (mm/day)']])
    
    data = np.vstack((meteoObj.TIME[tindx:], RECHG[tindx:])).transpose()
       
    fileout = np.vstack((fileout, data))
    
    
    with open(filename, 'wb') as f:
        writer = csv.writer(f,delimiter='\t')
        writer.writerows(fileout)
    
    #---- Other Calculus ----
   
    # Estimation of the wilting point for plants
    
#    SoilObj = SoilTypes(10)
#    VWC, _ = calc_VWC([-164573], SoilObj)
#    print VWC
    
#    SoilObj = SoilTypes(8)
#    Pc, K = calc_Pc([0.3], SoilObj)
#    print K
