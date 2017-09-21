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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Standard library imports :
import os
import csv

# Third party imports :
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple
import pandas as pd
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QApplication, QGridLayout,
                             QLabel, QPushButton, QCheckBox, QLineEdit,
                             QFileDialog)

# Local imports :

from common import IconDB, QToolButtonSmall
from meteo.weather_reader import read_weather_datafile


def merge_datafiles(datafiles, mode='overwrite'):
    # mode can be either 'overwrite' or 'average'
    global dset1, dset2, dset12

    dset1 = pd.DataFrame.from_dict(datafiles[0])
    dset1.index = dset1.Time

    dset2 = pd.DataFrame.from_dict(datafiles[1])
    dset2.index = dset2.Time

    dset12 = dset1.combine_first(dset2)

#    df['Tmax'] = data[:, var.index('Max Temp (deg C)')]
#    df['Tmin'] = data[:, var.index('Min Temp (deg C)')]
#    df['Tavg'] = data[:, var.index('Mean Temp (deg C)')]
#    df['Ptot'] = data[:, var.index('Total Precip (mm)')]


class WXDataMerger(object):
    """Base class to read and merge input weather datafiles."""

    def __init__(self):

        self.data = []        # Weather data
        self.DATE = []        # Date in tuple format [YEAR, MONTH, DAY]

        self.time = []        # Date in numeric format
        self.time_start = []
        self.time_end = []

        self.DATE_START = []  # Date on which the data record begins
        self.DATE_END = []    # Date on which data record ends

        self.names = []     # Station names
        self.ALT = []         # Station elevation in m
        self.LAT = []         # Station latitude in decimal degree
        self.LON = []         # Station longitude in decimal degree
        self.VARNAME = []     # Names of the meteorological variables
        self.ClimateID = []   # Climate Identifiers of weather station
        self.provinces = []    # Provinces where weater station are located

        self.NUMMISS = []     # Number of missing data
        self.fnames = []

    def load_and_format_data(self, pathlist):
        self.fnames = [os.path.basename(p) for p in pathlist]
        nSTA = len(pathlist)
        if nSTA == 0:
            # Reset the states of all class variables and return.
            self.names = []
            self.ALT = []
            self.LAT = []
            self.LON = []
            self.provinces = []
            self.ClimateID = []
            self.DATE_START = []
            self.DATE_END = []

            return False
        else:
            self.names = np.zeros(nSTA).astype('str')
            self.ALT = np.zeros(nSTA)
            self.LAT = np.zeros(nSTA)
            self.LON = np.zeros(nSTA)
            self.provinces = np.zeros(nSTA).astype('str')
            self.ClimateID = np.zeros(nSTA).astype('str')
            self.DATE_START = np.zeros((nSTA, 3)).astype('int')
            self.DATE_END = np.zeros((nSTA, 3)).astype('int')

        date_flag = False
        # If date_flag becomes True, a new DATE matrix will be rebuilt at the
        # end of this routine.

        wxdsets = []
        for i, path in enumerate(pathlist):
            wxdsets.append(read_weather_datafile(path))

            time = np.hstack([df['Time'] for df in wxdsets])
            time = np.unique(time)
            time = np.sort(time)
            
        return time
            
