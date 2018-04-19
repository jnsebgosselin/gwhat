# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Standard library imports

from calendar import monthrange
from collections.abc import Mapping
from abc import abstractmethod


# ---- Third parties imports

import numpy as np
from xlrd import xldate_as_tuple


class GLUEDataFrameBase(Mapping):
    """
    A base class storing GLUE results.
    """
    GLUE_LIMITS = [0.05, 0.25, 0.5, 0.75, 0.95]

    def __init__(self, *args, **kwargs):
        super(GLUEDataFrameBase, self).__init__(*args, **kwargs)
        self.store = None

    @abstractmethod
    def __load_data__(self, data):
        """Load glue data and save it in a store."""
        pass


class GLUEDataFrame(GLUEDataFrameBase):
    """
    A class for calculating GLUE from a set of behavioural models and to store
    the results in a standardized way.
    """
    def __init__(self, data, *args, **kwargs):
        super(GLUEDataFrame, self).__init__(*args, **kwargs)
        self.__load_data__(data)

    def __getitem__(self, key):
        """Return the value saved in the store at key."""
        return self.store.__getitem__(key)

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __iter__(self):
        return self.store.__iter__()

    def __len__(self):
        return self.store.__len__()

    def __load_data__(self, data):
        """
        Take the results of a set of behavioural models, calculate the GLUE
        results for the typical confidence intervals and save the results in
        the store.
        """
        self.store = {}

        # Store the model distribution info.
        self.store['count'] = data['count']
        self.store['RMSE'] = data['RMSE']
        self.store['params'] = data['params']
        self.store['ranges'] = data['ranges']

        # Store the piezometric and weather stations info.
        self.store['wlinfo'] = data['wlinfo']
        self.store['wxinfo'] = data['wxinfo']

        # Store the Master Recession Curve parameters and simulated values.
        self.store['mrc'] = data['mrc']

        # Calcul daily, monthly, and yearly GLUE values of all the computed
        # components of the water budget.
        self.store['daily budget'] = calcul_dly_budget(
            data, [0.05, 0.25, 0.5, 0.75, 0.95])
        self.store['monthly budget'] = calcul_mly_budget(
            self.store['daily budget'])
        self.store['yearly budget'] = calcul_yrly_budget(
            self.store['monthly budget'])
        self.store['hydrol yearly budget'] = calcul_hydro_yrly_budget(
            self.store['daily budget'])

        # Calcul daily GLUE values for the water levels and store the results
        # along with the oberved values.
        grp = self.store['water levels'] = {}
        grp['time'] = data['water levels']['time']
        grp['date'] = data['water levels']['date']
        grp['observed'] = data['water levels']['observed']
        grp['GLUE limits'] = [0.05, 0.5, 0.95]
        grp['predicted'] = calcul_glue(
            data, grp['GLUE limits'], varname='hydrograph')


def calcul_glue(data, glue_limits, varname='recharge'):
    """
    Calcul recharge for the provided GLUE uncertainty limits from a set of
    behavioural models.
    """
    if varname not in ['recharge', 'etr', 'ru', 'hydrograph']:
        raise ValueError("varname value must be",
                         ['recharge', 'etr', 'ru', 'hydrograph'])
    x = np.array(data[varname])
    _, n = np.shape(x)

    rmse = np.array(data['RMSE'])
    # Rescale the RMSE so the sum of all values equal 1.
    rmse = rmse/np.sum(rmse)

    glue = np.zeros((n, len(glue_limits)))
    for i in range(n):
        # Sort predicted values.
        isort = np.argsort(x[:, i])
        # Compute the Cumulative Density Function.
        cdf = np.cumsum(rmse[isort])
        # Get GLUE values for the p confidence intervals.
        glue[i, :] = np.interp(glue_limits, cdf, x[isort, i])

    return glue


def calcul_dly_budget(data, glue_limits):
    """
    Calcul GLUE daily water budget for the provided GLUE uncertainty limits.
    """
    times = np.array(data['Time']).astype(float)
    years = np.array(data['Year']).astype(int)
    months = np.array(data['Month']).astype(int)
    days = np.array(data['Day']).astype(int)

    glue_rechg_dly = calcul_glue(data, glue_limits, varname='recharge')
    glue_evapo_dly = calcul_glue(data, glue_limits, varname='etr')
    glue_runof_dly = calcul_glue(data, glue_limits, varname='ru')
    precip_dly = data['Weather']['Ptot']

    deltat = int(data['params']['deltat'])
    if deltat > 0:
        # We pad data with zeros at the beginning of the recharge array and
        # at the end of the evapotranspiration and runoff array to take into
        # account the time delta that represents the percolation time of
        # water through the unsaturated zone.
        zeros_pad = np.zeros((deltat, len(glue_limits)))
        glue_rechg_dly = np.vstack([zeros_pad, glue_rechg_dly])
        glue_evapo_dly = np.vstack([glue_evapo_dly, zeros_pad])
        glue_runof_dly = np.vstack([glue_runof_dly, zeros_pad])
        precip_dly = np.hstack([precip_dly, np.zeros(deltat)])

        # We extend the time and date arrays.
        times2add = np.arange(deltat) + times[-1] + 1
        years2add = []
        months2add = []
        days2add = []
        for time_ in times2add:
            date = xldate_as_tuple(time_, 0)
            years2add.append(date[0])
            months2add.append(date[1])
            days2add.append(date[2])
        times = np.hstack([times, times2add])
        years = np.hstack([years, years2add])
        months = np.hstack([months, months2add])

    return {'recharge': glue_rechg_dly,
            'evapo': glue_evapo_dly,
            'runoff': glue_runof_dly,
            'precip': precip_dly,
            'time': times,
            'years': years,
            'months': months,
            'days': days,
            'GLUE limits': glue_limits}


