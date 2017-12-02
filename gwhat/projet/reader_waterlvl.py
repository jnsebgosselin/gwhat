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

import os
import numpy as np
import xlrd
import csv

# ---- Imports: local
from gwhat.common.utils import save_content_to_csv

FILE_EXTS = ['.csv', '.xls', '.xlsx']


def load_excel_datafile(fname):
    print('Loading waterlvl time-series from Excel file...')

    with xlrd.open_workbook(fname, on_demand=True) as wb:
        sheet = wb.sheet_by_index(0)

        df = {'filename': fname,
              'Well': '',
              'Latitude': 0,
              'Longitude': 0,
              'Elevation': 0,
              'Municipality': '',
              'Time': np.array([]),
              'WL': np.array([]),
              'BP': np.array([]),
              'ET': np.array([])}

        # ---------------------------------------------------- Read header ----

        header = np.array(sheet.col_values(0, start_rowx=0, end_rowx=None))

        for row, item in enumerate(header):
            if item == 'Well Name':
                df['Well'] = str(sheet.cell(row, 1).value)
            elif item == 'Latitude':
                try:
                    df['Latitude'] = float(sheet.cell(row, 1).value)
                except:
                    print('Wrong format for entry "Latitude".')
                    df['Latitude'] = 0
            elif item == 'Longitude':
                try:
                    df['Longitude'] = float(sheet.cell(row, 1).value)
                except:
                    print('Wrong format for entry "Longitude".')
                    df['Longitude'] = 0
            elif item == 'Altitude':
                try:
                    df['Elevation'] = float(sheet.cell(row, 1).value)
                except:
                    print('Wrong format for entry "Altitude".')
                    df['Elevation'] = 0
            elif item == 'Municipality':
                df['Municipality'] = str(sheet.cell(row, 1).value)
            elif item == 'Date':
                break

        row += 1

        # ------------------------------------------------------ Read Data ----

        # ---- Water Level ----

        try:
            time = sheet.col_values(0, start_rowx=row, end_rowx=None)
            time = np.array(time).astype(float)
            df['Time'] = time

            wl = sheet.col_values(1, start_rowx=row, end_rowx=None)
            wl = np.array(wl).astype(float)
            df['WL'] = wl
        except:
            print('WARNING: Waterlvl data file is not formatted correctly')
            return None

        print('Waterlvl time-series for well %s loaded successfully.' %
              df['Well'])

        # ---- Barometric data ----

        try:
            if sheet.cell(row-1, 2).value == 'BP(m)':
                bp = sheet.col_values(2, start_rowx=row, end_rowx=None)
                bp = np.array(bp).astype(float)
                df['BP'] = bp
            else:
                print('No barometric data.')
        except:
            print('No barometric data.')

        # ---- Earth Tide ----

        try:
            if sheet.cell(row-1, 3).value == 'ET':
                et = sheet.col_values(3, start_rowx=row, end_rowx=None)
                et = np.array(et).astype(float)
                df['ET'] = et
            else:
                print('No Earth tide data.')
        except:
            print('No Earth tide data.')

    return df


# =============================================================================


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


# ---- Water level manual measurements

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
