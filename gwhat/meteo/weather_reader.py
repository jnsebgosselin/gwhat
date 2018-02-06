# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Standard Library imports

import os
import os.path as osp
import csv
from calendar import monthrange
from time import strftime
from collections.abc import Mapping
from abc import abstractmethod

# ---- Third Party imports

import numpy as np
from xlrd.xldate import xldate_from_datetime_tuple, xldate_from_date_tuple
from xlrd import xldate_as_tuple


# ---- Local Library imports

from gwhat.meteo.evapotranspiration import calcul_Thornthwaite
from gwhat.common.utils import save_content_to_csv, save_content_to_file
from gwhat import __namever__


# ---- API

class WXDataFrameBase(Mapping):
    """
    A daily weather data frame base class.
    """
    def __init__(self, *args, **kwargs):
        super(WXDataFrameBase, self).__init__(*args, **kwargs)
        self.store = None

    @abstractmethod
    def __load_dataset__(self):
        """Loads the dataset and save it in a store."""
        pass

    def get_monthly_normals(self, yearmin=None, yearmax=None):
        """
        Returns a dict with the normal values of the weather dataset
        for the period defined by yearmin and yearmax.
        """
        raise NotImplementedError

    def export_dataset_to_file(self, filename, time_frame):
        """
        Exports the dataset to file using a daily, monthly or yearly format.
        The extension of the file determine in which file type the data will
        be saved (xls or xlsx for Excel, csv for coma-separated values text
        file, or tsv for tab-separated values text file).
        """
        if time_frame == 'daily':
            vrbs = ['Year', 'Month', 'Day']
            lbls = ['Year', 'Month', 'Day']
        elif time_frame == 'monthly':
            vrbs = ['Year', 'Month']
            lbls = ['Year', 'Month']
        elif time_frame == 'yearly':
            vrbs = ['Year']
            lbls = ['Year']
        else:
            raise ValueError('"time_frame" must be either "yearly", "monthly"'
                             ' or "daily".')

        vrbs.extend(['Tmin', 'Tavg', 'Tmax', 'Rain', 'Snow', 'Ptot', 'PET'])
        lbls.extend(['Tmin (\u00B0C)', 'Tavg (\u00B0C)', 'Tmax (\u00B0C)',
                     'Rain (mm)', 'Snow (mm)', 'Ptot (mm)',
                     'PET (mm)'])

        startdate = '%02d/%02d/%d' % (
                self['Day'][0], self['Month'][0], self['Year'][0])
        enddate = '%02d/%02d/%d' % (
                self['Day'][-1], self['Month'][-1], self['Year'][-1])

        fcontent = [['Station Name', self['Station Name']],
                    ['Province', self['Province']],
                    ['Latitude', self['Longitude']],
                    ['Longitude', self['Longitude']],
                    ['Elevation', self['Elevation']],
                    ['Climate Identifier', self['Climate Identifier']],
                    ['', ''],
                    ['Start Date ', startdate],
                    ['End Date ', enddate],
                    ['', ''],
                    ['Created by', __namever__],
                    ['Created on', strftime("%d/%m/%Y")],
                    ['', '']
                    ]
        fcontent.append(lbls)

        N = len(self[time_frame]['Year'])
        M = len(vrbs)
        data = np.zeros((N, M))
        for j, vrb in enumerate(vrbs):
            data[:, j] = self[time_frame][vrb]
        fcontent.extend(data.tolist())

        save_content_to_file(filename, fcontent)

    def export_dataset_to_HELP(self):
        raise NotImplementedError


