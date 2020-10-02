# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------


# ---- Standard library imports
import csv
import datetime as dt
import os
import os.path as osp
import re
from time import strftime
from collections import OrderedDict
from collections.abc import Mapping
from abc import abstractmethod

# ---- Third party imports
import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError
import xlrd
from xlrd.xldate import xldate_as_datetime

# ---- Local library imports
from gwhat.meteo.evapotranspiration import calcul_thornthwaite
from gwhat.common.utils import save_content_to_file
from gwhat.utils.math import nan_as_text_tolist
from gwhat import __namever__


PRECIP_VARIABLES = ['Ptot', 'Rain', 'Snow']
TEMP_VARIABLES = ['Tmax', 'Tavg', 'Tmin', 'PET']
METEO_VARIABLES = PRECIP_VARIABLES + TEMP_VARIABLES
VARLABELS_MAP = {'Ptot': 'Ptot (mm)',
                 'Rain': 'Rain (mm)',
                 'Snow': 'Snow (mm)',
                 'Tmax': 'Tmax (\u00B0C)',
                 'Tavg': 'Tavg (\u00B0C)',
                 'Tmin': 'Tmin (\u00B0C)',
                 'PET': 'PET (mm)'}
FILE_EXTS = ['.out', '.csv', '.xls', '.xlsx']


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
        self.missing_value_indexes = {
            var: pd.DatetimeIndex([]) for var in METEO_VARIABLES}

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
            data = self.data.copy()
            data.insert(0, 'Year', data.index.year)
            data.insert(1, 'Month', data.index.month)
            data.insert(2, 'Day', data.index.day)
        elif time_frame == 'monthly':
            data = self.get_monthly_values()
            data.insert(0, 'Year', data.index.get_level_values(0))
            data.insert(1, 'Month', data.index.get_level_values(1))
        elif time_frame == 'yearly':
            data = self.get_yearly_values()
            data.insert(0, 'Year', data.index)
        else:
            raise ValueError('"time_frame" must be either "yearly", "monthly"'
                             ' or "daily".')

        fcontent = [['Station Name', self.metadata['Station Name']],
                    ['Station ID', self.metadata['Station ID']],
                    ['Location', self.metadata['Location']],
                    ['Latitude (\u00B0)', self.metadata['Latitude']],
                    ['Longitude (\u00B0)', self.metadata['Longitude']],
                    ['Elevation (m)', self.metadata['Elevation']],
                    ['', ''],
                    ['Start Date ', self.data.index[0].strftime("%Y-%m-%d")],
                    ['End Date ', self.data.index[-1].strftime("%Y-%m-%d")],
                    ['', ''],
                    ['Created by', __namever__],
                    ['Created on', strftime("%Y-%m-%d")],
                    ['', '']
                    ]
        fcontent.append(
            [VARLABELS_MAP.get(col, col) for col in data.columns])
        fcontent.extend(nan_as_text_tolist(data.values))
        save_content_to_file(filename, fcontent)

    def get_data_period(self):
        """
        Return the year range for which data are available for this
        dataset.
        """
        return (self.data.index.min().year, self.data.index.max().year)

    def get_xldates(self):
        """
        Return a numpy array containing the Excel numerical dates
        corresponding to the dates of the dataset.
        """
        timedeltas = self.data.index - xldate_as_datetime(4000, 0)
        xldates = timedeltas.total_seconds() / (3600 * 24) + 4000
        return xldates.values

    # ---- utilities
    def strftime(self):
        """
        Return a list of formatted strings corresponding to the datetime
        indexes of this dataset.
        """
        return self.data.index.strftime("%Y-%m-%dT%H:%M:%S").values.tolist()

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
    def get_monthly_normals(self, year_range=None):
        """
        Return the monthly normals for the weather variables saved in this
        data frame.
        """
        df = self.get_monthly_values()
        if year_range:
            df = df.loc[(df.index.get_level_values(0) >= year_range[0]) &
                        (df.index.get_level_values(0) <= year_range[1])]
        df = df.groupby(level=[1]).mean()
        df.index.rename('Month', inplace=True)
        return df

    def get_yearly_normals(self, year_range=None):
        """
        Return the yearly normals for the weather variables saved in this
        data frame.
        """
        df = self.get_yearly_values()
        if year_range:
            df = df.loc[(df.index >= year_range[0]) &
                        (df.index <= year_range[1])]
        return df.mean()


class WXDataFrame(WXDataFrameBase):
    """A daily weather dataset container that loads its data from a file."""

    def __init__(self, filename, *args, **kwargs):
        super(WXDataFrame, self).__init__(*args, **kwargs)
        self.__load_dataset__(filename)

    def __getitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return self.data.__str__()

    def __load_dataset__(self, filename):
        """Loads the dataset from a file and saves it in the store."""
        print('-' * 78)
        print('Reading weather data from "%s"...' % os.path.basename(filename))

        # Import data.
        self.metadata, self.data = read_weather_datafile(filename)

        # Import the missing data log if it exist.
        root, ext = osp.splitext(filename)
        finfo = root + '.log'
        if os.path.exists(finfo):
            print('Reading gapfill data from "%s"...' % osp.basename(finfo))
            var_labels = [('Tmax', 'Max Temp (deg C)'),
                          ('Tmin', 'Min Temp (deg C)'),
                          ('Tavg', 'Mean Temp (deg C)'),
                          ('Ptot', 'Total Precip (mm)')]
            for var, label in var_labels:
                self.missing_value_indexes[var] = (
                    self.missing_value_indexes[var]
                    .append(load_weather_log(finfo, label))
                    .drop_duplicates()
                    )

        # Make the daily time series continuous.
        self.data = self.data.resample('1D').asfreq()

        # Store the time indexes where data are missing.
        for var in METEO_VARIABLES:
            if var in self.data.columns:
                self.missing_value_indexes[var] = (
                    self.missing_value_indexes[var]
                    .append(self.data.index[pd.isnull(self.data[var])])
                    .drop_duplicates())

        # Fill missing with values with in-stations linear interpolation for
        # temperature based variables.
        for var in ['Tmax', 'Tavg', 'Tmin', 'PET']:
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


