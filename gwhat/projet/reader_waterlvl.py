# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

import os
import numpy as np
import xlrd
import csv


# ---- Imports: local

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
        if len(line) == 0:
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

    # Read the barometric data

    try:
        if column_labels[2] == 'BP(m)':
            df['BP'] = data[:, 2].astype(float)
        else:
            print('No barometric data.')
    except:
        print('No barometric data.')

    # Read the earth tide data :

    try:
        if column_labels[3] == 'ET':
            df['ET'] = data[:, 3].astype(float)
        else:
            print('No Earth tide data.')
    except:
        print('No Earth tide data.')

    return df


def make_waterlvl_continuous(t, wl):
    # This method produce a continuous daily water level time series.
    # Missing data are filled with nan values.

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


# ---- if __name__ == "__main__"

if __name__ == "__main__":
    df = read_water_level_datafile("PO01_15min.xlsx")
    df2 = read_water_level_datafile("PO01_15min.xls")
    df3 = read_water_level_datafile("PO01_15min.csv")
