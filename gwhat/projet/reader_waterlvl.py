# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Standard library imports
import os
import os.path as osp
import numpy as np
import xlrd
import csv
from collections.abc import Mapping


# ---- Local library imports
from gwhat.common.utils import save_content_to_csv

FILE_EXTS = ['.csv', '.xls', '.xlsx']


# ---- Read and Load Water Level Datafiles
def open_water_level_datafile(filename):
    """Open a water level data file and return the data."""
    root, ext = os.path.splitext(filename)
    if ext not in FILE_EXTS:
        raise ValueError("Supported file format are: ", FILE_EXTS)
    else:
        print('Loading waterlvl time-series from %s file...' % ext[1:])

    if ext == '.csv':
        with open(filename, 'r', encoding='utf8') as f:
            data = list(csv.reader(f, delimiter=','))
    elif ext in ['.xls', '.xlsx']:
        with xlrd.open_workbook(filename, on_demand=True) as wb:
            sheet = wb.sheet_by_index(0)
            data = [sheet.row_values(rowx, start_colx=0, end_colx=None) for
                    rowx in range(sheet.nrows)]

    return data


def read_water_level_datafile(filename):
    """Load a water level dataset from a csv or Excel file."""
    data = open_water_level_datafile(filename)
    if data is None:
        return None

    df = {'filename': filename,
          'Well': '',
          'Well ID': '',
          'Province': '',
          'Latitude': 0,
          'Longitude': 0,
          'Elevation': 0,
          'Municipality': '',
          'Time': np.array([]),
          'WL': np.array([]),
          'BP': np.array([]),
          'ET': np.array([])}

    # ---- Read the Header
    for row, line in enumerate(data):
        if not len(line):
            continue

        try:
            label = line[0].lower().replace(":", "").replace("=", "").strip()
        except AttributeError:
            continue

        if label == 'well name':
            df['Well'] = str(line[1])
        elif label == 'well id':
            df['Well ID'] = str(line[1])
        elif label == 'province':
            df['Province'] = str(line[1])
        elif label == 'latitude':
            try:
                df['Latitude'] = float(line[1])
            except ValueError:
                print('Wrong format for entry "Latitude".')
                df['Latitude'] = 0
        elif label == 'longitude':
            try:
                df['Longitude'] = float(line[1])
            except ValueError:
                print('Wrong format for entry "Longitude".')
                df['Longitude'] = 0
        elif label in ['altitude', 'elevation']:
            try:
                df['Elevation'] = float(line[1])
            except ValueError:
                print('Wrong format for entry "Altitude".')
                df['Elevation'] = 0
        elif label == 'municipality':
            df['Municipality'] = str(line[1])
        elif label == 'date':
            column_labels = line
            break
    else:
        print("ERROR: the water level datafile is not"
              " formatted correctly.")
        return None

    # ---- Read the Data
    try:
        data = np.array(data[row+1:])
    except IndexError:
        # The file is correctly formatted but there is no data.
        return df

    # Read the water level data :
    try:
        df['Time'] = data[:, 0].astype(float)
        df['WL'] = data[:, 1].astype(float)
    except ValueError:
        print('The water level datafile is not formatted correctly')
        return None
    else:
        print('Waterlvl time-series for well %s loaded successfully.' %
              df['Well'])

    # The data are not monotically increasing in time.
    if np.min(np.diff(df['Time'])) <= 0:
        print("The data are not monotically increasing in time.")
        return None

    # Read the barometric data.
    try:
        if column_labels[2] == 'BP(m)':
            df['BP'] = data[:, 2].astype(float)
        else:
            print('No barometric data.')
    except IndexError:
        print('No barometric data.')

    # Read the Earth tides data.
    try:
        if column_labels[3] == 'ET':
            df['ET'] = data[:, 3].astype(float)
        else:
            print('No Earth tide data.')
    except IndexError:
        print('No Earth tide data.')

    return df


def make_waterlvl_continuous(t, wl):
    """
    This method produce a continuous daily water level time series.
    Missing data are filled with nan values.
    """
    print('Making water level continuous...')
    i = 1
    while i < len(t)-1:
        if t[i+1]-t[i] > 1:
            wl = np.insert(wl, i+1, np.nan, 0)
            t = np.insert(t, i+1, t[i]+1, 0)
        i += 1
    print('Making water level continuous done.')

    return t, wl


# ---- Water Level Manual Measurements
def init_waterlvl_measures(dirname):
    """
    Create an empty waterlvl_manual_measurements.csv file with headers
    if it does not already exist.
    """
    for ext in FILE_EXTS:
        fname = os.path.join(dirname, "waterlvl_manual_measurements"+ext)
        if os.path.exists(fname):
            return
    else:
        fname = os.path.join(dirname, 'waterlvl_manual_measurements.csv')
        fcontent = [['Well_ID', 'Time (days)', 'Obs. (mbgs)']]

        if not os.path.exists(dirname):
            os.makedirs(dirname)
        save_content_to_csv(fname, fcontent)


