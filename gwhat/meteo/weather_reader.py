# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Imports: Standard Libraries

import os
import csv
from calendar import monthrange
from copy import copy

# ---- Imports: Third Parties

import numpy as np
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple


# ---- Imports: Local Libraries

from gwhat.meteo.evapotranspiration import calcul_Thornthwaite
from gwhat.common.utils import save_content_to_csv


# ---- API

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
                           'PET': None,
                           'Period': (None, None)}

        # ---- Import primary data

        data = read_weather_datafile(filename)
        for key in data.keys():
            self[key] = data[key]

        # ---- Import missing

        finfo = filename[:-3] + 'log'
        if os.path.exists(finfo):
            self['Missing Tmax'] = load_weather_log(finfo, 'Max Temp (deg C)')
            self['Missing Tmin'] = load_weather_log(finfo, 'Min Temp (deg C)')
            self['Missing Tavg'] = load_weather_log(finfo, 'Mean Temp (deg C)')
            self['Missing Ptot'] = load_weather_log(finfo, 'Total Precip (mm)')

        # ---- Format Data

        time = copy(self['Time'])
        date = [copy(self['Year']), copy(self['Month']), copy(self['Day'])]
        vbrs = ['Tmax', 'Tavg', 'Tmin', 'Ptot', 'Rain', 'PET']
        data = [self[x] for x in vbrs]

        # Make daily time series continuous :

        time, date, data = make_timeserie_continuous(self['Time'], date, data)
        self['Time'] = time
        self['Year'], self['Month'], self['Day'] = date[0], date[1], date[2]
        for i, vbr in enumerate(vbrs):
            self[vbr] = data[i]

        self['normals']['Period'] = (np.min(self['Year']),
                                     np.max(self['Year']))

        # Fill missing with estimated values :

        for vbr in ['Tmax', 'Tavg', 'Tmin', 'PET']:
            self[vbr] = fill_nan(self['Time'], self[vbr], vbr, 'interp')

        for vbr in ['Ptot', 'Rain', 'Snow']:
            self[vbr] = fill_nan(self['Time'], self[vbr], vbr, 'zeros')

        # ---- Monthly & Normals

        # Temperature based variables:

        for vrb in ['Tmax', 'Tmin', 'Tavg']:
            x = calc_yearly_mean(self['Year'], self[vrb])
            self['yearly'][vrb] = x[1]

            x = calc_monthly_mean(self['Year'], self['Month'], self[vrb])
            self['monthly'][vrb] = x[2]

            self['normals'][vrb] = calcul_monthly_normals(x[0], x[1], x[2])

        # Precipitation :

        x = calc_yearly_sum(self['Year'], self['Ptot'])
        self['yearly']['Ptot'] = x[1]
        self['yearly']['Year'] = x[0]

        x = calc_monthly_sum(self['Year'], self['Month'], self['Ptot'])
        self['monthly']['Ptot'] = x[2]
        self['monthly']['Year'] = x[0]
        self['monthly']['Month'] = x[1]

        self['normals']['Ptot'] = calcul_monthly_normals(x[0], x[1], x[2])

        # ---- Secondary Variables

        # Rain

        if self['Rain'] is None:
            self['Rain'] = calcul_rain_from_ptot(
                    self['Tavg'], self['Ptot'], Tcrit=0)
            print('Rain estimated from Ptot.')

        x = calc_yearly_sum(self['Year'], self['Rain'])
        self['yearly']['Rain'] = x[1]

        x = calc_monthly_sum(self['Year'], self['Month'], self['Rain'])
        self['monthly']['Rain'] = x[2]

        self['normals']['Rain'] = calcul_monthly_normals(x[0], x[1], x[2])

        # Snow

        if self['Snow'] is None:
            self['Snow'] = self['Ptot'] - self['Rain']
            print('Snow estimated from Ptot.')

        x = calc_yearly_sum(self['Year'], self['Snow'])
        self['yearly']['Snow'] = x[1]

        x = calc_monthly_sum(self['Year'], self['Month'], self['Snow'])
        self['monthly']['Snow'] = x[2]

        self['normals']['Snow'] = calcul_monthly_normals(x[0], x[1], x[2])

        # Potential Evapotranspiration

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

        self['normals']['PET'] = calcul_monthly_normals(x[0], x[1], x[2])

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


# ---- Base functions: file and data manipulation

def open_weather_datafile(filename):
    """
    Open the csv datafile and try to guess the delimiter.
    Return None if this fails.
    """
    for dlm in ['\t', ',']:
        with open(filename, 'r') as csvfile:
            reader = list(csv.reader(csvfile, delimiter=dlm))
        for line in reader:
            if line and line[0] == 'Station Name':
                return reader
    else:                                                    # pragma: no cover
        print("Failed to open %s." % os.path.basename(filename))
        return None


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

    # Get info from header and grab the data from the file.

    reader = open_weather_datafile(filename)
    if reader is None:                                       # pragma: no cover
        return
    else:
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


