# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------


# ---- Standard library imports
import os
import os.path as osp
import csv
import re
from time import strftime
from collections import OrderedDict
from collections.abc import Mapping
from abc import abstractmethod

# ---- Third party imports
import numpy as np
import pandas as pd
from xlrd.xldate import xldate_from_datetime_tuple, xldate_from_date_tuple


# ---- Local library imports

from gwhat.meteo.evapotranspiration import calcul_thornthwaite
from gwhat.common.utils import save_content_to_csv, save_content_to_file
from gwhat.utils.math import nan_as_text_tolist
from gwhat import __namever__


PRECIP_VARIABLES = ['Ptot', 'Rain', 'Snow']
TEMP_VARIABLES = ['Tmax', 'Tavg', 'Tmin', 'PET']
METEO_VARIABLES = PRECIP_VARIABLES + TEMP_VARIABLES


# ---- API
class WXDataFrameBase(Mapping):
    """
    A daily weather data frame base class.
    """

    def __init__(self, *args, **kwargs):
        super(WXDataFrameBase, self).__init__(*args, **kwargs)
        self.metadata = {
            'filename': '',
            'Station Name': '',
            'Station ID': '',
            'Location': '',
            'Latitude': 0,
            'Longitude': 0,
            'Elevation': 0}
        self.data = pd.DataFrame([], columns=METEO_VARIABLES)
        self.missing_value_indexes = {}

    @abstractmethod
    def __load_dataset__(self):
        """Loads the dataset and save it in a store."""
        pass

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
        fcontent.extend(nan_as_text_tolist(data))

        save_content_to_file(filename, fcontent)

    def get_data_period(self):
        """
        Return the year range for which data are available for this
        dataset.
        """
        return (data.index.min().year, data.index.max().year)

    # ---- Monthly and yearly values
    def get_monthly_values(self):
        """
        Return the monthly mean or cummulative values for the weather
        variables saved in this data frame.
        """
        group = self.data.groupby(
            [self.data.index.year, self.data.index.month])
        df = pd.concat(
            [group[PRECIP_VARIABLES].sum(), group[TEMP_VARIABLES].mean()],
            axis=1)
        df.index.rename(['Year', 'Month'], inplace=True)
        return df

    def get_yearly_values(self):
        """
        Return the yearly mean or cummulative values for the weather
        variables saved in this data frame.
        """
        group = self.data.groupby(self.data.index.year)
        df = pd.concat(
            [group[PRECIP_VARIABLES].sum(), group[TEMP_VARIABLES].mean()],
            axis=1)
        df.index.rename('Year', inplace=True)
        return df

    # ---- Normals
    def get_monthly_normals(self):
        """
        Return the monthly normals for the weather variables saved in this
        data frame.
        """
        df = self.get_monthly_values().groupby(level=[1]).mean()
        df.index.rename('Month', inplace=True)
        return df

    def get_yearly_normals(self):
        """
        Return the yearly normals for the weather variables saved in this
        data frame.
        """
        return self.get_yearly_values().mean()


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

    def __load_dataset__(self, filename):
        """Loads the dataset from a file and saves it in the store."""
        print('-' * 78)
        print('Reading weather data from "%s"...' % os.path.basename(filename))

        # Import data.
        self.metadata, self.data = read_weather_datafile(filename)

        # Make the daily time series continuous.
        self.data = self.data.resample('1D').asfreq()

        # Store the time indexes where data are missing.
        for var in METEO_VARIABLES:
            if var in self.data.columns:
                self.missing_value_indexes[var] = (
                    self.data.index[pd.isnull(self.data[var])])

        # Fill missing with values with in-stations linear interpolation for
        # temperature based variables.
        for var in TEMP_VARIABLES:
            if var in self.data.columns:
                self.data[var] = self.data[var].interpolate()

        # We fill the remaining missing value with 0.
        self.data = self.data.fillna(0)

        # Generate rain and snow daily series if it was not present in the
        # datafile.
        if 'Rain' not in self.data.columns:
            self.data['Rain'] = calcul_rain_from_ptot(
                self.data['Tavg'], self.data['Ptot'], Tcrit=0)
            self.data['Snow'] = self.data['Ptot'] - self.data['Rain']
            print("Rain and snow estimated from Ptot.")

        # Calculate potential evapotranspiration if missing.
        if 'PET' not in self.data.columns:
            self.data['PET'] = calcul_thornthwaite(
                self.data['Tavg'], self.metadata['Latitude'])
            print("Potential evapotranspiration evaluated with Thornthwaite.")

        isnull = self.data.isnull().any()
        if isnull.any():
            print("Warning: There is missing values remaining in the data "
                  "for {}.".format(', '.join(isnull[isnull].index.tolist())))
        print('-' * 78)

        # TODO: see what need to be done here to still support this
        # functionality.

        # # Missing data.
        # root, ext = osp.splitext(filename)
        # finfo = root + '.log'
        # if os.path.exists(finfo):
        #     print('Reading gapfill data from "%s"...' % osp.basename(finfo))
        #     keys_labels = [('Missing Tmax', 'Max Temp (deg C)'),
        #                    ('Missing Tmin', 'Min Temp (deg C)'),
        #                    ('Missing Tavg', 'Mean Temp (deg C)'),
        #                    ('Missing Ptot', 'Total Precip (mm)')]
        #     for key, label in keys_labels:
        #         self.store[key] = load_weather_log(finfo, label)


