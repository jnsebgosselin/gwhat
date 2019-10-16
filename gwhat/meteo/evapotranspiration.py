# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
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
from numpy import pi, sin, cos, arccos, arcsin
import pandas as pd
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
    

def calcul_daylength(dtimes, latitude):
    """Calculate the photoperiod for the given latitude and dates

    Parameters
    ----------
    dtimes: :class:`pandas.DatetimeIndex`
        A :class:`pandas.DatetimeIndex` containing a series of dates for which
        we want to calculate the photoperiod for the specified latitude.
    latitude: float
        The latitude in decimal degrees where we want to calculate the
        photoperiod for the specified dates.

    Returns
    -------
    daylength:
        A :class:`pandas.DatetimeIndex` containing the photoperiod for the
        specified dates and latitude.
    """
    latitude = np.radians(latitude)

    # Calculate sun declination.
    # http://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations

    # N is the number of days since midnight UT as January 1 begins (
    # i.e. the days part of the ordinal date −1)
    N = dtimes.dayofyear.values - 1
    A = 2 * pi / 365.24 * (N - 2)
    B = 2 * pi / pi * 0.0167
    C = 2 * pi / 365.24 * (N + 10)
    D = -23.44 * pi / 180
    sun_declination = arcsin(sin(D) * cos(C + B * sin(A)))

    # Solve the sunrise equation.
    # https://en.wikipedia.org/wiki/Sunrise_equation

    # We take the equation that take into account corrections for
    # astronomical refraction and solar disc diameter.
    num = sin(-0.83 * pi / 180) - sin(latitude) * sin(sun_declination)
    denum = cos(latitude) * cos(sun_declination)
    hour_angle = arccos(num / denum)

    daylen = 2 * hour_angle * 24 / (2 * pi)

    return pd.Series(daylen, index=dtimes)


if __name__ == '__main__':
    dtimes = pd.DatetimeIndex([
        '2019-01-01', '2019-02-01', '2019-03-01', '2019-04-01',
        '2019-05-01', '2019-06-01', '2019-07-01', '2019-08-01',
        '2019-09-01', '2019-10-01', '2019-11-01', '2019-12-01'])
    daylength = calcul_daylength(dtimes, 46.82).to_frame('calculated')
    daylength['expected'] = np.array([8.62, 9.64, 11.09, 12.82, 14.41, 15.61,
                                      15.80, 14.88, 13.35, 11.70, 10.04, 8.83])
    print(daylength)

    # The expected day lenghts were calculated for the city of Quebec
    # (latitude=46.82 ddec) with a tool available on the Government of
    # Canada website at:
    # https://www.nrc-cnrc.gc.ca/eng/services/sunrise/index.html
