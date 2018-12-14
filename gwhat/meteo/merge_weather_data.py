# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: standard libraries

import os
import csv

# ---- Imports: third parties

from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QApplication, QGridLayout,
                             QLabel, QPushButton, QCheckBox, QLineEdit,
                             QFileDialog)

# ---- Imports: local

from gwhat.utils import icons
from gwhat.utils.icons import QToolButtonSmall
from gwhat.meteo.weather_reader import read_weather_datafile


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

    def save_to_csv(self, filepath):
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

        with open(filepath, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',', lineterminator='\n')
            writer.writerows(fcontent)

        if self.deleteInpuFiles():
            for file in self._filepaths:
                if file == filepath:
                    continue
                else:
                    try:
                        os.remove(file)
                    except PermissionError:                  # pragma: no cover
                        pass


class WXDataMergerWidget(QDialog):

    def __init__(self, wxdset=None, parent=None):
        super(WXDataMergerWidget, self).__init__(parent)

        self.setModal(False)
        self.setWindowFlags(Qt.CustomizeWindowHint |
                            Qt.WindowCloseButtonHint)

        self.setWindowTitle('Combine two weather datasets')
        self.setWindowIcon(icons.get_icon('master'))
        self._workdir = os.getcwd()

        self.__initUI__()

    def __initUI__(self):

        # ---- Toolbar ----

        self.btn_saveas = QPushButton('Save As...')
        self.btn_saveas.clicked.connect(self.btn_saveas_isClicked)
        self.btn_saveas.setEnabled(False)
        btn_cancel = QPushButton('Close')
        btn_cancel.clicked.connect(self.close)

        toolbar = QGridLayout()
        toolbar.addWidget(self.btn_saveas, 0, 1)
        toolbar.addWidget(btn_cancel, 0, 2)
        toolbar.setColumnStretch(0, 100)
        toolbar.setContentsMargins(0, 25, 0, 0)  # (L, T, R, B)

        # ---- Central Widget ----

        self._file_path1 = QLineEdit()
        self._file_path1.setReadOnly(True)
        lbl_get_file1 = QLabel("Select a first weather data file :")
        self.btn_get_file1 = QToolButtonSmall(icons.get_icon('openFile'))
        self.btn_get_file1.file_path = self._file_path1
        self.btn_get_file1.clicked.connect(self.set_first_filepath)

        self._file_path2 = QLineEdit()
        self._file_path2.setReadOnly(True)
        lbl_get_file2 = QLabel("Select a second weather data file :")
        self.btn_get_file2 = QToolButtonSmall(icons.get_icon('openFile'))
        self.btn_get_file2.file_path = self._file_path2
        self.btn_get_file2.clicked.connect(self.set_second_filepath)

        self._del_input_files_ckbox = QCheckBox(
                "Delete both original input datafiles after merging.")
        self._del_input_files_ckbox.setCheckState(Qt.Unchecked)

        # ---- Setup Layout ----

        # Place widgets for file #1.
        central_layout = QGridLayout()
        row = 0
        central_layout.addWidget(lbl_get_file1, row, 0, 1, 2)
        row += 1
        central_layout.addWidget(self._file_path1, row, 0)
        central_layout.addWidget(self.btn_get_file1, row, 1)
        row += 1
        central_layout.setRowMinimumHeight(row, 15)
        row += 1
        # Place widgets for file #2.
        central_layout.addWidget(lbl_get_file2, row, 0, 1, 2)
        row += 1
        central_layout.addWidget(self._file_path2, row, 0)
        central_layout.addWidget(self.btn_get_file2, row, 1)
        row += 1
        central_layout.setRowMinimumHeight(row, 15)
        row += 1
        central_layout.setRowMinimumHeight(row, 15)
        row += 1
        central_layout.addWidget(self._del_input_files_ckbox, row, 0, 1, 2)
        central_layout.setColumnStretch(1, 100)

        # ---- Self Layout ----

        layout = QGridLayout(self)
        layout.addLayout(central_layout, 0, 0)
        layout.addLayout(toolbar, 1, 0)

    def set_first_filepath(self, file1=None):
        if file1 in [None, False]:
            file1 = self.get_filepath()
        if file1:
            self._file_path1.setText(file1)

        file2 = self._file_path2.text()
        if os.path.exists(file1) and os.path.exists(file2):
            self.btn_saveas.setEnabled(True)

    def set_second_filepath(self, file2=None):
        if file2 in [None, False]:
            file2 = self.get_filepath()
        if file2:
            self._file_path2.setText(file2)

        file1 = self._file_path2.text()
        if os.path.exists(file1) and os.path.exists(file2):
            self.btn_saveas.setEnabled(True)

    def get_filepath(self):
        fpath, ftype = QFileDialog.getOpenFileName(
                self, 'Select a valid weather data file', self._workdir,
                '*.csv')
        if fpath:
            self._workdir = os.path.dirname(fpath)
        return fpath

    def set_workdir(self, dirname):
        if os.path.exists(dirname):
            self._workdir = dirname

    def btn_saveas_isClicked(self):
        data_merger = WXDataMerger(
                [self._file_path1.text(), self._file_path2.text()])

        fpath = os.path.join(self._workdir,
                             data_merger.get_proposed_saved_filename())

        fpath, ftype = QFileDialog.getSaveFileName(
                self, 'Save the combine dataset to file', fpath, '*.csv')

        if fpath:
            self._workdir = os.path.dirname(fpath)
            data_merger.setDeleteInputFiles(
                    self._del_input_files_ckbox.isChecked())
            data_merger.save_to_csv(fpath)
            self.close()

    def show(self):
        super(WXDataMergerWidget, self).show()
        self.setFixedSize(self.size())


if __name__ == '__main__':                                   # pragma: no cover
    import platform
    import sys

    app = QApplication(sys.argv)

    if platform.system() == 'Windows':
        app.setFont(QFont('Segoe UI', 11))
    elif platform.system() == 'Linux':
        app.setFont(QFont('Ubuntu', 11))

    merger_widget = WXDataMergerWidget()
    merger_widget.show()

    sys.exit(app.exec_())