class WXDataFrame(WXDataFrameBase):
    """A daily weather dataset container that loads its data from a file."""

    def __init__(self, filename, *args, **kwargs):
        super(WXDataFrame, self).__init__(*args, **kwargs)
        self.__load_dataset__(filename)

    def __getitem__(self, key):
        """Returns the value saved in the store at key."""
        if key == 'daily':
            vrbs = ['Year', 'Month', 'Day', 'Tmin', 'Tavg', 'Tmax',
                    'Rain', 'Snow', 'Ptot', 'PET']
            x = {}
            for vrb in vrbs:
                x[vrb] = self[vrb]
            return x
        else:
            return self.store.__getitem__(key)

    def __setitem__(self, key, value):
        return NotImplementedError

    def __iter__(self):
        return NotImplementedError

    def __len__(self, key):
        return NotImplementedError

    def __init_store__(self, filename):
        """Initializes the store."""
        self.store = dict()
        self.store['filename'] = filename
        self.store['Station Name'] = ''
        self.store['Latitude'] = 0
        self.store['Longitude'] = 0
        self.store['Province'] = ''
        self.store['Elevation'] = 0
        self.store['Climate Identifier'] = ''

        self.store['Year'] = np.array([])
        self.store['Month'] = np.array([])
        self.store['Day'] = np.array([])
        self.store['Time'] = np.array([])

        self.store['Tmax'] = np.array([])
        self.store['Tavg'] = np.array([])
        self.store['Tmin'] = np.array([])
        self.store['Ptot'] = np.array([])
        self.store['Rain'] = None
        self.store['Snow'] = None
        self.store['PET'] = None

        self.store['Missing Tmax'] = []
        self.store['Missing Tmin'] = []
        self.store['Missing Tavg'] = []
        self.store['Missing Ptot'] = []

        self.store['monthly'] = {'Year': np.array([]),
                                 'Month': np.array([]),
                                 'Tmax': np.array([]),
                                 'Tmin': np.array([]),
                                 'Tavg': np.array([]),
                                 'Ptot': np.array([]),
                                 'Rain': None,
                                 'Snow': None,
                                 'PET': None}

        self.store['yearly'] = {'Year': np.array([]),
                                'Tmax': np.array([]),
                                'Tmin': np.array([]),
                                'Tavg': np.array([]),
                                'Ptot': np.array([]),
                                'Rain': None,
                                'Snow': None,
                                'PET': None}

        self.store['normals'] = {'Tmax': np.array([]),
                                 'Tmin': np.array([]),
                                 'Tavg': np.array([]),
                                 'Ptot': np.array([]),
                                 'Rain': None,
                                 'Snow': None,
                                 'PET': None,
                                 'Period': (None, None)}

    def __load_dataset__(self, filename):
        """Loads the dataset from a file and saves it in the store."""
        print('-'*78)
        print('Reading weather data from "%s"...' % os.path.basename(filename))

        self.__init_store__(filename)

        # ---- Import primary data

        data = read_weather_datafile(filename)
        for key in data.keys():
            self.store[key] = data[key]

        # ---- Format Data

        # Make the daily time series continuous :

        date = [self['Year'], self['Month'], self['Day']]
        vrbs = ['Tmax', 'Tavg', 'Tmin', 'Ptot', 'Rain', 'PET']
        data = [self[vrb] for vrb in vrbs]
        time, date, data = make_timeserie_continuous(self['Time'], date, data)

        self.store['Time'] = time
        self.store['Year'], self.store['Month'], self.store['Day'] = date
        for i, vrb in enumerate(vrbs):
            self.store[vrb] = data[i]

        # Fill missing with estimated values :

        for vbr in ['Tmax', 'Tavg', 'Tmin', 'PET']:
            self.store[vbr] = fill_nan(self['Time'], self[vbr], vbr, 'interp')

        for vbr in ['Ptot', 'Rain', 'Snow']:
            self.store[vbr] = fill_nan(self['Time'], self[vbr], vbr, 'zeros')

        # ---- Rain & Snow

        # Generate rain and snow daily series if it was not present in the
        # datafile.

        # Rain

        if self['Rain'] is None:
            self.store['Rain'] = calcul_rain_from_ptot(
                    self['Tavg'], self['Ptot'], Tcrit=0)
            print("Rain estimated from Ptot.")

        # Snow

        if self['Snow'] is None:
            self.store['Snow'] = self['Ptot'] - self['Rain']
            print("Snow estimated from Ptot.")

        # ---- Missing data

        root, ext = osp.splitext(filename)
        finfo = root + '.log'
        if os.path.exists(finfo):
            print('Reading gapfill data from "%s"...' % osp.basename(finfo))
            keys_labels = [('Missing Tmax', 'Max Temp (deg C)'),
                           ('Missing Tmin', 'Min Temp (deg C)'),
                           ('Missing Tavg', 'Mean Temp (deg C)'),
                           ('Missing Ptot', 'Total Precip (mm)')]
            for key, label in keys_labels:
                self.store[key] = load_weather_log(finfo, label)

        # ---- Monthly & Normals

        self.store['normals']['Period'] = (np.min(self['Year']),
                                           np.max(self['Year']))

        # Temperature based variables :

        for vrb in ['Tmax', 'Tmin', 'Tavg']:
            x_yr = calc_yearly_mean(self['Year'], self[vrb])
            self.store['yearly'][vrb] = x_yr[1]

            x_mt = calc_monthly_mean(self['Year'], self['Month'], self[vrb])
            self.store['monthly'][vrb] = x_mt[2]

            self.store['normals'][vrb] = calcul_monthly_normals(
                    x_mt[0], x_mt[1], x_mt[2])

        # Precipitation based variables :

        for vrb in ['Ptot', 'Rain', 'Snow']:
            x_yr = calc_yearly_sum(self['Year'], self[vrb])
            self.store['yearly'][vrb] = x_yr[1]

            x_mt = calc_monthly_sum(self['Year'], self['Month'], self[vrb])
            self.store['monthly'][vrb] = x_mt[2]

            self.store['normals'][vrb] = calcul_monthly_normals(
                    x_mt[0], x_mt[1], x_mt[2])

        self.store['yearly']['Year'] = x_yr[0]
        self.store['monthly']['Year'] = x_mt[0]
        self.store['monthly']['Month'] = x_mt[1]

        # ---- Potential Evapotranspiration

        if self['PET'] is None:
            dates = [self['Year'], self['Month'], self['Day']]
            Tavg = self['Tavg']
            lat = self['Latitude']
            Ta = self['normals']['Tavg']
            self.store['PET'] = calcul_Thornthwaite(dates, Tavg, lat, Ta)
            print("Potential evapotranspiration evaluated with Thornthwaite.")

        x_yr = calc_yearly_sum(self['Year'], self['PET'])
        self['yearly']['PET'] = x_yr[1]

        x_mt = calc_monthly_sum(self['Year'], self['Month'], self['PET'])
        self.store['monthly']['PET'] = x_mt[2]

        self.store['normals']['PET'] = calcul_monthly_normals(
                x_mt[0], x_mt[1], x_mt[2])

        print('-'*78)


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
        pass

    try:
        df['Rain'] = data[:, var.index('Rain (mm)')]
        print('Rain data imported from datafile.')
    except ValueError:
        pass

    try:
        df['Snow'] = data[:, var.index('Snow (mm)')]
        print('Snow data imported from datafile.')
    except ValueError:
        pass

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
    Scans the entire daily time series, inserts a row with nan values whenever
    there is a gap in the data, and returns the continuous daily data set.

    time = 1d numpy array containing the time in Excel numeric format.
    date = tuple containg the time series for year, month and days.
    data = tuple containing the data series.
    """
    # Initialize the arrays in which the continuous time series will be saved :

    ctime = np.arange(time[0], time[-1]+1)
    if np.array_equal(ctime, time):
        # The dataset is already continuous.
        return time, date, data
    cdate = [np.empty(len(ctime))*np.nan for item in date]
    cdata = []
    for item in data:
        if item is not None:
            cdata.append(np.empty(len(ctime))*np.nan)
        else:
            cdata.append(None)

    # Fill the continuous arrays :

    indexes = np.digitize(time, ctime, right=True)
    for i in range(len(date)):
        cdate[i][indexes] = date[i]
    for i in range(len(data)):
        if data[i] is not None:
            cdata[i][indexes] = data[i]

    # Complete the dates for the lines that where missing and convert to
    # integers :

    nan_indexes = np.where(np.isnan(cdate[0]))[0]
    for idx in nan_indexes:
        new_date = xldate_as_tuple(ctime[idx], 0)
        cdate[0][idx] = new_date[0]
        cdate[1][idx] = new_date[1]
        cdate[2][idx] = new_date[2]
    cdate[0] = cdate[0].astype(int)
    cdate[1] = cdate[1].astype(int)
    cdate[2] = cdate[2].astype(int)

    return ctime, cdate, cdata


def fill_nan(time, data, name='data', fill_mode='zeros'):
    """
    Fills the nan values in data with zeros if fill_mode value is 'zeros' or
    using linear interpolation if fill_mode value is 'interp'.
    """
    if fill_mode not in ['zeros', 'interp']:
        raise ValueError('fill_mode must be either "zeros" or "interp"')

    if data is None:
        return None

    nbr_nan = len(np.where(np.isnan(data))[0])
    if nbr_nan == 0:
        # There is no missing value in the dataset.
        return data

    if fill_mode == 'interp':
        indx = np.where(~np.isnan(data))[0]
        data = np.interp(time, time[indx], data[indx])
        print("%d missing values were estimated by linear interpolation"
              " in %s." % (nbr_nan, name))
    elif fill_mode == 'zeros':
        indx = np.where(np.isnan(data))[0]
        data[indx] = 0
        print("%d missing values were assigned a value of 0"
              " in %s." % (nbr_nan, name))
    return data


# ---- Read CWEEDS Files

def read_cweeds_file(filename, format_to_daily=True):
    """
    Reads and formats data from a CWEEDS file, either version WY2 or WY3.
    Returns a dictionary, which includes a numpy array of the global
    solar irradiance in MJ/m², as well as corresponding arrays of the years,
    months, days, and hours. By default, the hourly data from the CWEEDS file
    are formated to daily values. The data are kept in a hourly format if
    format_to_daily is set to False.
    """
    # Determine if the CWEEDS file is in the WY2 or WY3 format :

    root, ext = osp.splitext(filename)
    ext = ext.replace('.', '')
    if ext not in ['WY2', 'WY3']:
        raise ValueError("%s is not a valid file extension. CWEEHDS files must"
                         " have either a WY2 or WY3 extension" % ext)

    # Open and format the data from the CWEEDS file :

    with open(filename, 'r') as f:
        reader = list(csv.reader(f))

    header_df = {}
    if ext == 'WY3':
        # We remove the header line from the data if the format is WY3.
        header_list = reader.pop(0)
        header_df['HORZ version'] = header_list[0]
        header_df['Location'] = header_list[1]
        header_df['Province'] = header_list[2]
        header_df['Country'] = header_list[3]
        header_df['Station ID'] = header_list[4]
        header_df['Latitude'] = float(header_list[5])
        header_df['Longitude'] = float(header_list[6])
        header_df['Time Zone'] = float(header_list[7])
        header_df['Elevation'] = float(header_list[8])

    char_offset = 0 if ext == 'WY2' else 2
    hourly_df = {}
    hourly_df['Years'] = np.empty(len(reader)).astype(int)
    hourly_df['Months'] = np.empty(len(reader)).astype(int)
    hourly_df['Days'] = np.empty(len(reader)).astype(int)
    hourly_df['Hours'] = np.empty(len(reader)).astype(int)
    hourly_df['Time'] = np.empty(len(reader)).astype('float64')
    # Global horizontal irradiance, kJ/m²
    hourly_df['Irradiance'] = np.empty(len(reader)).astype('float64')

    for i, line in enumerate(reader):
        hourly_df['Years'][i] = year = int(line[0][char_offset:][6:10])
        hourly_df['Months'][i] = month = int(line[0][char_offset:][10:12])
        hourly_df['Days'][i] = day = int(line[0][char_offset:][12:14])
        hourly_df['Hours'][i] = hour = int(line[0][char_offset:][14:16]) - 1
        # The global horizontal irradiance is converted from kJ/m² to MJ/m².
        hourly_df['Irradiance'][i] = float(line[0][char_offset:][20:24])/1000

        # Compute time in Excel numeric format :
        hourly_df['Time'][i] = xldate_from_datetime_tuple(
                (year, month, day, hour, 0, 0), 0)

    if format_to_daily:
        # Convert the hourly data to daily format.
        assert len(hourly_df['Irradiance']) % 24 == 0
        new_shape = (len(hourly_df['Irradiance'])//24, 24)

        daily_df = {}
        daily_df['Irradiance'] = np.sum(
                hourly_df['Irradiance'].reshape(new_shape), axis=1)
        for key in ['Years', 'Months', 'Days', 'Time']:
            daily_df[key] = hourly_df[key].reshape(new_shape)[:, 0]
        daily_df['Hours'] = np.zeros(len(daily_df['Irradiance']))

        daily_df.update(header_df)
        daily_df['Time Format'] = 'daily'
        daily_df['CWEEDS Format'] = ext
        return daily_df
    else:
        hourly_df.update(header_df)
        hourly_df['Time Format'] = 'hourly'
        hourly_df['CWEEDS Format'] = ext
        return hourly_df


def join_daily_cweeds_wy2_and_wy3(wy2_df, wy3_df):
    """
    Join a CWEEDS dataset in the wy2 format to another cweeds dataset in the
    wy3 format.
    """
    assert wy2_df['CWEEDS Format'] == 'WY2'
    assert wy3_df['CWEEDS Format'] == 'WY3'
    assert wy2_df['Time Format'] == wy3_df['Time Format']

    time_wy23 = np.hstack([wy2_df['Time'], wy3_df['Time']])
    time_wy23 = np.unique(time_wy23)
    time_wy23 = np.sort(time_wy23)

    wy23_df = {}
    wy23_df['Time Format'] = wy3_df['Time Format']
    wy23_df['CWEEDS Format'] = 'WY2+WY3'

    # Copy the header info from WY3 dataset :

    for key in ['HORZ version', 'Location', 'Province', 'Country',
                'Station ID', 'Latitude', 'Longitude', 'Time Zone',
                'Elevation']:
        wy23_df[key] = wy3_df[key]

    # Merge the two datasets :

    wy23_df['Time'] = time_wy23
    wy23_df['Years'] = np.empty(len(time_wy23)).astype(int)
    wy23_df['Months'] = np.empty(len(time_wy23)).astype(int)
    wy23_df['Days'] = np.empty(len(time_wy23)).astype(int)
    wy23_df['Hours'] = np.empty(len(time_wy23)).astype(int)
    wy23_df['Irradiance'] = np.empty(len(time_wy23)).astype('float64')

    for dataset in [wy2_df, wy3_df]:
        indexes = np.digitize(dataset['Time'], time_wy23, right=True)
        for key in ['Years', 'Months', 'Days', 'Hours', 'Irradiance']:
            wy23_df[key][indexes] = dataset[key]

    return wy23_df


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


# %% if __name__ == '__main__'

if __name__ == '__main__':
    fmeteo = ("C:/Users/jsgosselin/GWHAT/gwhat/tests/"
              "sample_weather_datafile.csv")
    wxdset = WXDataFrame(fmeteo)

    filename = "C:/Users/jsgosselin/GWHAT/gwhat/tests/cweed_sample.WY2"
    daily_wy2 = read_cweeds_file(filename, format_to_daily=True)

    filename = ("C:/Users/jsgosselin/GWHAT/gwhat/tests/cweed_sample.WY3")
    daily_wy3 = read_cweeds_file(filename, format_to_daily=True)

    wy23_df = join_daily_cweeds_wy2_and_wy3(daily_wy2, daily_wy3)
