# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).

GWHAT is free software: you can redistribute it and/or modify
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

# ---- Standard library imports

import os
import csv
from calendar import monthrange
from copy import copy

# ---- Third party imports

import numpy as np
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

# ---- Local imports

from gwhat.meteo.evapotranspiration import calcul_Thornthwaite


class WXDataFrame(dict):
    def __init__(self, filename, *args, **kwargs):
        super(WXDataFrame, self).__init__(*args, **kwargs)

        self['filename'] = filename
        self['Station Name'] = ''
        self['Latitude'] = 0
        self['Longitude'] = 0
        self['Province'] = ''
        self['Elevation'] = 0
        self['Climate Identifier'] = ''

        self['Year'] = np.array([])
        self['Month'] = np.array([])
        self['Day'] = np.array([])
        self['Time'] = np.array([])

        self['Missing Tmax'] = []
        self['Missing Tmin'] = []
        self['Missing Tavg'] = []
        self['Missing Ptot'] = []

        self['Tmax'] = np.array([])
        self['Tavg'] = np.array([])
        self['Tmin'] = np.array([])
        self['Ptot'] = np.array([])
        self['Rain'] = None
        self['Snow'] = None
        self['PET'] = None

        self['monthly'] = {'Year': np.array([]),
                           'Month': np.array([]),
                           'Tmax': np.array([]),
                           'Tmin': np.array([]),
                           'Tavg': np.array([]),
                           'Ptot': np.array([]),
                           'Rain': None,
                           'Snow': None,
                           'PET': None}

        self['yearly'] = {'Year': np.array([]),
                          'Tmax': np.array([]),
                          'Tmin': np.array([]),
                          'Tavg': np.array([]),
                          'Ptot': np.array([]),
                          'Rain': None,
                          'Snow': None,
                          'PET': None}

        self['normals'] = {'Tmax': np.array([]),
                           'Tmin': np.array([]),
                           'Tavg': np.array([]),
                           'Ptot': np.array([]),
                           'Rain': None,
                           'Snow': None,
                           'PET': None}

        # -------------------------------------------- Import primary data ----

        data = read_weather_datafile(filename)
        for key in data.keys():
            self[key] = data[key]

        # ------------------------------------------------- Import missing ----

        finfo = filename[:-3] + 'log'
        if os.path.exists(finfo):
            self['Missing Tmax'] = load_weather_log(finfo, 'Max Temp (deg C)')
            self['Missing Tmin'] = load_weather_log(finfo, 'Min Temp (deg C)')
            self['Missing Tavg'] = load_weather_log(finfo, 'Mean Temp (deg C)')
            self['Missing Ptot'] = load_weather_log(finfo, 'Total Precip (mm)')

        # ---------------------------------------------------- format data ----

        print('Make daily time series continuous.')

        time = copy(self['Time'])
        date = [copy(self['Year']), copy(self['Month']), copy(self['Day'])]
        vbrs = ['Tmax', 'Tavg', 'Tmin', 'Ptot', 'Rain', 'PET']
        data = [self[x] for x in vbrs]

        time, date, data = make_timeserie_continuous(self['Time'], date, data)
        self['Time'] = time
        self['Year'], self['Month'], self['Day'] = date[0], date[1], date[2]
        for i, vbr in enumerate(vbrs):
            self[vbr] = data[i]

        print('Fill missing with estimated values.')

        for vbr in ['Tmax', 'Tavg', 'Tmin', 'PET']:
            self[vbr] = fill_nan(self['Time'], self[vbr], vbr, 'interp')

        for vbr in ['Ptot', 'Rain', 'Snow']:
            self[vbr] = fill_nan(self['Time'], self[vbr], vbr, 'zeros')

        # ---------------------------------------------- monthly & normals ----

        # Temperature based variables:

        for vrb in ['Tmax', 'Tmin', 'Tavg']:
            x = calc_yearly_mean(self['Year'], self[vrb])
            self['yearly'][vrb] = x[1]

            x = calc_monthly_mean(self['Year'], self['Month'], self[vrb])
            self['monthly'][vrb] = x[2]

            self['normals'][vrb] = calcul_monthly_normals(x[1], x[2])

        # Precipitation :

        x = calc_yearly_sum(self['Year'], self['Ptot'])
        self['yearly']['Ptot'] = x[1]
        self['yearly']['Year'] = x[0]

        x = calc_monthly_sum(self['Year'], self['Month'], self['Ptot'])
        self['monthly']['Ptot'] = x[2]
        self['monthly']['Year'] = x[0]
        self['monthly']['Month'] = x[1]

        self['normals']['Ptot'] = calcul_monthly_normals(x[1], x[2])

        # ------------------------------------------------- secondary vrbs ----

        # ---- Rain ----

        if self['Rain'] is None:
            self['Rain'] = calcul_rain_from_ptot(
                    self['Tavg'], self['Ptot'], Tcrit=0)
            print('Rain estimated from Ptot.')

        x = calc_yearly_sum(self['Year'], self['Rain'])
        self['yearly']['Rain'] = x[1]

        x = calc_monthly_sum(self['Year'], self['Month'], self['Rain'])
        self['monthly']['Rain'] = x[2]

        self['normals']['Rain'] = calcul_monthly_normals(x[1], x[2])

        # ---- Snow ----

        if self['Snow'] is None:
            self['Snow'] = self['Ptot'] - self['Rain']
            print('Snow estimated from Ptot.')

        x = calc_yearly_sum(self['Year'], self['Snow'])
        self['yearly']['Snow'] = x[1]

        x = calc_monthly_sum(self['Year'], self['Month'], self['Snow'])
        self['monthly']['Snow'] = x[2]

        self['normals']['Snow'] = calcul_monthly_normals(x[1], x[2])

        # ---- Potential Evapotranspiration ----

        if self['PET'] is None:
            dates = [self['Year'], self['Month'], self['Day']]
            Tavg = self['Tavg']
            lat = self['Latitude']
            Ta = self['normals']['Tavg']
            self['PET'] = calcul_Thornthwaite(dates, Tavg, lat, Ta)
            print('Potential evapotranspiration evaluated with Thornthwaite.')

        x = calc_yearly_sum(self['Year'], self['PET'])
        self['yearly']['PET'] = x[1]

        x = calc_monthly_sum(self['Year'], self['Month'], self['PET'])
        self['monthly']['PET'] = x[2]

        self['normals']['PET'] = calcul_monthly_normals(x[1], x[2])

        print('-'*78)

    def __getitem__(self, key):
        if key == 'daily':
            vrbs = ['Year', 'Month', 'Day', 'Tmin', 'Tavg', 'Tmax',
                    'Rain', 'Snow', 'Ptot', 'PET']
            x = {}
            for vrb in vrbs:
                x[vrb] = self[vrb]
            return x
        else:
            return super(WXDataFrame, self).__getitem__(key)


