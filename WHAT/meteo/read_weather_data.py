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

# Third party imports :

import numpy as np
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

# Local imports :

for i in range(2):
    try:
        from _version import __version__
        from meteo.evapotranspiration import calcul_Thornthwaite
        break
    except ImportError:  # to run this module standalone
        print('Running module as a standalone script...')
        import sys
        from os.path import dirname, realpath
        sys.path.append(dirname(dirname(realpath(__file__))))


# =============================================================================


def load_weather_datafile(filename):
    print('-'*78)
    print('Loading weather data from "%s"...' % os.path.basename(filename))

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
          'PET': None,
          'Monthly Year': np.array([]),
          'Monthly Month': np.array([]),
          'Monthly Tmax': np.array([]),
          'Monthly Tmin': np.array([]),
          'Monthly Tavg': np.array([]),
          'Monthly Ptot': np.array([]),
          'Monthly Rain': None,
          'Monthly PET': None
          }

    df['normals'] = {'Tmax': np.array([]),
                     'Tmin': np.array([]),
                     'Tavg': np.array([]),
                     'Ptot': np.array([]),
                     'Rain': None,
                     'PET': None}

    # -------------------------------------------------------- import data ----

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
                except:
                    print('Wrong format for entry "%s".' % row[0])
                    df[item[0]] = 0
            elif row[0] == 'Year':
                istart = i+1
                var = row
                header = reader[:istart]
                data = np.array(reader[istart:]).astype('float')
                break

    data = clean_endsof_file(data)

    df['Year'] = data[:, var.index('Year')].astype(int)
    df['Month'] = data[:, var.index('Month')].astype(int)
    df['Day'] = data[:, var.index('Day')].astype(int)

    df['Tmax'] = data[:, var.index('Max Temp (deg C)')]
    df['Tmin'] = data[:, var.index('Min Temp (deg C)')]
    df['Tavg'] = data[:, var.index('Mean Temp (deg C)')]
    df['Ptot'] = data[:, var.index('Total Precip (mm)')]

    try:
        df['Time'] = data[:, var.index('Time')]
    except ValueError:
        df['Time'] = np.zeros(len(df['Year']))
        for i in range(len(df['Year'])):
            dtuple = (df['Year'][i], df['Month'][i], df['Day'][i])
            df['Time'][i] = xldate_from_date_tuple(dtuple, 0)

    print()
    try:
        df['PET'] = data[:, var.index('ETP (mm)')]
        print('Potential evapotranspiration imported from datafile.')
    except ValueError:
        print('Potential evapotranspiration evaluated with Thornthwaite.')

    try:
        df['Rain'] = data[:, var.index('Rain (mm)')]
        print('Rain data imported from datafile.')
    except ValueError:
        print('Rain estimated from Ptot.')

    # ----------------------------------------------------- Import missing ----

    finfo = filename[:-3] + 'log'
    if os.path.exists(finfo):
        df['Missing Tmax'] = load_weather_log(finfo, 'Max Temp (deg C)')
        df['Missing Tmin'] = load_weather_log(finfo, 'Min Temp (deg C)')
        df['Missing Tavg'] = load_weather_log(finfo, 'Mean Temp (deg C)')
        df['Missing Ptot'] = load_weather_log(finfo, 'Total Precip (mm)')
    else:
        df['Missing Tmax'] = []
        df['Missing Tmin'] = []
        df['Missing Tavg'] = []
        df['Missing Ptot'] = []

    # -------------------------------------------------------- format data ----

    print()
    df = make_timeserie_continuous(df)
    df = fill_nan(df)

    # -------------------------------------------------- monthly & normals ----

    for vrb in ['Tmax', 'Tmin', 'Tavg']:
        key = 'Monthly %s' % vrb
        x = calc_monthly_mean(df['Year'], df['Month'], df[vrb])
        df[key] = x[2]
        df['normals'][vrb] = calcul_normals_from_monthly(x[1], x[2])

    x = calc_monthly_sum(df['Year'], df['Month'], df['Ptot'])
    df['Monthly Ptot'] = x[2]
    df['Monthly Year'] = x[0]
    df['Monthly Month'] = x[1]
    df['normals']['Ptot'] = calcul_normals_from_monthly(x[1], x[2])

    # ----------------------------------------------------- secondary vrbs ----

    # ---- Rain ----

    if df['Rain'] is None:
        df['Rain'] = calcul_rain_from_ptot(df['Tavg'], df['Ptot'], Tcrit=0)

    x = calc_monthly_sum(df['Year'], df['Month'], df['Rain'])
    df['Monthly Rain'] = x[2]
    df['normals']['Rain'] = calcul_normals_from_monthly(x[1], x[2])

    # ---- Potential Evapotranspiration ----

    if df['PET'] is None:
        dates = [df['Year'], df['Month'], df['Day']]
        Tavg = df['Tavg']
        lat = df['Latitude']
        Ta = df['normals']['Tavg']
        df['PET'] = calcul_Thornthwaite(dates, Tavg, lat, Ta)

    x = calc_monthly_sum(df['Year'], df['Month'], df['PET'])
    df['Monthly PET'] = x[2]
    df['normals']['PET'] = calcul_normals_from_monthly(x[1], x[2])

    print('-'*78)

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


