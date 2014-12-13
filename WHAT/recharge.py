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

#===============================================================================
def calculate_ETP(fmeteo):
#===============================================================================
    """
    Daily potential evapotranspiration (mm) is calculated with a method adapted
    from Thornwaite (1948).
    
    Requires at least a year of data.            
    """
    
    METEO = MeteoObj()
    METEO.load(fmeteo)
    
    TAVG = METEO.TAVG  # Daily temperature average
    TIME = METEO.TIME  # Time in days 
    LAT = float(METEO.LAT)  # Latitude in degrees
    
#----------------------------------------------------------- CALCULATE ETP -----
    
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
    
    
if __name__ == '__main__':
    
    import matplotlib.pyplot as plt
    
    help(calculate_ETP)
       
    fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
    fmeteo = 'Files4testing/Daily - SASKATOON DIEFENBAKER & RCS_1980-2014.out'
    
    ETP =  calculate_ETP(fmeteo)
    
    plt.close('all')
    plt.figure()
    plt.plot(ETP)
    