# =============================================================================


def read_weather_datafile(filename):
    print('-'*78)
    print('Reading weather data from "%s"...' % os.path.basename(filename))

    df = {'filename': filename,
          'Station Name': '',
          'Latitude': 0,
          'Longitude': 0,
          'Province': '',
          'Elevation': 0,
          'Climate Identifier': '',
          'Year': np.array([]),
          'Month': np.array([]),
          'Day': np.array([]),
          'Time': np.array([]),
          'Tmax': np.array([]),
          'Tavg': np.array([]),
          'Tmin': np.array([]),
          'Ptot': np.array([]),
          'Rain': None,
          'Snow': None,
          'PET': None,
          }

    # Get info from header and grab data from file :

    with open(filename, 'r') as f:
        reader = list(csv.reader(f, delimiter='\t'))
        for i, row in enumerate(reader):
            if len(row) == 0:
                continue

            if row[0] in ['Station Name', 'Province', 'Climate Identifier']:
                df[row[0]] = str(row[1])
            elif row[0] in ['Latitude', 'Longitude', 'Elevation']:
                try:
                    df[row[0]] = float(row[1])
                except ValueError:
                    print('Wrong format for entry "%s".' % row[0])
                    df[row[0]] = 0
            elif row[0] == 'Year':
                istart = i+1
                var = row
                data = np.array(reader[istart:]).astype('float')
                break

    data = clean_endsof_file(data)

    df['Year'] = data[:, var.index('Year')].astype(int)
    df['Month'] = data[:, var.index('Month')].astype(int)
    df['Day'] = data[:, var.index('Day')].astype(int)

    df['Tmax'] = data[:, var.index('Max Temp (deg C)')].astype(float)
    df['Tmin'] = data[:, var.index('Min Temp (deg C)')].astype(float)
    df['Tavg'] = data[:, var.index('Mean Temp (deg C)')].astype(float)
    df['Ptot'] = data[:, var.index('Total Precip (mm)')].astype(float)

    try:
        df['Time'] = data[:, var.index('Time')]
    except ValueError:
        # The time is not saved in the datafile. We need to calculate it from
        # the Year, Month, and Day arrays.
        df['Time'] = np.zeros(len(df['Year']))
        for i in range(len(df['Year'])):
            dtuple = (df['Year'][i], df['Month'][i], df['Day'][i])
            df['Time'][i] = xldate_from_date_tuple(dtuple, 0)

    try:
        df['PET'] = data[:, var.index('ETP (mm)')]
        print('Potential evapotranspiration imported from datafile.')
    except ValueError:
        print('No potential evapotranspiration in datafile.')

    try:
        df['Rain'] = data[:, var.index('Rain (mm)')]
        print('Rain data imported from datafile.')
    except ValueError:
        print('No rain in datafile.')

    try:
        df['Snow'] = data[:, var.index('Snow (mm)')]
        print('Snow data imported from datafile.')
    except ValueError:
        print('No snow in datafile.')

    return df


