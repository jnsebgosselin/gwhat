# -*- coding: utf-8 -*-
"""
Copyright 2014-2015 Jean-Sebastien Gosselin
email: jnsebgosselin@gmail.com

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

from calendar import monthrange
import csv
import os
from time import clock
import datetime

import numpy as np
from xlrd import xldate_as_tuple, open_workbook


class WaterlvlData():
    """
    Class that loads the water level data files.
    """

    def __init__(self):

        self.wlvlFilename = []
        self.soilFilename = []

        # --- Water Level Time Series --- #

        self.time = []  # time series in excel numeric format
        self.lvl = []   # water level in mbgs (meters below ground surface)

        # --- Well Info --- #

        self.name_well = []
        self.municipality = []
        self.well_info = []  # html table to display in the UI
        self.LAT = []
        self.LON = []
        self.ALT = []

        # --- Manual Measurements --- #

        self.WLmes = []
        self.TIMEmes = []

        # Recession :

        self.trecess = []
        self.hrecess = []
        self.A, self.B = None, None

    # =========================================================================

    def load(self, fname):

        print('Loading waterlvl time-series...')

        self.wlvlFilename = fname
        fileName, fileExtension = os.path.splitext(fname)
        self.soilFilename = fileName + '.sol'

        book = open_workbook(fname, on_demand=True)
        sheet = book.sheet_by_index(0)

        # Search for First Line With Data :

        self.time = sheet.col_values(0, start_rowx=0, end_rowx=None)
        self.time = np.array(self.time)

        row = 0
        hit = False
        while hit is False:
            if self.time[row] == 'Date':
                hit = True
            else:
                row += 1

            if row >= len(self.time):
                print('WARNING: Waterlvl data file is not formatted correctly')
                book.release_resources()
                return False

        start_rowx = row + 1

        # Load Data :

        try:
            self.time = self.time[start_rowx:]
            self.time = np.array(self.time).astype(float)

            header = sheet.col_values(1, start_rowx=0, end_rowx=5)
            self.name_well = header[0]
            self.LAT = header[1]
            self.LON = header[2]
            self.ALT = header[3]
            self.municipality = header[4]

            self.lvl = sheet.col_values(1, start_rowx=start_rowx,
                                        end_rowx=None)
            self.lvl = np.array(self.lvl).astype(float)
        except:
            print('WARNING: Waterlvl data file is not formatted correctly')
            book.release_resources()
            return False

        book.release_resources()

        self.make_waterlvl_continuous()  # Make time series continuous :
        self.generate_HTML_table()
        self.load_interpretation_file()

        print('Waterlvl time-series for well %s loaded.' % self.name_well)

        return True

    def load_waterlvl_measures(self, fname, name_well):

        print('Loading waterlvl manual measures for well %s' % name_well)

        WLmes, TIMEmes = [], []

        if os.path.exists(fname):

            # ---- Import Data ----

            reader = open_workbook(fname)
            sheet = reader.sheet_by_index(0)

            NAME = sheet.col_values(0, start_rowx=1, end_rowx=None)
            TIME = sheet.col_values(1, start_rowx=1, end_rowx=None)
            OBS = sheet.col_values(2, start_rowx=1, end_rowx=None)

            # ---- Convert to Numpy ----

            NAME = np.array(NAME).astype('str')
            TIME = np.array(TIME).astype('float')
            OBS = np.array(OBS).astype('float')

            if len(NAME) > 1:
                rowx = np.where(NAME == name_well)[0]
                if len(rowx) > 0:
                    WLmes = OBS[rowx]
                    TIMEmes = TIME[rowx]

        self.TIMEmes = TIMEmes
        self.WLmes = WLmes

        return TIMEmes, WLmes

    def load_interpretation_file(self):

        # ---- Check if file exists ----

        wifname = os.path.splitext(self.wlvlFilename)[0] + '.wif'
        if not os.path.exists(wifname):
            print('%s does not exist' % wifname)
            return False

        # ---- Open File ----

        with open(wifname, 'r') as f:
            reader = list(csv.reader(f, delimiter='\t'))

        # ---- Find Recess Data ----

        row = 0
        while True:
            if row >= len(reader):
                print('Something is wrong with the .wif file.')
                return False

            try:
                if reader[row][0] == 'Time':
                    break
                elif reader[row][0] == 'A (1/d) :':
                    self.A = float(reader[row][1])
                elif reader[row][0] == 'B (m/d) :':
                    self.B = float(reader[row][1])
            except IndexError:
                pass

            row += 1
        row += 1

        # ---- Save Data in Class Attributes ----

        dat = np.array(reader[row:]).astype('float')
        self.trecess = dat[:, 0]
        self.hrecess = dat[:, 1]

        return True

    # =========================================================================

    def make_waterlvl_continuous(self):
        # This method produce a continuous daily water level time series.
        # Missing data are filled with NaN values.

        print('Making water level continuous...')
        t = self.time
        w = self.lvl

        i = 1
        while i < len(t) - 1:
            # If dates 1 and 2 are not consecutive, add a nan row to DATA
            # after date 1.
#            dt1 = t[i]-t[i-1]
#            dt2 = t[i+1]-t[i]
#            if dt1 == dt2:
#                # sampling frequency is the same. data are continuous
#            if dt1 > dt2:
#                # sampling frequency was increased.
#            if dt1 > dt2:

            if t[i+1] - t[i] > 1:
                w = np.insert(w, i+1, np.nan, 0)
                t = np.insert(t, i+1, t[i]+1, 0)
            i += 1
        print('Making water level continuous done.')

        self.time = t
        self.lvl = w

    # =========================================================================

    def generate_HTML_table(self):

        FIELDS = [['Well Name', self.name_well],
                  ['Latitude', self.LAT],
                  ['Longitude', self.LON],
                  ['Altitude', self.ALT],
                  ['Municipality', self.municipality]]

        well_info = '''
                    <table border="0" cellpadding="2" cellspacing="0"
                    align="left">
                    '''

        for row in range(len(FIELDS)):

             try:
                 VAL = '%0.2f' % float(FIELDS[row][1])
             except:
                 VAL = FIELDS[row][1]

             well_info += '''
                          <tr>
                            <td width=10></td>
                            <td align="left">%s</td>
                            <td align="left" width=20>:</td>
                            <td align="left">%s</td>
                          </tr>
                          ''' % (FIELDS[row][0], VAL)
        well_info += '</table>'

        self.well_info = well_info

        return well_info


if __name__ == '__main__':

    # ---- Pont-Rouge ----

    filename = '../Projects/Pont-Rouge/Water Levels/5080001.xls'

    # ---- IDM ----

    dirname = '../Projects/IDM/'
    fname = os.path.join(dirname, 'Water Levels', 'Boisville.xls')

    waterlvldata = WaterlvlData()
    waterlvldata.load(fname)
