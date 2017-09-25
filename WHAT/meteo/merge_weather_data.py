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
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QApplication, QGridLayout,
                             QLabel, QPushButton, QCheckBox, QLineEdit,
                             QFileDialog)

# Local imports :

from common import IconDB, QToolButtonSmall
from meteo.weather_reader import read_weather_datafile


class WXDataMerger(dict):
    """Base class to read and merge input weather datafiles."""

    def __init__(self, filepaths=None, delete_files=False):
        super(WXDataMerger, self).__init__()
        self.__init_attrs__()
        self.setDeleteInputFiles(delete_files)
        if filepaths:
            self.load_and_format_data(filepaths)

    def deleteInpuFiles(self):
        """
        Return whether the input weather data files are deleted after saving
        the combined weather dataset to a file. This option is False by
        default.
        """
        return self.__delete_input_files

    def setDeleteInputFiles(self, state):
        """
        Set whether the input weather data file are deleted after saving the
        combined weather dataset to a file.
        """
        self.__delete_input_files = bool(state)

    def __init_attrs__(self):
        self._filepaths = []
        self._station_names = []
        self._provinces = []
        self._latitudes = []
        self._longitudes = []
        self._elevations = []
        self._climate_ids = []

        self['Station Name'] = None
        self['Province'] = None
        self['Latitude'] = None
        self['Longitude'] = None
        self['Elevation'] = None
        self['Climate Identifier'] = None
        self['Minimum Year'] = None
        self['Maximum Year'] = None

        self['Time'] = np.array([])
        self['Year'] = np.array([])
        self['Month'] = np.array([])
        self['Day'] = np.array([])
        self['Tmax'] = np.array([])
        self['Tavg'] = np.array([])
        self['Tmin'] = np.array([])
        self['Ptot'] = np.array([])
        self['Combined Dataset'] = None

    def load_and_format_data(self, filepaths):
        wxdsets = []
        for i, file in enumerate(filepaths):
            wxdsets.append(read_weather_datafile(file))

            self._filepaths.append(file)
            self._station_names.append(wxdsets[-1]['Station Name'])
            self._provinces.append(wxdsets[-1]['Province'])
            self._latitudes.append(wxdsets[-1]['Latitude'])
            self._longitudes.append(wxdsets[-1]['Longitude'])
            self._elevations.append(wxdsets[-1]['Elevation'])
            self._climate_ids.append(wxdsets[-1]['Climate Identifier'])

        # Header info of the combined dataframe are automatically set to
        # those of the first datafile that was opened.
        self['Station Name'] = self._station_names[0]
        self['Province'] = self._provinces[0]
        self['Latitude'] = self._latitudes[0]
        self['Longitude'] = self._longitudes[0]
        self['Elevation'] = self._elevations[0]
        self['Climate Identifier'] = self._climate_ids[0]

        # Combine the time arrays from all datasets.
        time = np.hstack([df['Time'] for df in wxdsets])
        time = np.unique(time)
        time = np.sort(time)
        self['Time'] = time

        # Using time as the index, combine the datasets for all
        # relevant weather variables.
        keys = ['Tmin', 'Tavg', 'Tmax', 'Ptot', 'Year', 'Month', 'Day']
        for key in keys:
            data_stack = np.zeros((len(time), len(wxdsets))) * np.nan
            for i, wxdset in enumerate(wxdsets):
                if wxdset[key] is not None:
                    indexes = np.digitize(wxdset['Time'], time, right=True)
                    data_stack[indexes, i] = wxdset[key]
            self[key] = self.combine_first(data_stack)

        keys = ['Year', 'Month', 'Day', 'Tmax', 'Tmin', 'Tavg', 'Ptot']
        self['Combined Dataset'] = \
            np.vstack([self[key] for key in keys]).transpose()

        self['Minimum Year'] = int(np.min(self['Year']))
        self['Maximum Year'] = int(np.max(self['Year']))

    @staticmethod
    def combine_first(data_stack):
        m, n = np.shape(data_stack)
        host = data_stack[:, 0]
        guests = [data_stack[:, i] for i in range(1, n)]
        for guest in guests:
            nan_indexes = np.where(np.isnan(host))[0]
            host[nan_indexes] = guest[nan_indexes]

        return host

    def get_proposed_saved_filename(self):
        station_name = self['Station Name']
        climate_id = self['Climate Identifier']
        min_year = self['Minimum Year']
        max_year = self['Maximum Year']

        # Check if the characters "/" or "\" are present in the station
        # name and replace these characters by "_" if applicable.

        station_name = station_name.replace('\\', '_')
        station_name = station_name.replace('/', '_')

        return "%s (%s)_%s-%s.csv" % (station_name, climate_id,
                                      min_year, max_year)

    def save_to_csv(self, filepath=None):
        """
        This method saves the combined data into a single csv file.
        """
        keys = ['Station Name', 'Province', 'Latitude', 'Longitude',
                'Elevation', 'Climate Identifier']
        fcontent = []
        for key in keys:
            fcontent.append([key, self[key]])
        fcontent.append([])
        fcontent.append(['Year', 'Month', 'Day', 'Max Temp (deg C)',
                         'Min Temp (deg C)', 'Mean Temp (deg C)',
                         'Total Precip (mm)'])

        keys = ['Year', 'Month', 'Day', 'Tmax', 'Tmin', 'Tavg', 'Ptot']
        fcontent = fcontent + self['Combined Dataset'].astype(str).tolist()

        if filepath is None:
            filename = self.get_proposed_saved_filename()
            filepath = os.path.join(os.getcwd(), filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
            writer.writerows(fcontent)

        if self.deleteInpuFiles():
            for file in self._filepaths:
                try:
                    os.remove(file)
                except PermissionError:
                    pass


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
    workdir = os.path.join("..", "tests", "@ new-prô'jèt!", "Meteo", "Input")
    file1 = os.path.join(workdir, "Station 1 (7020560)_1960-1974.csv")
    file2 = os.path.join(workdir, "Station 2 (7020560)_1990-1974.csv")

    wxdata_merger = WXDataMerger([file1, file2], True)
    wxdata_merger.save_to_csv(
            os.path.join(workdir, wxdata_merger.get_proposed_saved_filename()))


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