# ---- Base functions: file and data manipulation
def open_weather_datafile(filename):
    """
    Open the csv datafile and try to guess the delimiter.
    Return None if this fails.
    """
    for dlm in ['\t', ',', ';']:
        with open(filename, 'r') as csvfile:
            reader = list(csv.reader(csvfile, delimiter=dlm))
        for line in reader:
            if line and line[0] == 'Station Name':
                return reader
    else:
        print("Failed to open %s." % os.path.basename(filename))
        return None


def read_weather_datafile(filename):
    metadata = {'filename': filename,
                'Station Name': '',
                'Station ID': '',
                'Location': '',
                'Latitude': 0,
                'Longitude': 0,
                'Elevation': 0,
                }
    # Data is a pandas dataframe with the following required columns:
    # (1) Tmax, (2) Tavg, (3) Tmin, (4) Ptot.
    # The dataframe can also have these optional columns:
    # (5) Rain, (6) Snow, (7) PET
    # The dataframe must use a datetime index.

    # Get info from header and grab the data from the file.
    reader = open_weather_datafile(filename)
    if reader is None:
        return None, None

    HEADER_REGEX = {
        'Station Name': r'(?<!\S)(wellname|name)(:|=)?(?!\S)',
        'Station ID': r'(stationid|id|climateidentifier)',
        'Latitude': r'(?<!\S)(latitude|lat)(:|=)?(?!\S)',
        'Longitude': r'(?<!\S)(longitude|lon)(:|=)?(?!\S)',
        'Location': r'(?<!\S)(location|prov)(:|=)?(?!\S)',
        'Elevation': r'(?<!\S)(elev|alt)'
        }
    HEADER_TYPE = {
        'Station Name': str,
        'Station ID': str,
        'Location': str,
        'Latitude': float,
        'Longitude': float,
        'Elevation': float
        }

    for i, row in enumerate(reader):
        if len(row) == 0:
            continue

        label = row[0].replace(" ", "").replace("_", "")
        for key, regex in HEADER_REGEX.items():
            if re.search(regex, label, re.IGNORECASE):
                try:
                    metadata[key] = HEADER_TYPE[key](row[1])
                except ValueError:
                    # The default value will be kept.
                    print('Wrong format for entry "%s".' % key)
        else:
            if re.search(r'(time|datetime|year)', label, re.IGNORECASE):
                istart = i + 1
                break

    # Fetch the valid columns from the data header.
    COL_REGEX = OrderedDict([
        ('Year', r'(year)'),
        ('Month', r'(month)'),
        ('Day', r'(day)'),
        ('Tmax', r'(maxtemp)'),
        ('Tmin', r'(mintemp)'),
        ('Tavg', r'(meantemp)'),
        ('Ptot', r'(totalprecip)'),
        ('PET', r'(etp|evapo)'),
        ('Rain', r'(rain)'),
        ('Snow', r'(snow)')
        ])
    columns = []
    indexes = []
    for i, label in enumerate(row):
        label = label.replace(" ", "").replace("_", "")
        for column, regex in COL_REGEX.items():
            if re.search(regex, label, re.IGNORECASE):
                columns.append(column)
                indexes.append(i)
                break

    # Format the numerical data.
    data = np.array(reader[istart:])[:, indexes]
    data = np.char.strip(data, ' ')
    data[data == ''] = np.nan
    data = np.char.replace(data, ',', '.')
    data = data.astype('float')
    data = clean_endsof_file(data)

    # Format the data into a pandas dataframe.
    data = pd.DataFrame(data, columns=columns)
    for col in ['Year', 'Month', 'Day']:
        data[col] = data[col].astype(int)
    for col in ['Tmax', 'Tmin', 'Tavg', 'Ptot']:
        data[col] = data[col].astype(float)

    # We now create the time indexes for the dataframe form the year,
    # month, and day data.
    data = data.set_index(pd.to_datetime(dict(
        year=data['Year'], month=data['Month'], day=data['Day'])))
    data.drop(labels=['Year', 'Month', 'Day'], axis=1, inplace=True)

    # We print some comment if optional data was loaded from the file.
    if 'PET' in columns:
        print('Potential evapotranspiration imported from datafile.')
    if 'Rain' in columns:
        print('Rain data imported from datafile.')
    if 'Snow' in columns:
        print('Snow data imported from datafile.')

    return metadata, data


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
    tseg = [np.nan, xldates[0], xldates[0] + 1]
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
        hourly_df['Irradiance'][i] = float(line[0][char_offset:][20:24]) / 1000

        # Compute time in Excel numeric format :
        hourly_df['Time'][i] = xldate_from_datetime_tuple(
            (year, month, day, hour, 0, 0), 0)

    if format_to_daily:
        # Convert the hourly data to daily format.
        assert len(hourly_df['Irradiance']) % 24 == 0
        new_shape = (len(hourly_df['Irradiance']) // 24, 24)

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


# ----- Base functions: secondary variables
def calcul_rain_from_ptot(Tavg, Ptot, Tcrit=0):
    rain = Ptot.copy(deep=True)
    rain[Tavg < Tcrit] = 0

    # np.copy(Ptot)
    # rain[np.where(Tavg < Tcrit)[0]] = 0
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
    fmeteo = ("D:/Desktop/Meteo_station_1973a2019.csv")
    wxdset = WXDataFrame(fmeteo)
    data = wxdset.data

    monthly_values = wxdset.get_monthly_values()
    yearly_values = wxdset.get_yearly_values()

    monthly_normals = wxdset.get_monthly_normals()
    yearly_normals = wxdset.get_yearly_normals()

    print(monthly_normals, end='\n\n')
    print(yearly_normals)