def calcul_mly_budget(glue_dly):
    """
    Calcul the water budget monthly values from the water budget daily values
    calculated with the GLUE method from a set of behavioural models for a
    given set of p confidence intervals.
    """
    years = glue_dly['years']
    months = glue_dly['months']

    year_range = np.unique(years)
    month_range = range(1, 13)

    # Initialize a dict where the results will be saved.
    glue_mly = {'years': year_range,
                'GLUE limits': glue_dly['GLUE limits']}
    for var in ['recharge', 'evapo', 'runoff']:
        glue_mly[var] = np.zeros(
            (len(year_range), 12, len(glue_dly['GLUE limits']))) * np.nan
    glue_mly['precip'] = np.zeros((len(year_range), 12)) * np.nan

    # Compute monthly values from daily time series.
    for i, year in enumerate(year_range):
        for j, month in enumerate(month_range):
            indexes = np.where((years == year) & (months == month))[0]
            if len(indexes) < monthrange(year, month)[1]:
                # This month is not complete, so we keep its value a nan.
                continue
            for var in ['recharge', 'evapo', 'runoff']:
                glue_mly[var][i, j, :] = np.sum(
                    glue_dly[var][indexes, :], axis=0)
            glue_mly['precip'][i, j] = np.sum(glue_dly['precip'][indexes])

    return glue_mly


def calcul_yrly_budget(glue_mly):
    """
    Calcul yearly water budget components from montly values calculated
    with the GLUE method from a set of behavioural models for a
    given set of p confidence intervals.
    """
    # Initialize a dict where the results will be saved.
    glue_yrly = {'years': glue_mly['years'],
                 'GLUE limits': glue_mly['GLUE limits']}
    for var in ['recharge', 'evapo', 'runoff', 'precip']:
        glue_yrly[var] = np.sum(glue_mly[var], axis=1)

    return glue_yrly


def calcul_hydro_yrly_budget(glue_dly):
    """
    Calcul the water budget values for hydrological years from the
    water budget daily values calculated with the GLUE method from a set of
    behavioural models for a given set of p confidence intervals.
    An hydrological year is defined from October 1 to September 30 of the
    next year.
    """
    years = glue_dly['years']
    months = glue_dly['months']
    glue_rechg_dly = glue_dly['recharge']
    glue_evapo_dly = glue_dly['evapo']
    glue_runof_dly = glue_dly['runoff']
    precip_dly = glue_dly['precip']

    # Define the range of the years for which yearly values of the water
    # budget components will be computed.

    year_range = np.arange(np.min(years), np.max(years)).astype('int')

    # Convert daily to hydrological year. An hydrological year is defined from
    # October 1 to September 30 of the next year.

    nyear, nlim = len(year_range), len(glue_dly['GLUE limits'])
    glue_rechg_yly = np.zeros((nyear, nlim))
    glue_evapo_yly = np.zeros((nyear, nlim))
    glue_runof_yly = np.zeros((nyear, nlim))
    precip_yly = np.zeros(nyear)
    for i in range(nyear):
        yr0 = year_range[i]
        yr1 = yr0 + 1

        indexes = np.where((years == yr0) & (months == 10))[0]
        indx0 = 0 if len(indexes) == 0 else indexes[0]

        indexes = np.where((years == yr1) & (months == 9))[0]
        indx1 = len(years-1) if len(indexes) == 0 else indexes[-1]

        glue_rechg_yly[i, :] = np.sum(glue_rechg_dly[indx0:indx1+1, :], axis=0)
        glue_evapo_yly[i, :] = np.sum(glue_evapo_dly[indx0:indx1+1, :], axis=0)
        glue_runof_yly[i, :] = np.sum(glue_runof_dly[indx0:indx1+1, :], axis=0)
        precip_yly[i] = np.sum(precip_dly[indx0:indx1+1])

    return {'years': year_range,
            'recharge': glue_rechg_yly,
            'evapo': glue_evapo_yly,
            'runoff': glue_runof_yly,
            'precip': precip_yly,
            'GLUE limits': glue_dly['GLUE limits']}


if __name__ == '__main__':
    from gwhat.gwrecharge.gwrecharge_calc2 import load_glue_from_npy

    GLUE_DATA = load_glue_from_npy('glue_rawdata.npy')
    GLUE_DSET = GLUEDataFrame(GLUE_DATA)