# =============================================================================


def load_weather_log(fname, varname):
    print('loading info for missing %s' % varname)

    # ---- load Data ----

    with open(fname, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        reader = list(reader)[36:]

    # ---- load data and convert time ----

    xldates = []
    for i in range(len(reader)):
        if reader[i][0] == varname:
            year = int(float(reader[i][1]))
            month = int(float(reader[i][2]))
            day = int(float(reader[i][3]))
            xldates.append(xldate_from_date_tuple((year, month, day), 0))

    time = []
    tseg = [np.nan, xldates[0], xldates[0]+1]
    for xldate in xldates:
        if tseg[2] == xldate:
            if xldate == xldates[-1]:  # the last data of the series is missing
                time.extend(tseg)
            else:
                tseg[2] += 1
        else:
            time.extend(tseg)
            tseg[1] = xldate
            tseg[2] = xldate + 1

    time.append(np.nan)
    time = np.array(time)

    return time


# =============================================================================


def clean_endsof_file(data):
    """
    Remove nan values at the beginning and end of the record if any.
    """

    # ---- Beginning ----

    n = len(data[:, 0])
    while True:
        if len(data[:, 0]) == 0:
            print('Dataset is empty.')
            return None

        if np.all(np.isnan(data[0, 3:])):
            data = np.delete(data, 0, axis=0)
        else:
            break

    if n < len(data[:, 0]):
        print('%d empty' % (n - len(data[:, 0])) +
              ' rows of data removed at the beginning of the dataset.')

    # ---- End ----

    n = len(data[:, 0])
    while True:
        if np.all(np.isnan(data[-1, 3:])):
            data = np.delete(data, -1, axis=0)
        else:
            break

    if n < len(data[:, 0]):
        print('%d empty' % (n - len(data[:, 0])) +
              ' rows of data removed at the end of the dataset.')

    return data


# =========================================================================

def make_timeserie_continuous(time, date, data):
    """
    Scan the entire time serie and will insert a row with nan values
    whenever there is a gap in the data and will return the continuous
    data set.

    data = tuple containing the data series
    date = tuple containg the time series for year, month and days
    """

    i = 0
    while i < len(time)-1:
        if (time[i+1]-time[i]) > 1:
            time = np.insert(time, i+1, time[i]+1)

            new = xldate_as_tuple(time[i]+1, 0)
            date[0] = np.insert(date[0], i+1, new[0])
            date[1] = np.insert(date[1], i+1, new[1])
            date[2] = np.insert(date[2], i+1, new[2])

            for k in range(len(data)):
                if data[k] is not None:
                    data[k] = np.insert(data[k], i+1, np.nan)

        i += 1

    return time, date, data


# =============================================================================


def fill_nan(time, data, name='data', fill_mode='zeros'):
    # Preferable to be run before ETP or RAIN is estimated, So that
    # there is no missing value in both of these estimated time series.
    # It needs to be ran after but after 'check_time_continuity'.

    # fill_mode can be either 'zeros' or 'interp'

    if data is None:
        return None

    if fill_mode == 'interp':
        indx = np.where(~np.isnan(data))[0]
        nbr_nan = len(data)-len(indx)
        if nbr_nan == 0:
            print('There was no nan values in %s series.' % name)
        else:
            data = np.interp(time, time[indx], data[indx])
            print('There was %d nan values in %s series.' % (nbr_nan, name))
            print('Missing values were estimated by linear interpolation.')

    elif fill_mode == 'zeros':
        indx = np.where(np.isnan(data))[0]
        if len(indx) == 0:
            print('There was no nan values in %s series.' % name)
        else:
            data[indx] = 0
            print(('There was %d nan values in %s series. Missing values'
                   ' were assigned a 0 value.') % (len(indx), name))

    else:
        raise ValueError('fill_mode must be either "zeros" or "interp"')

    return data


#  ============================================================================


def add_ETP_to_weather_data_file(filename):
    """ Add PET to weather data file."""

    print('>>> Adding PET to weather data file...')

    # load and stock original data :

    with open(filename, 'r') as f:
        reader = list(csv.reader(f, delimiter='\t'))
        for i, row in enumerate(reader):
            if len(row) == 0:
                continue

            if row[0] == 'Latitude':
                lat = float(row[1])
            elif row[0] == 'Year':
                istart = i+1
                vrbs = row
                data = np.array(reader[istart:]).astype('float')
                break

    Year = data[:, vrbs.index('Year')].astype(int)
    Month = data[:, vrbs.index('Month')].astype(int)
    Day = data[:, vrbs.index('Day')].astype(int)
    Dates = [Year, Month, Day]

    Tavg = data[:, vrbs.index('Mean Temp (deg C)')]
    x = calc_monthly_mean(Year, Month, Tavg)
    Ta = calcul_monthly_normals(x[1], x[2])

    PET = calcul_Thornthwaite(Dates, Tavg, lat, Ta)

    # extend dataset with PET :

    if 'ETP (mm)' in vrbs:
        print('There is already a ETP time series in the dataset file. '
              'The existing data were overriden.')

        indx = vrbs.index('ETP (mm)')
        for i in range(len(PET)):
            reader[i+istart][indx] = PET[i]
    else:
        print('Added ETP to dataset file.')

        reader[istart-1].append('ETP (mm)')
        for i in range(len(PET)):
            reader[i+istart].append(PET[i])

    # Save data :

    with open(filename, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerows(reader)

    print('ETP time series added successfully to %s' % filename)


# =============================================================================


def calcul_rain_from_ptot(Tavg, Ptot, Tcrit=0):
    rain = np.copy(Ptot)
    rain[np.where(Tavg < Tcrit)[0]] = 0
    return rain


# =============================================================================


def calc_monthly_sum(yy_dly, mm_dly, x_dly):
    return calc_monthly(yy_dly, mm_dly, x_dly, np.sum)


def calc_monthly_mean(yy_dly, mm_dly, x_dly):
    return calc_monthly(yy_dly, mm_dly, x_dly, np.mean)


def calc_monthly(yy_dly, mm_dly, x_dly, func):
    yy = np.unique(yy_dly)
    mm = range(1, 13)

    yy_mly = np.repeat(yy, len(mm))
    mm_mly = np.tile(mm, len(yy))
    x_mly = np.zeros(len(mm)*len(yy))

    for i in range(len(mm)*len(yy)):
        indx = np.where((yy_dly == yy_mly[i]) & (mm_dly == mm_mly[i]))[0]
        if len(indx) < monthrange(yy_mly[i], mm_mly[i])[1]:
            x_mly[i] = np.nan  # incomplete dataset for this month
        else:
            x_mly[i] = func(x_dly[indx])

    return yy_mly, mm_mly, x_mly

# -------------------------------------------------------------------------


def calc_yearly_sum(yy_dly, x_dly):
    return calc_yearly(yy_dly, x_dly, np.sum)


def calc_yearly_mean(yy_dly, x_dly):
    return calc_yearly(yy_dly, x_dly, np.mean)


def calc_yearly(yy_dly, x_dly, func):
    yy_yrly = np.unique(yy_dly)
    x_yrly = np.zeros(len(yy_yrly))
    for i in range(len(yy_yrly)):
        indx = np.where(yy_dly == yy_yrly[i])[0]
        x_yrly[i] = func(x_dly[indx])

    return yy_yrly, x_yrly


# =============================================================================


def calcul_monthly_normals(mm_mly, x_mly):
    x_norm = np.zeros(12)
    for i, mm in enumerate(range(1, 13)):
        indx = np.where((mm_mly == mm) & (~np.isnan(x_mly)))[0]
        if len(indx) > 0:
            x_norm[i] = np.mean(x_mly[indx])
        else:
            x_norm[i] = np.nan

    return x_norm


# =============================================================================


def generate_weather_HTML(staname, prov, lat, climID, lon, alt):

    # HTML table with the info related to the weather station.

    FIELDS = [['Station', staname],
              ['Latitude', '%0.3f°' % lat],
              ['Longitude', '%0.3f°' % lon],
              ['Altitude', '%0.1f m' % alt],
              ['Clim. ID', climID],
              ['Province', prov]
              ]

    table = '<table border="0" cellpadding="2" cellspacing="0" align="left">'
    for row in FIELDS:
        table += '''
                 <tr>
                   <td width=10></td>
                   <td align="left">%s</td>
                   <td align="left" width=20>:</td>
                   <td align="left">%s</td>
                   </tr>
                 ''' % (row[0], row[1])
    table += '</table>'

    return table


# =============================================================================


if __name__ == '__main__':
    filename = 'SUSSEX (8105200_8105210)_1980-2017.out'
    df = WXDataFrame(filename)

    add_ETP_to_weather_data_file(filename)