# =============================================================================


def make_timeserie_continuous(df):
    """
    Scan the entire time serie and will insert a row with nan values whenever
    there is a gap in the data and will return the continuous data set.

    df : dataframe
    """

    i = 0
    while i < len(df['Time'])-1:
        if (df['Time'][i+1]-df['Time'][i]) > 1:
            df['Time'] = np.insert(df['Time'], i+1, df['Time'][i]+1)

            date = xldate_as_tuple(df['Time'][i]+1, 0)
            df['Year'] = np.insert(df['Year'], i+1, date[0])
            df['Month'] = np.insert(df['Month'], i+1, date[1])
            df['Day'] = np.insert(df['Day'], i+1, date[2])

            for key in ['Tmax', 'Tmin', 'Tavg', 'Ptot']:
                df[key] = np.insert(df[key], i+1, np.nan)

            for key in ['PET', 'Rain']:
                if df[key] is not None:
                    df[key] = np.insert(df[key], i+1, np.nan)

        i += 1

    return df


# =============================================================================

# Preferable to be run before ETP or RAIN is estimated, So that
# there is no missing value in both of these estimated time series.
# It needs to be ran after but after 'check_time_continuity'.

def fill_nan(df):
    time = df['Time']

    for var in ['Tmax', 'Tmin', 'Tavg', 'PET']:
        if df[var] is None:
            continue

        indx = np.where(~np.isnan(df[var]))[0]
        nbr_nan = len(df[var])-len(indx)
        if nbr_nan == 0:
            print('There was no nan values in %s series.' % var)
        else:
            df[var] = np.interp(time, time[indx], df[var][indx])
            print('There was %d nan values in %s series.' % (nbr_nan, var))
            print('Missing values were estimated by linear interpolation.')

    for var in ['Ptot', 'Rain']:
        if df[var] is None:
            continue

        indx = np.where(np.isnan(df[var]))[0]
        if len(indx) == 0:
            print('There was no nan values in %s series.' % var)
        else:
            df['Ptot'][indx] = 0
            print('There was %d nan values in %s series.' % (len(indx), var))
            print('Missing values were assigned a 0 value.')

    return df


#  ============================================================================


def add_ETP_to_weather_data_file(filename):
    """ Add PET to weather data file."""

    # load and stock original data :

    meteoObj = MeteoObj()
    meteoObj.load(filename)

    HEADER = copy.copy(meteoObj.HEADER)
    DATAORIG = np.copy(meteoObj.DATA)
    DATE = DATAORIG[:, :3]

    # -- compute air temperature normals --

    meteoObj.clean_endsof_file()
    meteoObj.check_time_continuity()
    meteoObj.get_TIME(meteoObj.DATA[:, :3])
    meteoObj.fill_nan()

    NORMALS, _ = calculate_normals(meteoObj.DATA, meteoObj.datatypes)

    varnames = np.array(meteoObj.HEADER[-1])
    indx = np.where(varnames == 'Mean Temp (deg C)')[0][0]

    Ta = NORMALS[:, indx-3]    # monthly air temperature averages (deg C)
    LAT = float(meteoObj.LAT)  # Latitude (decimal deg)

    # -- estimate ETP from original temperature time series --

    TAVG = np.copy(DATAORIG[:, indx])
    ETP = calculate_ETP(DATE, TAVG, LAT, Ta)

    # -- extend data --

    filecontent = copy.copy(HEADER)
    if np.any(varnames == 'ETP (mm)'):
        print('Already a ETP time series in the datasets. Overriding data.')

        # Override ETP in DATA:
        indx = np.where(varnames == 'ETP (mm)')[0][0]
        DATAORIG[:, indx] = ETP

    else:
        # Add new variable name to header:
        filecontent[-1].append('ETP (mm)')

        # Add ETP to DATA matrix:
        ETP = ETP[:, np.newaxis]
        DATAORIG = np.hstack([DATAORIG, ETP])

        DATAORIG.tolist()

    # -- save data --

    for i in range(len(DATAORIG[:, 0])):
        filecontent.append(DATAORIG[i, :])

    with open(filename, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerows(filecontent)

    print('ETP time series added successfully to %s' % filename)

# =========================================================================


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


# =============================================================================


def calcul_normals_from_monthly(mm_mly, x_mly):
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
    df = load_weather_datafile(filename)
