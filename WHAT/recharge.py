# -*- coding: utf-8 -*-
"""
Copyright 2014 Jean-Sebastien Gosselin

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
    POREFF:  Effective Porosity (cm**3/cm**3)
    RSAT:    Residual Saturation (cm**3/cm**3)
    PSD:     Pore Size Distribution - Geometric mean
    BP:      Bubbling Pressure - Geometric mean (cm)
    KSAT:    Saturated Hydraulic Conductivity (cm/hr)
    
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
                        
        self.RSAT =  [0.020, 0.035, 0.041, 0.027, 0.015, 0.068, 0.075, 0.040,
                        0.109, 0.056, 0.090][indx]        
        self.RSATmax = [0.039, 0.067, 0.106, 0.074, 0.058, 0.137, 0.174,
                          0.118, 0.205, 0.136, 0.195][indx]
        self.RSATmin = [0.001, 0.003, 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        
        self.PSD = [0.592, 0.474, 0.322, 0.220, 0.211, 0.250, 0.194, 0.151,
                    0.168, 0.127, 0.131][indx]
        self.PSDmax = [1.051, 0.827, 0.558, 0.355, 0.326, 0.502, 0.377, 0.253,
                       0.364, 0.219, 0.253][indx]
        self.PSDmin = [0.334, 0.271, 0.186, 0.137, 0.136, 0.125, 0.100, 0.090,
                       0.078, 0.074, 0.068][indx]
                       
        self.BP = [7.26, 8.69, 14.66, 11.15, 20.76, 28.08, 25.89, 32.56, 29.17,
                   34.19, 37.30][indx]
        self.BPmax = [38.74, 41.85, 62.24, 76.40, 120.40, 141.50, 115.70,
                      158.7, 171.6, 166.2, 187.2][indx]
        self.BPmin = [1.36, 1.80, 3.45, 1.63, 3.58, 5.57, 5.80, 6.68, 4.96,
                      7.04, 7.43][indx]
                      
        self.KSAT = [21.00, 6.11, 2.59, 1.32, 0.68, 0.43, 0.23, 0.15, 0.12,
                     0.09, 0.06][indx]

#===============================================================================
def soil_char_curves(P, SOIL):
    # Calculate soil water content, matric potential and unsaturated hydraulic 
    # conductivity after Campbel, 1974
#===============================================================================
    
    Pe = np.mean(SIMOUT.Pe)
    PDI = np.mean(SIMOUT.PDI)
    VLCsat = np.mean(SIMOUT.VLCsat)
    Ksat = np.mean(SIMOUT.Ksat)
    VLCres = np.mean(SIMOUT.VLCres)               
   
    VLC = np.zeros(len(P)) # soil volumetric water content (m3/m3)
    K = np.zeros(len(P)) # soil unsaturated hydraulic conductivity (cm/h)
    for i in range(len(P)):
        if Pe > P[i]:
            VLC[i] = VLCres + (VLCsat - VLCres) * (Pe / P[i]) ** PDI
            K[i] = Ksat * (Pe / P[i]) ** (2 + 3*PDI)
        elif Pe <= P[i]:
            VLC[i] = VLCsat
            K[i] = Ksat
    return VLC, K
    
#===============================================================================
def calculate_recharge(TMELT, CM, CRU, RASmax, ETP, PTOT, TAVG):
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
def calculate_hydrograph(RECHG, RECESS, WLobs):
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
def bestfit_waterlvl(fmeteo, fwaterlvl):
#===============================================================================
   
    import matplotlib.pyplot as plt
    
    plt.close('all')
    
    meteoObj = MeteoObj()
    meteoObj.load(fmeteo)
    
    TAVG = meteoObj.TAVG
    TIMEmeteo = meteoObj.TIME
    LAT = float(meteoObj.LAT)
    
    ETP = calculate_ETP(TIMEmeteo, TAVG, LAT)
    
    PTOT = meteoObj.PTOT
    TAVG = meteoObj.TAVG
    
    TMELT = 0
    CM = 4 # Daily melt coefficient
#    RASmax = 100
#    CRU = 0.1
    
#    RECHG = calculate_recharge(TMELT, CM, CRU, RASmax, ETP, PTOT, TAVG)

    waterlvlObj = WaterlvlData()
    waterlvlObj.load(fwaterlvl)
    
    WLobs = waterlvlObj.lvl * 1000
    TIMEwater = waterlvlObj.time
    
#-------------------------------------------------------------------------------
    
    CRU = np.arange(0, 0.41, 0.05)
    RASmax = np.arange(0, 101, 5)
    Sy = np.ones((len(CRU), len(RASmax)))
    RMSE = np.ones((len(CRU), len(RASmax)))
    
    indx0 = np.where(TIMEmeteo <= TIMEwater[0])[0][-1]
    indxE = np.where(TIMEmeteo >= TIMEwater[-1])[0][0]
    
    # Resample observed water level on a daily basis.
    WLobs = np.interp(TIMEmeteo[indx0:indxE], TIMEwater, WLobs)

    RECESS = np.ones(len(WLobs)) * 0.69 # mm/d
    plt.plot(-WLobs)
    
    for it in range(0, len(CRU)):
        for it2 in range(0, len(RASmax)):
            RECHG = calculate_recharge(TMELT, CM, CRU[it], RASmax[it2],
                                       ETP, PTOT, TAVG)
                                    
            WLsim, Sy[it, it2] = calculate_hydrograph(
                                              RECHG[indx0:indxE], RECESS, WLobs)
            RMSE[it, it2] = (np.mean((WLsim - WLobs)**2))**0.5
            
            plt.plot(-WLsim, color=(0.75, 0.75, 0.75))
            plt.plot(-WLobs, color=(0,0,1))
            plt.pause(0.1)
            plt.pause(0.1)
            
    RMSE[np.isnan(RMSE)] = 99999
    
    best_it = np.where(RMSE == np.min(RMSE))[0][0]
    best_it2 = np.where(RMSE == np.min(RMSE))[1][0]
    
    RECHG = calculate_recharge(TMELT, CM, CRU[best_it], RASmax[best_it2],
                               ETP, PTOT, TAVG)
    WLsim, _ = calculate_hydrograph(RECHG[indx0:indxE], RECESS, WLobs)
   
    #plt.cla()                                  
    plt.plot(-WLsim, color=(1,0,0))
    print ' '
    print 'Cru = ', CRU[best_it]
    print 'RASmax = ', RASmax[best_it2]
    print 'Sy =', Sy[best_it, best_it2]
    print 'Recharge = ', sum(RECHG) / sum(PTOT) * 100, ' % de Ptot'
    
    
if __name__ == '__main__':
    
#    import matplotlib.pyplot as plt
     
#     fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
     
    fmeteo = 'Files4testing/Daily - SASKATOON DIEFENBAKER & RCS_1980-2014.out'
    fwaterlvl = 'Files4testing/P19 2013-2014.xls'
    
    bestfit_waterlvl(fmeteo, fwaterlvl)
    
    
#    print np.mean(RECHG) * 365
    
#    plt.close('all')
#    plt.figure()
#    plt.plot(ETP)
    