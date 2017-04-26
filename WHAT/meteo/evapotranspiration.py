# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

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

from __future__ import division, unicode_literals

# Standard library imports :

import os
import csv
from calendar import monthrange
import copy
import datetime

# Third party imports :

import numpy as np
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

# Local imports :

for i in range(2):
    try:
        from _version import __version__
        break
    except ImportError:  # to run this module standalone
        print('Running module as a standalone script...')
        import sys
        from os.path import dirname, realpath
        sys.path.append(dirname(dirname(realpath(__file__))))


# =============================================================================

def calcul_Thornthwaite(Date, Tavg, lat, Ta):
    """ Calcul reference PET0(mm/d) with  Thornwaite (1948).

    # Keyword arguments:

    {Tuple}   dates -- Contains daily time series of the year, month, and day.
    {1d array} Tavg -- Daily temperature average (deg C)
    {float}     lat -- Latitude in degrees
    {1d array}   Ta -- Monthly normals of air temperature

    # Return:

    {1d array} PET0 -- Daily Reference Potential Evapotranspiration (mm/d)

    # References:

    Pereira, A.R. and W.O. Pruitt. 2004. Adaptation of the Thornthwaite scheme
        for estimating daily reference evapotranspiration. Agricultural Water
        Management, 66, 251-257.
    """

    Ta = copy.copy(Ta)
    Tavg = copy.copy(Tavg)

    Ta[Ta < 0] = 0
    I = np.sum((0.2 * Ta) ** 1.514)  # Heat index
    a = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.7912e-2 * I) + 0.49239
    Tavg[Tavg < 0] = 0

    # Calcul photoperiod in hour/day:

    DAYLEN = calcul_daylength(Date, lat)

    PET0 = 16*(10*Tavg/I)**a * (DAYLEN/(12*30))

    return PET0


# =============================================================================
def calcul_daylength(DATE, LAT):
    """Calculate the photoperiod for the given latitude and dates

    # Keyword arguments:

    {1D array} time -- Excel numeric time in days
    {float}     lat -- latitude in decimal degrees

    # Return :

    {1D array} DAYLEN -- photoperiod in hr.
    """

    Year = copy.deepcopy(DATE[0])
    Month = copy.deepcopy(DATE[1])
    Day = copy.deepcopy(DATE[2])

    pi = np.pi
    LAT = np.radians(LAT)

    # ----- Convert date in day format -----

    # http://stackoverflow.com/questions/13943062

    N = len(Year)
    DAY365 = np.zeros(N)
    for i in range(N):
        date = datetime.date(Year[i], Month[i], Day[i])
        DAY365[i] = date.timetuple().tm_yday
        DAY365[i] = int(DAY365[i])

    # ----------------------------------------- DECLINATION OF THE SUN ----

    # http://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations

    N = DAY365-1

    A = 2*pi/365.24 * (N - 2)
    B = 2*pi/pi * 0.0167
    C = 2*pi/365.24 * (N + 10)

    D = -23.44 * pi/180

    SUNDEC = np.arcsin(np.sin(D) * np.cos(C + B * np.sin(A)))

    # ----------------------------------------------- SUNRISE EQUATION ----

    # http:/Omega/en.wikipedia.org/wiki/Sunrise_equation

    OMEGA = np.arccos(-np.tan(LAT) * np.tan(SUNDEC))

    # ------------------------------------------------- HOURS OF LIGHT ----

    # http://physics.stackexchange.com/questions/28563/
    #        hours-of-light-per-day-based-on-latitude-longitude-formula

    DAYLEN = OMEGA * 2 * 24 / (2 * np.pi)  # Day length in hours

    return DAYLEN