def add_PET_to_weather_datafile(filename):
    """Add PET to weather data file."""
    print('Adding PET to %s...' % os.path.basename(filename), end=' ')

    # Load and store original data.
    reader = open_weather_datafile(filename)
    if reader is None:                                       # pragma: no cover
        print('failed')
        return
    else:
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
    Ta = calcul_monthly_normals(x[0], x[1], x[2])

    PET = calcul_Thornthwaite(Dates, Tavg, lat, Ta)

    # Extend dataset with PET and save the dataset to csv.
    if 'ETP (mm)' in vrbs:
        indx = vrbs.index('ETP (mm)')
        for i in range(len(PET)):
            reader[i+istart][indx] = PET[i]
    else:
        reader[istart-1].append('ETP (mm)')
        for i in range(len(PET)):
            reader[i+istart].append(PET[i])

    # Save data.
    save_content_to_csv(filename, reader)
    print('done')


def open_weather_log(fname):
    """
    Open the csv file and try to guess the delimiter.
    Return None if this fails.
    """
    for dlm in [',', '\t']:
        with open(fname, 'r') as f:
            reader = list(csv.reader(f, delimiter=dlm))
            if reader[0][0] == 'Station Name':
                return reader[36:]
    else:
        return None


def load_weather_log(fname, varname):
    print('loading info for missing %s' % varname)
    reader = open_weather_log(fname)
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
            if xldate == xldates[-1]:
                # the last data of the series is missing
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


# ----- Base functions: monthly downscaling

def calc_monthly_sum(yy_dly, mm_dly, x_dly):
    """
    Calcul monthly cumulative values from daily values, where yy_dly are the
    years, mm_dly are the months (1 to 12), and x_dly are the daily values.
    """
    return calc_monthly(yy_dly, mm_dly, x_dly, np.sum)


def calc_monthly_mean(yy_dly, mm_dly, x_dly):
    """
    Calcul monthly mean values from daily values, where yy_dly are the
    years, mm_dly are the months (1 to 12), and x_dly are the daily values.
    """
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


def calcul_monthly_normals(years, months, x_mly, yearmin=None, yearmax=None):
    """Calcul the monthly normals from monthly values."""
    if len(years) != len(months) != len(x_mly):
        raise ValueError("The dimension of the years, months, and x_mly array"
                         " must match exactly.")
    if np.min(months) < 1 or np.max(months) > 12:
        raise ValueError("Months values must be between 1 and 12.")

    # Mark as nan monthly values that are outside the year range that is
    # defined by yearmin and yearmax :
    x_mly = np.copy(x_mly)
    if yearmin is not None:
        x_mly[years < yearmin] = np.nan
    if yearmax is not None:
        x_mly[years > yearmax] = np.nan

    # Calcul the monthly normals :
    x_norm = np.zeros(12)
    for i, mm in enumerate(range(1, 13)):
        indx = np.where((months == mm) & (~np.isnan(x_mly)))[0]
        if len(indx) > 0:
            x_norm[i] = np.mean(x_mly[indx])
        else:
            x_norm[i] = np.nan

    return x_norm


# ----- Base functions: yearly downscaling

def calc_yearly_sum(yy_dly, x_dly):
    """
    Calcul yearly cumulative values from daily values, where yy_dly are the
    years and x_dly are the daily values.
    """
    return calc_yearly(yy_dly, x_dly, np.sum)


def calc_yearly_mean(yy_dly, x_dly):
    """
    Calcul yearly mean values from daily values, where yy_dly are the years
    and x_dly are the daily values.
    """
    return calc_yearly(yy_dly, x_dly, np.mean)


def calc_yearly(yy_dly, x_dly, func):
    yy_yrly = np.unique(yy_dly)
    x_yrly = np.zeros(len(yy_yrly))
    for i in range(len(yy_yrly)):
        indx = np.where(yy_dly == yy_yrly[i])[0]
        x_yrly[i] = func(x_dly[indx])

    return yy_yrly, x_yrly


# ----- Base functions: secondary variables

def calcul_rain_from_ptot(Tavg, Ptot, Tcrit=0):
    rain = np.copy(Ptot)
    rain[np.where(Tavg < Tcrit)[0]] = 0
    return rain


# ---- Utility functions

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


if __name__ == '__main__':
    filename = 'FARNHAM (7022320)_1980-2017.csv'
    df = WXDataFrame(filename)
    add_PET_to_weather_datafile(filename)

    filename = 'AUTEUIL (7020392)_1980-2014.csv'
    df2 = WXDataFrame(filename)
    add_PET_to_weather_datafile(filename)
