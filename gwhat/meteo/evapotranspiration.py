# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------


# ---- Third party imports
import numpy as np
from numpy import pi, sin, cos, arccos, arcsin
import pandas as pd


def calcul_thornthwaite(Tavg, latitude):
    """
    Calcul reference potential evapotranspiration, PET0(mm/d) with
    the method of Thornwaite (1948).

    Parameters
    ----------
    Tavg: :class:`pandas.Series`
        A pandas time series containing average daily air temperatures in
        Celcius.
    latitude: float
        The latitude in decimal degrees where we want to calculate the
        evapotranspiration.

    Returns
    -------
    PET0:
        A :class:`pandas.Series` containing the corresponding reference
        daily potential evapotranspiration values in mm/d.

    Pereira, A.R. and W.O. Pruitt. 2004. Adaptation of the Thornthwaite scheme
        for estimating daily reference evapotranspiration. Agricultural Water
        Management, 66, 251-257.
    """
    Ta = Tavg.groupby(Tavg.index.month).mean()
    Ta[Ta < 0] = 0

    I = np.sum((0.2 * Ta)**1.514)  # Heat index
    a = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.7912e-2 * I) + 0.49239

    # Calcul photoperiod in hours per day.
    day_length = calcul_daylength(Tavg.index, latitude)

    # Calcul the reference evapotranspiration.

    # Note that we need to force all negative values to zeros in the
    # average air temperature time series.
    Tavg_corr = Tavg.copy(deep=True)
    Tavg_corr[Tavg_corr < 0] = 0
    PET0 = 16 * (10 * Tavg_corr / I)**a * (day_length / (12 * 30))

    return PET0


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
