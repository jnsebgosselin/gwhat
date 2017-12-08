# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

#----  Standard library imports

import os
import csv
from calendar import monthrange
import copy
import datetime

# ---- Third party imports

import numpy as np
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple


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
    Ta[Ta < 0] = 0
    I = np.sum((0.2*Ta)**1.514)  # Heat index
    a = (6.75e-7*I**3) - (7.71e-5*I**2) + (1.7912e-2*I) + 0.49239

    inan = np.where(~np.isnan(Tavg))[0]
    N = len(Tavg)
    Tavg = copy.copy(Tavg)
    Tavg = Tavg[inan]
    Tavg[Tavg < 0] = 0

    # Calcul photoperiod in hour/day :

    DAYLEN = calcul_daylength(Date, lat)

    # Calcul reference evapotranspiration :

    PET0 = np.zeros(N) * np.nan
    PET0[inan] = 16*(10*Tavg/I)**a * (DAYLEN[inan]/(12*30))

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
        DAY365[i] = int(date.timetuple().tm_yday)

    # --------------------------------------------- DECLINATION OF THE SUN ----

    # http://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations

    N = DAY365-1

    A = 2*pi/365.24 * (N - 2)
    B = 2*pi/pi * 0.0167
    C = 2*pi/365.24 * (N + 10)

    D = -23.44 * pi/180

    SUNDEC = np.arcsin(np.sin(D) * np.cos(C + B * np.sin(A)))

    # --------------------------------------------------- SUNRISE EQUATION ----

    # http:/Omega/en.wikipedia.org/wiki/Sunrise_equation

    OMEGA = np.arccos(-np.tan(LAT) * np.tan(SUNDEC))

    # ----------------------------------------------------- HOURS OF LIGHT ----

    # http://physics.stackexchange.com/questions/28563/
    # hours-of-light-per-day-based-on-latitude-longitude-formula

    DAYLEN = OMEGA * 2 * 24 / (2 * np.pi)  # Day length in hours

    return DAYLEN