def load_waterlvl_measures(filename, well):
    """
    Load and read the water level manual measurements from the specified
    resource file for the specified well.
    """
    print('Loading manual water level measures for well %s...' % well, end=" ")
    time_mes, wl_mes = np.array([]), np.array([])
    # Determine the extension of the file.
    root, ext = os.path.splitext(filename)
    exts = [ext] if ext in FILE_EXTS else FILE_EXTS
    for ext in exts:
        filename = root+ext
        if os.path.exists(root+ext):
            break
    else:
        # The file does not exists, so we generate an empty file with
        # a header.
        print("none")
        init_waterlvl_measures(os.path.dirname(root))
        return time_mes, wl_mes

    # Open and read the file.
    if ext == '.csv':
        with open(filename, 'r') as f:
            reader = np.array(list(csv.reader(f, delimiter=',')))
            data = np.array(reader[1:])

            well_name = np.array(data[:, 0]).astype('str')
            time = np.array(data[:, 1]).astype('float')
            wl = np.array(data[:, 2]).astype('float')

    elif ext in ['.xlsx', '.xls']:
        with xlrd.open_workbook(filename) as wb:
            sheet = wb.sheet_by_index(0)

            well_name = sheet.col_values(0, start_rowx=1, end_rowx=None)
            time = sheet.col_values(1, start_rowx=1, end_rowx=None)
            wl = sheet.col_values(2, start_rowx=1, end_rowx=None)

            well_name = np.array(well_name).astype('str')
            time = np.array(time).astype('float')
            wl = np.array(wl).astype('float')

    if len(well_name) > 0:
        rowx = np.where(well_name == well)[0]
        if len(rowx) > 0:
            wl_mes = wl[rowx]
            time_mes = time[rowx]
    print("done")

    return time_mes, wl_mes


# =========================================================================


def generate_HTML_table(name, lat, lon, alt, mun):

    FIELDS = [['Well Name', name],
              ['Latitude', '%0.3f°' % lat],
              ['Longitude', '%0.3f°' % lon],
              ['Altitude', '%0.1f m' % alt],
              ['Municipality', mun]]

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


class WLDataFrameBase(Mapping):
    """
    A water level data frame base class.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dset = None
        self._undo_stack = []
        self._waterlevels = np.array([])
        self._datetimes = np.array([])

    def __load_dataset__(self):
        """Loads the dataset and save it in a store."""
        raise NotImplementedError

    def __len__(self, key):
        return len(self._datetimes)

    def __setitem__(self, key, value):
        return NotImplementedError

    def __iter__(self):
        return NotImplementedError

    # ---- Water levels
    @property
    def datetimes(self):
        return self._datetimes

    @property
    def waterlevels(self):
        return self._waterlevels

    @property
    def has_uncommited_changes(self):
        """"
        Return whether there is uncommited changes to the water level data.
        """
        return bool(len(self._undo_stack))

    def commit(self):
        """Commit the changes made to the water level data to the project."""
        raise NotImplementedError

    def undo(self):
        """Undo the last changes made to the water level data."""
        if self.has_uncommited_changes:
            change = self._undo_stack.pop(-1)
            self._waterlevels[change[0]] = change[1]

    def clear_all_changes(self):
        """
        Clear all changes that were made to the water level data since the
        last commit.
        """
        while self.has_uncommited_changes:
            self.undo()

    def delete_waterlevels_at(self, indexes):
        """Delete the water level data at the specified indexes."""
        if len(indexes):
            self._add_to_undo_stack(indexes)
            self._waterlevels[indexes] = np.nan

    def _add_to_undo_stack(self, indexes):
        """
        Store the old water level values at the specified indexes in a stack
        before changing or deleting them. This allow to undo or cancel any
        changes made to the water level data before commiting them.
        """
        if len(indexes):
            self._undo_stack.append((indexes, self.waterlevels[indexes]))


class WLDataFrame(WLDataFrameBase):
    """A water level dataset container that loads its data from a file."""

    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__load_dataset__(filename)

    def __getitem__(self, key):
        """Returns the value saved in the store at key."""
        return self.dset.__getitem__(key)

    def __load_dataset__(self, filename):
        """Loads the dataset from a file and saves it in the store."""
        self.dset = read_water_level_datafile(filename)
        self._waterlevels = self.dset['WL']
        self._datetimes = self.dset['Time']


if __name__ == "__main__":
    from gwhat import __rootdir__
    df = WLDataFrame(
        osp.join(__rootdir__, 'tests', "water_level_datafile.csv"))
    df2 = WLDataFrame(
        osp.join(__rootdir__, 'tests', "water_level_datafile.xls"))
    df3 = WLDataFrame(
        osp.join(__rootdir__, 'tests', "water_level_datafile.xlsx"))