def read_weather_datafile(filename):
    """
    Read the weather data from the provided filename.

    Parameters
    ----------
    filename : str
        The absolute path of an input weather data file.
    """
    metadata = {'filename': filename,
                'Station Name': '',
                'Station ID': '',
                'Location': '',
                'Latitude': 0,
                'Longitude': 0,
                'Elevation': 0}

    # Read the file.
    root, ext = osp.splitext(filename)
    if ext == '.csv':
        with open(filename, 'r') as csvfile:
            data = list(csv.reader(csvfile, delimiter=','))
    elif ext in ['.xls', '.xlsx']:
        data = pd.read_excel(filename, dtype='str', header=None)
        data = data.values.tolist()
    else:
        raise ValueError("Supported file format are: ",
                         ['.csv', '.xls', '.xlsx'])

    # Read the metadata and try to find the row where the
    # numerical data begin.
    header_regex_type = {
        'Station Name': (r'(stationname|name)', str),
        'Station ID': (r'(stationid|id|climateidentifier)', str),
        'Latitude': (r'(latitude)', float),
        'Longitude': (r'(longitude)', float),
        'Location': (r'(location|province)', str),
        'Elevation': (r'(elevation|altitude)', float)}
    for i, row in enumerate(data):
        if len(row) == 0 or pd.isnull(row[0]):
            continue

        label = row[0].replace(" ", "").replace("_", "")
        for key, (regex, dtype) in header_regex_type.items():
            if re.search(regex, label, re.IGNORECASE):
                try:
                    metadata[key] = dtype(row[1])
                except ValueError:
                    print("Wrong format for entry '{}'.".format(key))
                else:
                    break
        else:
            if re.search(r'(year)', label, re.IGNORECASE):
                break
    else:
        raise ValueError("Cannot find the beginning of the data.")

    # Extract and format the numerical data from the file.
    data = pd.DataFrame(data[i + 1:], columns=data[i])
    data = data.replace(r'(?i)^\s*$|nan|none', np.nan, regex=True)

    # The data must contain the following columns :
    # (1) Tmax, (2) Tavg, (3) Tmin, (4) Ptot.
    # The dataframe can also have these optional columns:
    # (5) Rain, (6) Snow, (7) PET
    # The dataframe must use a datetime index.

    column_names_regexes = OrderedDict([
        ('Year', r'(year)'),
        ('Month', r'(month)'),
        ('Day', r'(day)'),
        ('Tmax', r'(maxtemp)'),
        ('Tmin', r'(mintemp)'),
        ('Tavg', r'(meantemp)'),
        ('Ptot', r'(totalprecip)'),
        ('PET', r'(etp|evapo)'),
        ('Rain', r'(rain)'),
        ('Snow', r'(snow)')])
    for i, column in enumerate(data.columns):
        column_ = column.replace(" ", "").replace("_", "")
        for key, regex in column_names_regexes.items():
            if re.search(regex, column_, re.IGNORECASE):
                data = data.rename(columns={column: key})
                break
        else:
            data = data.drop([column], axis=1)

    for col in data.columns:
        try:
            data[col] = pd.to_numeric(data[col])
        except ValueError:
            data[col] = pd.to_numeric(data[col], errors='coerce')
            print("Some {} data could not be converted to numeric value"
                  .format(col))

    # We now create the time indexes for the dataframe form the year,
    # month, and day data.
    data = data.set_index(pd.to_datetime(dict(
        year=data['Year'], month=data['Month'], day=data['Day'])))
    data = data.drop(labels=['Year', 'Month', 'Day'], axis=1)
    data.index.names = ['Datetime']

    # We print some comment if optional data was loaded from the file.
    if 'PET' in data.columns:
        print('Potential evapotranspiration imported from datafile.')
    if 'Rain' in data.columns:
        print('Rain data imported from datafile.')
    if 'Snow' in data.columns:
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
    datetimes = []
    for i in range(len(reader)):
        if reader[i][0] == varname:
            year = int(float(reader[i][1]))
            month = int(float(reader[i][2]))
            day = int(float(reader[i][3]))
            datetimes.append(dt.datetime(year, month, day))
    return pd.DatetimeIndex(datetimes)


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
    fmeteo = ("C:/Users/User/gwhat/gwhat/meteo/tests/"
              "basic_weather_datafile.csv")
    metadata, data = read_weather_datafile(fmeteo)

    fmeteo = ("C:/Users/User/gwhat/gwhat/meteo/tests/"
              "sample_weather_datafile.xlsx")
    metadata2, data2 = read_weather_datafile(fmeteo)

    # wxdset = WXDataFrame(fmeteo)
    # data = wxdset.data

    # monthly_values = wxdset.get_monthly_values()
    # yearly_values = wxdset.get_yearly_values()

    # monthly_normals = wxdset.get_monthly_normals()
    # yearly_normals = wxdset.get_yearly_normals()

    # print(monthly_normals, end='\n\n')
    # print(yearly_normals)