#            # -------------------------------------- Time continuity check ----
#
#            # Check if data are continuous over time. If not, the serie will be
#            # made continuous and the gaps will be filled with nan values.
#
#            time = wxdset['Time']
#            
#            # Sort time ascending
#
#            # ----------------------------------------- FIRST TIME ROUTINE ----
#
#            if i == 0:
#                self.VARNAME = reader[7][3:]
#                nVAR = len(self.VARNAME)
#                self.time = np.copy(time_new)
#                self.data = np.zeros((len(STADAT[:, 0]), nSTA, nVAR)) * np.nan
#                self.DATE = STADAT[:, :3]
#                self.NUMMISS = np.zeros((nSTA, nVAR)).astype('int')
#
#            # ---------------------------------- <DATA> & <TIME> RESHAPING ----
#
#            # Merge the data time series using time as index.
#
#            if self.time[0] <= time_new[0]:
#                if self.time[-1] >= time_new[-1]:
#
#                    #    [---------------]    self.time
#                    #         [-----]         time_new
#
#                    pass
#
#                else:
#
#                    #    [--------------]         self.time
#                    #         [--------------]    time_new
#                    #
#                    #           OR
#                    #
#                    #    [--------------]           self.time
#                    #                     [----]    time_new
#
#                    date_flag = True
#
#                    # Expand <DATA> and <TIME> to fit the new data serie
#
#                    EXPND = np.zeros((int(time_new[-1]-self.time[-1]),
#                                      nSTA,
#                                      nVAR)) * np.nan
#
#                    self.data = np.vstack((self.data, EXPND))
#                    self.time = np.arange(self.time[0], time_new[-1] + 1)
#
#            elif self.time[0] > time_new[0]:
#                if self.time[-1] >= time_new[-1]:
#
#                    #        [----------]    self.time
#                    #    [----------]        time_new
#                    #
#                    #            OR
#                    #           [----------]    self.time
#                    #    [----]                 time_new
#
#                    date_flag = True
#
#                    # Expand <DATA> and <TIME> to fit the new data serie
#
#                    EXPND = np.zeros((int(self.time[0]-time_new[0]),
#                                      nSTA,
#                                      nVAR)) * np.nan
#
#                    self.data = np.vstack((EXPND, self.data))
#                    self.time = np.arange(time_new[0], self.time[-1] + 1)
#                else:
#
#                    #        [----------]        self.time
#                    #    [------------------]    time_new
#
#                    date_flag = True
#
#                    # Expand <DATA> and <TIME> to fit the new data serie
#
#                    EXPNDbeg = np.zeros((int(self.time[0]-time_new[0]),
#                                         nSTA,
#                                         nVAR)) * np.nan
#
#                    EXPNDend = np.zeros((int(time_new[-1]-self.time[-1]),
#                                         nSTA,
#                                         nVAR)) * np.nan
#
#                    self.data = np.vstack((EXPNDbeg, self.data, EXPNDend))
#
#                    self.time = np.copy(time_new)
#
#            ifirst = np.where(self.time == time_new[0])[0][0]
#            ilast = np.where(self.time == time_new[-1])[0][0]
#            self.data[ifirst:ilast+1, i, :] = STADAT[:, 3:]
#
#            # --------------------------------------------------- Other Info --
#
#            # Nbr. of Missing Data :
#
#            isnan = np.isnan(STADAT[:, 3:])
#            self.NUMMISS[i, :] = np.sum(isnan, axis=0)
#
#            # station name :
#
#            # Check if a station with this name already exist in the list.
#            # If so, a number at the end of the name is added so it is
#            # possible to differentiate them in the list.
#
#            isNameExist = np.where(reader[0][1] == self.names)[0]
#            if len(isNameExist) > 0:
#
#                msg = ('Station name %s already exists. '
#                       'Added a number at the end.') % reader[0][1]
#                print(msg)
#
#                count = 1
#                while len(isNameExist) > 0:
#                    newname = '%s (%d)' % (reader[0][1], count)
#                    isNameExist = np.where(newname == self.names)[0]
#                    count += 1
#
#                self.names[i] = newname
#
#            else:
#                self.names[i] = reader[0][1]
#
#            # Other station info :
#
#            self.provinces[i] = str(reader[1][1])
#            self.LAT[i] = float(reader[2][1])
#            self.LON[i] = float(reader[3][1])
#            self.ALT[i] = float(reader[4][1])
#            self.ClimateID[i] = str(reader[5][1])
#
#        # ------------------------------------ Sort Station Alphabetically ----
#
#        sort_index = np.argsort(self.names)
#
#        self.data = self.data[:, sort_index, :]
#        self.names = self.names[sort_index]
#        self.provinces = self.provinces[sort_index]
#        self.LAT = self.LAT[sort_index]
#        self.LON = self.LON[sort_index]
#        self.ALT = self.ALT[sort_index]
#        self.ClimateID = self.ClimateID[sort_index]
#
#        self.NUMMISS = self.NUMMISS[sort_index, :]
#        self.DATE_START = self.DATE_START[sort_index]
#        self.DATE_END = self.DATE_END[sort_index]
#
#        self.fnames = self.fnames[sort_index]
#
#        # -------------------------------------------- Generate Date serie ----
#
#        # Rebuild a date matrix if <DATA> size changed. Otherwise, do nothing
#        # and keep *Date* as is.
#
#        if date_flag is True:
#            self.DATE = np.zeros((len(self.time), 3))
#            for i in range(len(self.time)):
#                date_tuple = xldate_as_tuple(self.time[i], 0)
#                self.DATE[i, 0] = date_tuple[0]
#                self.DATE[i, 1] = date_tuple[1]
#                self.DATE[i, 2] = date_tuple[2]
#
#        return True
#
#    # =========================================================================
#
#    def make_timeserie_continuous(self, DATA):
#        # scan the entire time serie and will insert a row with nan values
#        # whenever there is a gap in the data and will return the continuous
#        # data set.
#        #
#        # DATA = [YEAR, MONTH, DAY, VAR1, VAR2 ... VARn]
#        #
#        # 2D matrix containing the dates and the corresponding daily
#        # meteorological data of a given weather station arranged in
#        # chronological order.
#
#        nVAR = len(DATA[0, :]) - 3  # number of meteorological variables
#        nan2insert = np.zeros(nVAR) * np.nan
#
#        i = 0
#        date1 = xldate_from_date_tuple((DATA[i, 0].astype('int'),
#                                        DATA[i, 1].astype('int'),
#                                        DATA[i, 2].astype('int')), 0)
#
#        while i < len(DATA[:, 0]) - 1:
#            date2 = xldate_from_date_tuple((DATA[i+1, 0].astype('int'),
#                                            DATA[i+1, 1].astype('int'),
#                                            DATA[i+1, 2].astype('int')), 0)
#
#            # If dates 1 and 2 are not consecutive, add a nan row to DATA
#            # after date 1.
#            if date2 - date1 > 1:
#                date2insert = np.array(xldate_as_tuple(date1 + 1, 0))[:3]
#                row2insert = np.append(date2insert, nan2insert)
#                DATA = np.insert(DATA, i + 1, row2insert, 0)
#
#            date1 += 1
#            i += 1
#
#        return DATA


