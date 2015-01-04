# -*- coding: utf-8 -*-
"""
Copyright 2015 Jean-Sebastien Gosselin

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

#----- THIRD PARTY IMPORTS -----

import numpy as np
from xlrd import xldate_as_tuple
import matplotlib.pyplot as plt

#----- RAINBIRD LIBRARY IMPORTS -----

from meteo import MeteoObj
from meteo import calculate_normals
from hydroprint import WaterlvlData

#===============================================================================
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
#===============================================================================
    
    def __init__(self, indx):
        
        self.TEXTURE = ['Sand', 'Loamy sand', 'Sandy loam', 'Loam', 'Silt loam'
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
    
#===============================================================================
def calc_recharge_old(CRU, RASmax, ETP, PTOT, TAVG):
#===============================================================================
    
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
    
    MP = CM * (TAVG - TMELT)  # Potential Melt
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
    
#===============================================================================
def calc_recharge(CRU, RASmax, ETP, PTOT, TAVG):
    '''
    ----- Inputs -----
    
    VWCRES = Volumetric residual water content (mm**3 / mm**3)
    VWCSAT = Volumetric saturated water content - Porosity (mm**3 / mm**3)
    HROOTS = Thickness of the root zone (mm)
    
    ----- Outputs -----
    
    HWT = Water table depth (mmbgs)
    '''
#===============================================================================
    
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
    
    #--------------------------------------------------- INITIAL CONDITIONS ----
    
    Pc = z - HWT[0]
    VWC[:, 0], Krw = calc_VWC(Pc, SoilObj)
    
    #----------------------------------------------------------- SIMULATION ----


    for i in range(10): #range(0, N-1):
        
        #--------------------------------- SURFACE STORAGE and INFILTRATION ----

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
        
        for t in  range(24):
        
            #--------------------------------------------- POTENTIAL FLUXES ----
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
        
            #------------------------------------------- SUBSURFACE ROUTING ----

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

#===============================================================================
def calculate_ETP(TIME, TAVG, LAT):
    """
    Daily potential evapotranspiration (mm) is calculated with a method adapted
    from Thornwaite (1948).
    
    Requires at least a year of data.
    
    #----- INPUT -----
    
    TIME = Numeric time in days
    TAVG = Daily temperature average (deg C)
    LAT = Latitude in degrees    
    
    #----- OUTPUT -----

    ETP: Daily Potential Evapotranspiration (mm)    
    
    #----- SOURCE -----
    
    Pereira, A.R. and W.O. Pruitt. 2004. Adaptation of the Thornthwaite scheme
        for estimating daily reference evapotranspiration. Agricultural Water
        Management, 66, 251-257.
    """
#===============================================================================
        
    Ta, _, _, _ = calculate_normals(fmeteo) # Monthly normals
    Ta[Ta < 0] = 0    
    
    I = np.sum((0.2 * Ta) ** 1.514) # Heat index
    a = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.7912e-2 * I) + 0.49239
    
    TAVG[TAVG < 0] = 0
    
    DAYLEN = calculate_daylength(TIME, LAT) # Photoperiod in hr
    
    ETP = 16 * (10 * TAVG / I)**a * (DAYLEN / (12. * 30))
        
    return ETP
    
#===============================================================================   
def calculate_daylength(TIME, LAT):
#===============================================================================
    
    pi = np.pi
    
    LAT = np.radians(LAT) # Latitude in rad
    
    #----- CONVERT DAY FORMAT -----
    
    # http://stackoverflow.com/questions/13943062
    
    DAY = np.zeros(len(TIME))
    
    for i in range(len(DAY)):
        DATE = xldate_as_tuple(TIME[i], 0)
        DAY[i] = int(date(DATE[0], DATE[1], DATE[2]).timetuple().tm_yday)
    
#-------------------------------------------------- DECLINATION OF THE SUN -----    
    
    # http://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations

    N = DAY - 1
    
    A = 2 * pi / 365.24 * (N - 2)
    B = 2 * pi / pi * 0.0167
    C = 2 * pi / 365.24 * (N + 10)
    
    D = -23.44 * pi / 180.
            
    SUNDEC = np.arcsin(np.sin(D) * np.cos(C + B * np.sin(A)))
    
#-------------------------------------------------------- SUNRISE EQUATION -----    

    # http:/Omega/en.wikipedia.org/wiki/Sunrise_equation

    OMEGA = np.arccos(-np.tan(LAT) * np.tan(SUNDEC))
    
#---------------------------------------------------------- HOURS OF LIGHT -----
    
    # http://physics.stackexchange.com/questions/28563/
    #        hours-of-light-per-day-based-on-latitude-longitude-formula
    
    DAYLEN = OMEGA * 2 * 24 / (2 * np.pi) # Day length in hours
    
    return DAYLEN
    
#===============================================================================
def calc_hydrograph_old(RECHG, RECESS, WLobs):
#===============================================================================
     
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
    
#===============================================================================
def calc_hydrograph(RECHG, RECESS, WL0, Sy):
#===============================================================================
     
    WLsim = np.zeros(len(RECHG))
    WLsim[0] = WL0
    for i in range(len(RECHG)-1):            
        WLsim[i+1] = WLsim[i] - (RECHG[i] / Sy) + RECESS[i]

    return WLsim

#=============================================================================== 
def bestfit_hydrograph(meteoObj, waterlvlObj):
#===============================================================================
   
    plt.close('all')
    
    #---- Load Meteo -----
    
    PTOT = meteoObj.PTOT # Daily total precipitation (mm)
    TAVG = meteoObj.TAVG # Daily mean temperature (deg C)
    TIMEmeteo = meteoObj.TIME # Time (days)
    LAT = float(meteoObj.LAT) # Latitude (deg)
    
    ETP = calculate_ETP(TIMEmeteo, TAVG, LAT) # Daily potential reference 
                                              # evapotranspiration (mm)
    
    print np.mean(ETP)
    
    #---- Load Waterlvl -----
    
    WLobs = waterlvlObj.lvl * 1000 # Observed groundwater level (mbgs)
    TIMEwater = waterlvlObj.time  # Time (days)
    
#----------------------------------------------------- LONG TREND ANALYSIS -----
    
#    indx0 = np.where(TIMEmeteo <= TIMEwater[0])[0][-1]
#    indxE = np.where(TIMEmeteo >= TIMEwater[-1])[0][0]
    
#    Resample observed water level on a daily basis.
#    WLobs = np.interp(TIMEmeteo[indx0:indxE], TIMEwater, WLobs)
#    plt.plot(-WLobs)

    CRU = np.arange(0, 0.41, 0.05)
    RASmax = np.zeros(len(CRU))
    RECHyr = np.zeros(len(CRU))
    
    RECESS = np.ones(len(TIMEmeteo)) * 0.69 # Water level recession (mm/d)
    WL0 = np.mean(WLobs) #Initial water level (mm)
    Sy = 0.30
    for it in range(len(CRU)):
        
        RECHG = calc_recharge_old(CRU[it], RASmax[it], ETP, PTOT, TAVG)
        WLsim = calc_hydrograph(RECHG, RECESS, WL0, Sy)
        
        SLOPEnew = np.polyfit(TIMEmeteo, WLsim, 1)[0]
        
        delta_RAS = 10
        while abs(delta_RAS) >= 0.001:
            while 1:
                SLOPEold = np.copy(SLOPEnew)
                
                RASmax[it] += delta_RAS
                
                RECHG = calc_recharge_old(CRU[it], RASmax[it], ETP, PTOT, TAVG)
                WLsim = calc_hydrograph(RECHG, RECESS, WL0, Sy)
                
                
                SLOPEnew = np.polyfit(TIMEmeteo, WLsim, 1)[0]
                
                print SLOPEnew                
                
                if np.sign(SLOPEold) != np.sign(SLOPEnew):
                    delta_RAS /= -10.
                    break
                
                if abs(SLOPEold) < abs(SLOPEnew):
                    delta_RAS *= -1
                    break
                
        RECHyr[it] = np.mean(RECHG) * 365
        print 'NEW solution'
        plt.plot(TIMEmeteo, -WLsim, color=(0.75, 0.75, 0.75))
        plt.pause(0.1)
    
    print CRU
    print RASmax  
    print RECHyr          
            
    plt.plot(TIMEwater, -WLobs, color='b')

    
if __name__ == '__main__':
    
    plt.close('all')
    # fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
    fmeteo = 'Files4testing/Daily - SASKATOON DIEFENBAKER & RCS_1980-2014.out'
    meteoObj = MeteoObj()
    meteoObj.load(fmeteo)
    
    fwaterlvl = 'Files4testing/P19 2013-2014.xls'
    waterlvlObj = WaterlvlData()
    waterlvlObj.load(fwaterlvl)
    
    PTOT = meteoObj.PTOT # Daily total precipitation (mm)
    TAVG = meteoObj.TAVG # Daily mean temperature (deg C)
    TIMEmeteo = meteoObj.TIME # Time (days)
    LAT = float(meteoObj.LAT) # Latitude (deg)
        
    ETP = calculate_ETP(TIMEmeteo, TAVG, LAT) # Daily potential reference 
                                              # evapotranspiration (mm)
    
    RECHG = calc_recharge(0.1, 25, ETP, PTOT, TAVG)
    
    #---- OLD VERSION WITH NO UNSATURATED TRANSPORT ----
    
    # The program search for solutions with a long time trend that is close to
    # zero. There is no unique solution, but each solution gives mean recharge
    # rates that are equivalent and equal to the recession.
    
#    bestfit_hydrograph(meteoObj, waterlvlObj)
    
