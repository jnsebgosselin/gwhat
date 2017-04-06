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

import os
import numpy as np
import xlrd


# =============================================================================


def load_excel_datafile(fname):
    print('Loading waterlvl time-series from Excel file...')

    book = xlrd.open_workbook(fname, on_demand=True)
    sheet = book.sheet_by_index(0)

    df = {'well': '',
          'latitude': 0,
          'longitude': 0,
          'altitude': 0,
          'municipality': '',
          'Time': np.array([]),
          'WL': np.array([]),
          'BP': np.array([]),
          'ET': np.array([])}

    # ---------------------------------------------------- Read the header ----

    header = np.array(sheet.col_values(0, start_rowx=0, end_rowx=None))

    for row, item in enumerate(header):
        if item == 'Well Name':
            df['well'] = str(sheet.cell(row, 1).value)
        elif item == 'Latitude':
            try:
                df['latitude'] = float(sheet.cell(row, 1).value)
            except:
                print('Wrong format for entry "Latitude".')
                df['latitude'] = 0
        elif item == 'Longitude':
            try:
                df['longitude'] = float(sheet.cell(row, 1).value)
            except:
                print('Wrong format for entry "Longitude".')
                df['longitude'] = 0
        elif item == 'Altitude':
            try:
                df['altitude'] = float(sheet.cell(row, 1).value)
            except:
                print('Wrong format for entry "Altitude".')
                df['altitude'] = 0
        elif item == 'Municipality':
            df['municipality'] = str(sheet.cell(row, 1).value)
        elif item == 'Date':
            break

    row += 1

    # ------------------------------------------------------ Load the Data ----

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
        book.release_resources()
        return False

    time, wl = make_waterlvl_continuous(time, wl)

    print('Waterlvl time-series for well %s loaded successfully.' % df['well'])

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

        # If dates 1 and 2 are not consecutive, add a nan row to DATA
        # after date 1.
#            dt1 = t[i]-t[i-1]
#            dt2 = t[i+1]-t[i]
#            if dt1 == dt2:
#                # sampling frequency is the same. data are continuous
#            if dt1 > dt2:
#                # sampling frequency was increased.
#            if dt1 > dt2:


#def load_waterlvl_measures(self, fname, name_well):
#
#    print('Loading waterlvl manual measures for well %s' % name_well)
#
#    WLmes, TIMEmes = [], []
#
#    if os.path.exists(fname):
#
#        # ---- Import Data ----
#
#        reader = open_workbook(fname)
#        sheet = reader.sheet_by_index(0)
#
#        NAME = sheet.col_values(0, start_rowx=1, end_rowx=None)
#        TIME = sheet.col_values(1, start_rowx=1, end_rowx=None)
#        OBS = sheet.col_values(2, start_rowx=1, end_rowx=None)
#
#        # ---- Convert to Numpy ----
#
#        NAME = np.array(NAME).astype('str')
#        TIME = np.array(TIME).astype('float')
#        OBS = np.array(OBS).astype('float')
#
#        if len(NAME) > 1:
#            rowx = np.where(NAME == name_well)[0]
#            if len(rowx) > 0:
#                WLmes = OBS[rowx]
#                TIMEmes = TIME[rowx]
#
#    self.TIMEmes = TIMEmes
#    self.WLmes = WLmes
#
#    return TIMEmes, WLmes


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