class WXDataMergerWidget(QDialog):

    def __init__(self, wxdset=None, parent=None):
        super(WXDataMergerWidget, self).__init__(parent)

        self.setModal(False)
        self.setWindowFlags(Qt.CustomizeWindowHint |
                            Qt.WindowCloseButtonHint)

        self.setWindowTitle('Merge dataset')
        self.setWindowIcon(IconDB().master)
        self._workdir = os.getcwd()
        self.wxdsets = {}

        self.__initUI__()

    def __initUI__(self):

        # ---- Toolbar ----

        btn_merge = QPushButton('Merge')
        btn_merge.clicked.connect(self.btn_merge_isClicked)
        btn_cancel = QPushButton('Close')
        btn_cancel.clicked.connect(self.close)

        toolbar = QGridLayout()
        toolbar.addWidget(btn_merge, 0, 1)
        toolbar.addWidget(btn_cancel, 0, 2)
        toolbar.setColumnStretch(0, 100)
        toolbar.setContentsMargins(0, 25, 0, 0)  # (L, T, R, B)

        # ---- Central Widget ----

        self._file_path1 = QLineEdit()
        self._file_path1.setReadOnly(True)
        lbl_get_file1 = QLabel("Select a first dataset :")
        btn_get_file1 = QToolButtonSmall(IconDB().openFile)
        btn_get_file1.file_path = self._file_path1
        btn_get_file1.clicked.connect(self.set_first_filepath)

        self._file_path2 = QLineEdit()
        self._file_path2.setReadOnly(True)
        lbl_get_file2 = QLabel("Select a second dataset :")
        btn_get_file2 = QToolButtonSmall(IconDB().openFile)
        btn_get_file2.file_path = self._file_path2
        btn_get_file2.clicked.connect(self.set_second_filepath)

        lbl_wxdset3 = QLabel("Enter a name for the resulting dataset :")
        wxdset3 = QLineEdit()

        qchckbox = QCheckBox(
                "Delete both original input datafiles after merging.")
        qchckbox.setCheckState(Qt.Checked)

        # ---- Setup Layout ----

        # Place widgets for file #1.
        central_layout = QGridLayout()
        row = 0
        central_layout.addWidget(lbl_get_file1, row, 0, 1, 2)
        row += 1
        central_layout.addWidget(self._file_path1, row, 0)
        central_layout.addWidget(btn_get_file1, row, 1)
        row += 1
        central_layout.setRowMinimumHeight(row, 15)
        row += 1
        # Place widgets for file #2.
        central_layout.addWidget(lbl_get_file2, row, 0, 1, 2)
        row += 1
        central_layout.addWidget(self._file_path2, row, 0)
        central_layout.addWidget(btn_get_file2, row, 1)
        row += 1
        central_layout.setRowMinimumHeight(row, 15)
        row += 1
        # Place widgets for concatenated file.
        central_layout.addWidget(lbl_wxdset3, row, 0, 1, 2)
        row += 1
        central_layout.addWidget(wxdset3, row, 0, 1, 2)
        row += 1
        central_layout.setRowMinimumHeight(row, 15)
        row += 1
        central_layout.addWidget(qchckbox, row, 0, 1, 2)
        central_layout.setColumnStretch(1, 100)

        # ---- Self Layout ----

        layout = QGridLayout(self)
        layout.addLayout(central_layout, 0, 0)
        layout.addLayout(toolbar, 1, 0)

    def set_first_filepath(self, fpath=None):
        if fpath is None:
            fpath = self.get_filepath()
        if fpath:
            self._file_path1.setText(fpath)
            self.wxdsets['file1'] = read_weather_datafile(fpath)

    def set_second_filepath(self, fpath=None):
        if fpath is None:
            fpath = self.get_filepath()
        if fpath:
            self._file_path2.setText(fpath)
            self.wxdsets['file2'] = read_weather_datafile(fpath)

    def get_filepath(self):
        fpath, ftype = QFileDialog.getOpenFileName(
                self, 'Select a valid weather data file', self._workdir,
                '*.csv')
        return fpath

    def set_workdir(self, dirname):
        if os.path.exists(dirname):
            self._workdir = dirname

    def btn_merge_isClicked(self):
        if len(self.wxdsets) >= 2:
            merge_datafiles(list(self.wxdsets.values()))
        self.close()

    def show(self):
        super(WXDataMergerWidget, self).show()
        self.setFixedSize(self.size())


if __name__ == '__main__':                                   # pragma: no cover
    wxdata_merger = WXDataMerger()

    workdir = os.path.join("..", "tests", "@ new-prô'jèt!", "Meteo", "Input")
    file1 = os.path.join(workdir, "IBERVILLE (7023270)_2000-2010.csv")
    file2 = os.path.join(workdir, "L'ACADIE (702LED4)_2000-2010.csv")

    time = wxdata_merger.load_and_format_data([file1, file2])
    
    
    
    
#    import platform
#    import sys

#    app = QApplication(sys.argv)

#    if platform.system() == 'Windows':
#        app.setFont(QFont('Segoe UI', 11))
#    elif platform.system() == 'Linux':
#        app.setFont(QFont('Ubuntu', 11))





    # wxdata_merger.set_workdir(workdir)
#    wxdata_merger.set_first_filepath(file1)
#    wxdata_merger.set_second_filepath(file1)
#    wxdata_merger.show()

#    sys.exit(app.exec_())
