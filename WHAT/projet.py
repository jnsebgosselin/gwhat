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

from __future__ import division, unicode_literals

# Standard library imports :

from sys import argv
import platform
import os
import csv
from datetime import datetime

# Third party imports :

from PySide import QtGui, QtCore
import h5py

# Local imports :

import database as db
from icons import IconDB
from database import styleUI
import widgets as myqt
import custom_widgets as MyQWidget

import data as dtm


class Projet(h5py.File):
    def __init__(self, name):
        if not os.path.exists(name):
            self.create_projet(name)
        else:
            self.load_projet(name)

    def create_projet(self, name):
        super(Projet, self).__init__(name, mode='w')

        # ---------------------------------------------------------------------

        self.attrs['name'] = 'None'
        self.attrs['author'] = 'None'
        self.attrs['created'] = 'None'
        self.attrs['modified'] = 'None'
        self.attrs['version'] = 'None'
        self.attrs['latitude'] = 0
        self.attrs['longitude'] = 0

        # ---------------------------------------------------------------------

        self.create_group('wldsets')
        self.create_group('wxdsets')
        # http://wxbrad.com/why-wx-is-the-abbreviation-for-weather/

    def load_projet(self, name):
        super(Projet, self).__init__(name, mode='a')

        # for backward compatibility :

        for key in ['name', 'author', 'created', 'modified', 'version']:
            if key not in list(self.attrs.keys()):
                self.attrs[key] = 'None'

        for key in ['latitude', 'longitude']:
            if key not in list(self.attrs.keys()):
                self.attrs[key] = 0

        for key in ['wldsets', 'wxdsets']:
            if key not in list(self.keys()):
                self.create_group(key)

    # =========================================================================

    @property
    def name(self):
        return self.attrs['name']

    @name.setter
    def name(self, x):
        self.attrs['name'] = x

    @property
    def author(self):
        return self.attrs['author']

    @author.setter
    def author(self, x):
        self.attrs['author'] = x

    # -------------------------------------------------------------------------

    @property
    def created(self):
        return self.attrs['created']

    @created.setter
    def created(self, x):
        self.attrs['created'] = x

    @property
    def modified(self):
        return self.attrs['modified']

    @modified.setter
    def modified(self, x):
        self.attrs['modified'] = x

    @property
    def version(self):
        return self.attrs['version']

    @version.setter
    def version(self, x):
        self.attrs['version'] = x

    # -------------------------------------------------------------------------

    @property
    def lat(self):
        return self.attrs['latitude']

    @lat.setter
    def lat(self, x):
        self.attrs['latitude'] = x

    @property
    def lon(self):
        return self.attrs['longitude']

    @lon.setter
    def lon(self, x):
        self.attrs['longitude'] = x

    # =========================================================================

    @property
    def wldsets(self):
        return list(self['wldsets'].keys())

    def get_wldset(self, label):
        pass

    def create_wldset(self, name, df):
        if name in self.wldsets:
            del self['wldsets/%s' % name]

        grp = self['wldsets'].create_group(name)

        print('created new dataset sucessfully')

        grp.create_dataset('Time', data=df['Time'])
        grp.create_dataset('WL', data=df['WL'])
        grp.create_dataset('BP', data=df['BP'])
        grp.create_dataset('ET', data=df['ET'])

        grp.attrs['well'] = df['well']
        grp.attrs['latitude'] = df['latitude']
        grp.attrs['longitude'] = df['longitude']
        grp.attrs['altitude'] = df['altitude']
        grp.attrs['municipality'] = df['municipality']

        grp.create_group('brf')
        grp.create_group('hydrographs')

    def delete_wldataset(self, name):
        del self['wldsets/%s' % name]


# =============================================================================
# =============================================================================


class ProjetManager(QtGui.QWidget):

    currentProjetChanged = QtCore.Signal(bool)

    def __init__(self, parent=None, projet=None):
        super(ProjetManager, self).__init__(parent)

        self.data_manager = DataManager(parent)
        self.__projet = None
        if projet:
            self.load_project(projet)

        self.__initGUI__()

    def __initGUI__(self):

        self.project_display = QtGui.QPushButton()
        self.project_display.setFocusPolicy(QtCore.Qt.NoFocus)
        self.project_display.setFont(styleUI().font_menubar)
        self.project_display.setMinimumWidth(100)
        self.project_display.clicked.connect(self.select_project)

        new_btn = QtGui.QToolButton()
        new_btn.setAutoRaise(True)
        new_btn.setIcon(IconDB().new_project)
        new_btn.setToolTip('Create a new project...')
        new_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        new_btn.setIconSize(IconDB().iconSize2)
        new_btn.clicked.connect(self.show_newproject_dialog)

        # ---- layout ----

        layout = QtGui.QGridLayout(self)

        layout.addWidget(QtGui.QLabel('Project :'), 0, 1)
        layout.addWidget(self.project_display, 0, 2)
        layout.addWidget(new_btn, 0, 3)

        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 5)  # (L, T, R, B)
        layout.setColumnStretch(0, 500)
        layout.setRowMinimumHeight(0, 28)

    # =========================================================================

    @property
    def projet(self):
        return self.__projet

    def load_project(self, filename):
        print('\nLoading "%s"...' % os.path.basename(filename))

        # Read projet from filename :

        try:
            projet = Projet(filename)
        except:
            projet = self.convert_projet_format(filename)

        # Update UI and assign new projet to manager if not None :

        if projet is None:
            print('Project loading failed!\n')
            msg = ('Project loading failed. <i>%s</i> is not valid ' +
                   'WHAT project file.') % os.path.basename(filename)
            btn = QtGui.QMessageBox.Ok
            QtGui.QMessageBox.warning(self, 'Warning', msg, btn)
            return False
        else:
            if self.__projet:
                self.__projet.close()
            self.__projet = projet

            self.project_display.setText(projet.name)
            self.project_display.adjustSize()

            self.data_manager.set_projet(projet)
            self.currentProjetChanged.emit(True)

            print('Project "%s" loaded succesfully\n' % projet.name)

            return True

    def convert_projet_format(self, filename):
        try:
            print('Old file format. Converting to the new format...')
            with open(filename, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f, delimiter='\t'))

                name = reader[0][1]
                author = reader[1][1]
                created = reader[2][1]
                modified = reader[3][1]
                version = reader[4][1]
                lat = float(reader[6][1])
                lon = float(reader[7][1])
        except:
            print('Project file is not valid!')
            return None
        else:
            os.remove(filename)

            projet = Projet(filename)
            projet.name = name
            projet.author = author
            projet.created = created
            projet.modified = modified
            projet.version = version
            projet.lat = lat
            projet.lon = lon

            print('Projet converted to the new format successfully.')

            return projet

    # =========================================================================

    def show_newproject_dialog(self):
        if self.parent():
            new_project_window = NewProject(self.parent())
        else:
            new_project_window = NewProject(self)
        new_project_window.show()
        new_project_window.NewProjectSignal.connect(self.load_project)

    def select_project(self):
        directory = os.path.abspath(os.path.join('..', 'Projects'))
        filename, _ = QtGui.QFileDialog.getOpenFileName(
            self, 'Open Project', directory, '*.what')

        if filename:
            self.projectfile = filename
            self.load_project(filename)


# =============================================================================
# =============================================================================


class DataManager(QtGui.QWidget):
    def __init__(self, parent=None, projet=None):
        super(DataManager, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowIcon(IconDB().master)

        self.new_waterlvl_win = NewWaterLvl(parent, projet)
        self.new_waterlvl_win.newDatasetCreated.connect(self.update_wldsets)

        self.set_projet(projet)
        self.workdir = os.path.dirname(os.getcwd())

        self.__initUI__()

    # =========================================================================

    @property
    def projet(self):
        return self._projet

    def set_projet(self, projet):
        if projet is None:
            self._projet = None
        else:
            self._projet = projet
            self.workdir = os.path.dirname(projet.filename)
            self.update_wldsets()

        self.new_waterlvl_win.set_projet(projet)

    # =========================================================================

    def import_dataset(self):
        if self.projet is None:
            msg = ('Please first select a valid WHAT project or '
                   'create a new one.')
            btn = QtGui.QMessageBox.Ok
            QtGui.QMessageBox.warning(self, 'Create dataset', msg, btn)
            return
        else:
            self.new_waterlvl_win.show()

    def update_wldsets(self, name=None):
        self.wl_datasets.blockSignals(True)
        self.wl_datasets.clear()
        self.wl_datasets.addItems(self.projet.wldsets)
        if name:
            self.wl_datasets.setCurrentIndex(self.wl_datasets.findText(name))
        self.wl_datasets.blockSignals(False)

        self.dataset_changed()

    def dataset_changed(self):
        if self.wl_datasets.count() > 0:
            name = self.wl_datasets.currentText()
            dset = self.projet['wldsets/%s' % self.wl_datasets.currentText()]

            name = dset.attrs['well']
            lat = dset.attrs['latitude']
            lon = dset.attrs['longitude']
            alt = dset.attrs['altitude']
            mun = dset.attrs['municipality']

            html = dtm.waterlvl.generate_HTML_table(name, lat, lon, alt, mun)
            self.well_info_widget.clear()
            self.well_info_widget.setText(html)
        else:
            self.well_info_widget.clear()

    def del_current_wldset(self):
        if self.wl_datasets.count() > 0:
            name = self.wl_datasets.currentText()
            msg = ('Do you want to delete dataset <i>%s</i>? ' +
                   'All data will be lost.') % name
            reply = QtGui.QMessageBox.question(
                self, 'Delete current dataset', msg,
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.No:
                return

            self.projet.delete_wldataset(name)
            self.update_wldsets()

    # =========================================================================

    def __initUI__(self):

        # ----------------------------------------------- data files panel ----

        self.wl_datasets = QtGui.QComboBox()
        self.wl_datasets.currentIndexChanged.connect(self.dataset_changed)

        btn_load_wl = QtGui.QToolButton()
        btn_load_wl.setAutoRaise(True)
        btn_load_wl.setToolTip('Import a new WL dataset...')
        btn_load_wl.setIcon(IconDB().importFile)
        btn_load_wl.setIconSize(IconDB().iconSize2)
        btn_load_wl.clicked.connect(self.import_dataset)

        btn_del_wldset = QtGui.QToolButton()
        btn_del_wldset.setAutoRaise(True)
        btn_del_wldset.setToolTip('Delete current dataset.')
        btn_del_wldset.setIcon(IconDB().clear)
        btn_del_wldset.setIconSize(IconDB().iconSize2)
        btn_del_wldset.clicked.connect(self.del_current_wldset)

        self.well_info_widget = QtGui.QTextEdit()
        self.well_info_widget.setReadOnly(True)
        self.well_info_widget.setFixedHeight(150)

        self.meteo_datasets = QtGui.QComboBox()

        btn_load_meteo = QtGui.QToolButton()
        btn_load_meteo.setAutoRaise(True)
        btn_load_meteo.setToolTip('Import a new weather dataset...')
        btn_load_meteo.setIcon(IconDB().importFile)
        btn_load_meteo.setIconSize(IconDB().iconSize2)
        # btn_weather_dir.clicked.connect(self.select_meteo_file)

        self.meteo_info_widget = QtGui.QTextEdit()
        self.meteo_info_widget.setReadOnly(True)
        self.meteo_info_widget.setFixedHeight(150)

        # ---- Layout ----

        layout = QtGui.QGridLayout()

        layout.addWidget(self.wl_datasets, 0, 0)
        layout.addWidget(btn_load_wl, 0, 1)
        layout.addWidget(btn_del_wldset, 0, 2)
        layout.addWidget(self.well_info_widget, 1, 0, 1, 3)

        layout.addWidget(self.meteo_datasets, 2, 0, 1, 2)
        layout.addWidget(btn_load_meteo, 2, 2)
        layout.addWidget(self.meteo_info_widget, 3, 0, 1, 3)

        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)


# =============================================================================
# =============================================================================


class NewWaterLvl(myqt.DialogWindow):

    ConsoleSignal = QtCore.Signal(str)
    newDatasetCreated = QtCore.Signal(str)

    def __init__(self, parent=None, projet=None):
        super(NewWaterLvl, self).__init__(parent, resizable=False)
        self.setModal(True)
        self.setWindowTitle('New water level dataset')

        self.set_projet(projet)
        self.workdir = os.path.dirname(os.getcwd())
        self.__df = None

        self.__initUI__()

    # =========================================================================

    @property
    def projet(self):
        return self._projet

    def set_projet(self, projet):
        if projet is None:
            self._projet = None
        else:
            self._projet = projet
            self.workdir = os.path.dirname(projet.filename)

    # -------------------------------------------------------------------------

    @property
    def name(self):
        return self._name.text()

    @property
    def well(self):
        return self._well.text()

    @property
    def municipality(self):
        return self._mun.text()

    @property
    def lat(self):
        return self._lat.value()

    @property
    def lon(self):
        return self._lon.value()

    @property
    def alt(self):
        return self._alt.value()

    # =========================================================================

    def __initUI__(self):

        # ------------------------------------------------------- Dataset  ----

        self.directory = QtGui.QLineEdit()
        self.directory.setReadOnly(True)
        self.directory.setMinimumWidth(400)

        btn_browse = QtGui.QToolButton()
        btn_browse.setAutoRaise(True)
        btn_browse.setToolTip('Open file...')
        btn_browse.setIcon(IconDB().openFile)
        btn_browse.setIconSize(IconDB().iconSize2)
        btn_browse.clicked.connect(self.select_dataset)

        msg = ('<font color=red size=2><i>Error : Water level data file is '
               'not formatted correctly.</i></font>')
        self._msg = QtGui.QLabel(msg)
        self._msg.setVisible(False)

        # ---- layout ----

        grp_dset = QtGui.QGridLayout()

        row = 0
        text = 'Select a valid water level dataset file :'
        grp_dset.addWidget(QtGui.QLabel(text), row, 0, 1, 3)
        row += 1
        grp_dset.addWidget(QtGui.QLabel('File name :'), row, 0)
        grp_dset.addWidget(self.directory, row, 1, 1, 2)
        grp_dset.addWidget(btn_browse, row, 3)
        row += 1
        grp_dset.addWidget(self._msg, row, 1, 1, 3)

        grp_dset.setContentsMargins(0, 0, 0, 15)
        grp_dset.setColumnStretch(2, 100)
        grp_dset.setVerticalSpacing(15)

        # ----------------------------------------------------------- Well ----

        self._well = QtGui.QLineEdit()
        self._well.setAlignment(QtCore.Qt.AlignCenter)

        self._lat = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self._lat.setRange(-180, 180)

        self._lon = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self._lon.setRange(-180, 180)

        self._alt = myqt.QDoubleSpinBox(0, 3, 0.1, ' m')

        self._mun = QtGui.QLineEdit()
        self._mun.setAlignment(QtCore.Qt.AlignCenter)

        # ---- layout ----

        self.grp_well = myqt.QGroupWidget()
        self.grp_well.setTitle('Well info')
        self.grp_well.setEnabled(False)

        self.grp_well.addWidget(QtGui.QLabel('Well ID :'), row, 0)
        self.grp_well.addWidget(self._well, row, 1)
        row += 1
        self.grp_well.addWidget(QtGui.QLabel('Latitude :'), row, 0)
        self.grp_well.addWidget(self._lat, row, 1)
        row += 1
        self.grp_well.addWidget(QtGui.QLabel('Longitude :'), row, 0)
        self.grp_well.addWidget(self._lon, row, 1)
        row += 1
        self.grp_well.addWidget(QtGui.QLabel('Altitude :'), row, 0)
        self.grp_well.addWidget(self._alt, row, 1)
        row += 1
        self.grp_well.addWidget(QtGui.QLabel('Municipality :'), row, 0)
        self.grp_well.addWidget(self._mun, row, 1)

        self.grp_well.layout().setColumnStretch(2, 100)
        self.grp_well.layout().setSpacing(10)

        # ---------------------------------------------------------- Toolbar --

        self._name = QtGui.QLineEdit()

        self.btn_ok = QtGui.QPushButton(' Ok')
        self.btn_ok.setMinimumWidth(100)
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.accept_dataset)

        btn_cancel = QtGui.QPushButton(' Cancel')
        btn_cancel.setMinimumWidth(100)
        btn_cancel.clicked.connect(self.close)

        # ---- layout ----

        toolbar = QtGui.QGridLayout()

        toolbar.addWidget(QtGui.QLabel('Dataset name :'), 0, 0)
        toolbar.addWidget(self._name, 0, 1)

        toolbar.addWidget(self.btn_ok, 0, 3)
        toolbar.addWidget(btn_cancel, 0, 4)

        toolbar.setSpacing(10)
        toolbar.setColumnStretch(2, 100)
        toolbar.setContentsMargins(0, 15, 0, 0)  # (L, T, R, B)

        # ----------------------------------------------------------- Main ----

        layout = QtGui.QGridLayout(self)

        layout.addLayout(grp_dset, 0, 0)
        layout.addWidget(self.grp_well, 1, 0)
        layout.addLayout(toolbar, 2, 0)

        layout.setRowMinimumHeight(3, 15)

        warning = ('<i>Warning : Water levels must be in meter below '
                   'ground surface (mbgs)</i>')
        layout.addWidget(QtGui.QLabel(warning), 4, 0)

    # =========================================================================

    def select_dataset(self):
        filename, _ = QtGui.QFileDialog.getOpenFileName(
            self, 'Select a valid water level data file',
            self.workdir, '(*.xls *.xlsx)')

        for i in range(5):
            QtCore.QCoreApplication.processEvents()

        if filename:
            self.load_dataset(filename)

    def load_dataset(self, filename):

        if not os.path.exists(filename):
            print('Path does not exist. Cannot load water level file.')
            return

        # Update GUI path memory variables :

        self.workdir = os.path.dirname(filename)

        # Load Data :

        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        msg = 'Loading water level data...'
        print(msg)
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)

        for i in range(5):
            QtCore.QCoreApplication.processEvents()

        self.__df = dtm.waterlvl.load_excel_datafile(filename)

        # Update GUI :

        QtGui.QApplication.restoreOverrideCursor()

        self.directory.setText(filename)
        if self.__df:
            self.grp_well.setEnabled(True)
            self._msg.setVisible(False)
            self.btn_ok.setEnabled(True)

            self._well.setText(self.__df['well'])
            self._mun.setText(self.__df['municipality'])
            self._lat.setValue(self.__df['latitude'])
            self._lon.setValue(self.__df['longitude'])
            self._alt.setValue(self.__df['altitude'])
        else:
            self._msg.setVisible(True)
            self.btn_ok.setEnabled(False)
            self.grp_well.setEnabled(False)

            self._mun.setText('')
            self._well.setText('')
            self._lat.setValue(0)
            self._lon.setValue(0)
            self._alt.setValue(0)

    def accept_dataset(self):
        if self.name == '':
            msg = 'Please enter a valid name for the dataset.'
            btn = QtGui.QMessageBox.Ok
            QtGui.QMessageBox.warning(self, 'Save dataset', msg, btn)
            return

        elif self.name in self.projet.wldsets:
            msg = ('The dataset <i>%s</i> already exists.'
                   ' Do you want tho replace the existing dataset?'
                   ' All data will be lost.') % self.name
            btn = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            reply = QtGui.QMessageBox.question(self, 'Save dataset', msg, btn)
            if reply == QtGui.QMessageBox.No:
                return

        # Update dataset attributes from UI :

        self.__df['well'] = self.well
        self.__df['municipality'] = self.municipality
        self.__df['latitude'] = self.lat
        self.__df['longitude'] = self.lon
        self.__df['altitude'] = self.alt

        print('Saving dataset to project db.')
        self.projet.create_wldset(self.name, self.__df)
        self.newDatasetCreated.emit(self.name)

        self.close()

    def close(self):
        super(NewWaterLvl, self).close()
        self.clear()

    def clear(self):
        self.directory.clear()
        self._name.clear()
        self._well.clear()
        self._mun.clear()
        self._lat.setValue(0)
        self._lon.setValue(0)
        self._alt.setValue(0)

        self.__df = None

# =============================================================================
# =============================================================================


class NewProject(QtGui.QDialog):
    # Dialog window to create a new WHAT project.

    NewProjectSignal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(NewProject, self).__init__(parent)

        self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.setWindowTitle('New Project')
        self.setWindowIcon(IconDB().master)

        self.__initUI__()

    def __initUI__(self):

        # ---- Current Date ----

        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)

        # ----------------------------------------------------- PROJECT INFO --

        # ---- Widgets ----

        self.name = QtGui.QLineEdit()
        self.author = QtGui.QLineEdit()
        self.date = QtGui.QLabel('%02d/%02d/%d  %02d:%02d' % now)
        self.createdby = QtGui.QLabel(db.software_version)

        # ---- Layout ----

        projet_info = QtGui.QGridLayout()

        row = 0
        projet_info.addWidget(QtGui.QLabel('Project Title :'), row, 0)
        projet_info.addWidget(self.name, row, 1)
        row += 1
        projet_info.addWidget(QtGui.QLabel('Author :'), row, 0)
        projet_info.addWidget(self.author, row, 1)
        row += 1
        projet_info.addWidget(QtGui.QLabel('Created :'), row, 0)
        projet_info.addWidget(self.date, row, 1)
        row += 1
        projet_info.addWidget(QtGui.QLabel('Software :'), row, 0)
        projet_info.addWidget(self.createdby, row, 1)

        projet_info.setSpacing(10)
        projet_info.setColumnStretch(1, 100)
        projet_info.setColumnMinimumWidth(1, 250)
        projet_info.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # --------------------------------------------- LOCATION COORDINATES --

        locaCoord_title = QtGui.QLabel('<b>Project Location Coordinates:</b>')
        locaCoord_title.setAlignment(QtCore.Qt.AlignLeft)

        label_Lon2 = QtGui.QLabel('West')

        self.Lat_SpinBox = QtGui.QDoubleSpinBox()
        self.Lat_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.Lat_SpinBox.setSingleStep(0.1)
        self.Lat_SpinBox.setDecimals(3)
        self.Lat_SpinBox.setValue(0)
        self.Lat_SpinBox.setMinimum(0)
        self.Lat_SpinBox.setMaximum(180)
        self.Lat_SpinBox.setSuffix(u' °')

        self.Lon_SpinBox = QtGui.QDoubleSpinBox()
        self.Lon_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.Lon_SpinBox.setSingleStep(0.1)
        self.Lon_SpinBox.setDecimals(3)
        self.Lon_SpinBox.setValue(0)
        self.Lon_SpinBox.setMinimum(0)
        self.Lon_SpinBox.setMaximum(180)
        self.Lon_SpinBox.setSuffix(u' °')

        loc_coord = QtGui.QGridLayout()

        row = 0
        loc_coord.addWidget(locaCoord_title, row, 0, 1, 11)
        row += 1
        loc_coord.setColumnStretch(0, 100)
        loc_coord.addWidget(QtGui.QLabel('Latitude :'), row, 1)
        loc_coord.addWidget(self.Lat_SpinBox, row, 2)
        loc_coord.addWidget(QtGui.QLabel('North'), row, 3)
        loc_coord.setColumnStretch(4, 100)

        loc_coord.addWidget(myqt.VSep(), row, 5)
        loc_coord.setColumnStretch(6, 100)

        loc_coord.addWidget(QtGui.QLabel('Longitude :'), row, 7)
        loc_coord.addWidget(self.Lon_SpinBox, row, 8)
        loc_coord.addWidget(QtGui.QLabel('West'), row, 9)
        loc_coord.setColumnStretch(10, 100)

        loc_coord.setSpacing(10)
        loc_coord.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # --------------------------------------------------------- Browse ----

        # ---- widgets ----

        save_in_folder = os.path.abspath(os.path.join('..', 'Projects'))

        directory_label = QtGui.QLabel('Save in Folder:')
        self.directory = QtGui.QLineEdit()
        self.directory.setReadOnly(True)
        self.directory.setText(save_in_folder)
        self.directory.setMinimumWidth(350)

        btn_browse = QtGui.QToolButton()
        btn_browse.setAutoRaise(True)
        btn_browse.setIcon(IconDB().openFolder)
        btn_browse.setIconSize(IconDB().iconSize2)
        btn_browse.setToolTip('Browse...')
        btn_browse.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_browse.clicked.connect(self.browse_saveIn_folder)

        browse = QtGui.QGridLayout()

        browse.addWidget(directory_label, 0, 0)
        browse.addWidget(self.directory, 0, 1)
        browse.addWidget(btn_browse, 0, 2)

        browse.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
        browse.setColumnStretch(1, 100)
        browse.setSpacing(10)

        # ---------------------------------------------------------- Toolbar --

        # ---- widgets ----

        btn_save = QtGui.QPushButton(' Save')
        btn_save.setMinimumWidth(100)
        btn_save.clicked.connect(self.save_project)

        btn_cancel = QtGui.QPushButton(' Cancel')
        btn_cancel.setMinimumWidth(100)
        btn_cancel.clicked.connect(self.close)

        # ---- layout ----

        toolbar = QtGui.QGridLayout()

        toolbar.addWidget(btn_save, 0, 1)
        toolbar.addWidget(btn_cancel, 0, 2)

        toolbar.setSpacing(10)
        toolbar.setColumnStretch(0, 100)
        toolbar.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # ------------------------------------------------------------- MAIN --

        main_layout = QtGui.QGridLayout(self)

        main_layout.addLayout(projet_info, 0, 0)
        main_layout.addWidget(myqt.HSep(), 1, 0)
        main_layout.addLayout(loc_coord, 2, 0)
        main_layout.addWidget(myqt.HSep(), 3, 0)
        main_layout.addLayout(browse, 4, 0)
        main_layout.addLayout(toolbar, 5, 0)

        main_layout.setVerticalSpacing(25)
        main_layout.setContentsMargins(15, 15, 15, 15)  # (L, T, R, B)

    # =========================================================================

    def save_project(self):
        name = self.name.text()
        if name == '':
            print('Please enter a valid Project name')
            return

        rootname = self.directory.text()
        dirname = os.path.join(rootname, name)

        # If directory already exist, a number is added at the end within ().

        count = 1
        while os.path.exists(dirname):
            dirname = os.path.join(rootname, '%s (%d)' % (name, count))
            count += 1

        print('\n---------------')
        print('Creating files and folder achitecture for the new project in:')
        print(dirname)
        print

        # ---- Create Files and Folders ----

        try:
            os.makedirs(dirname)

            # ---- folder architecture ----

            folders = [os.path.join(dirname, 'Meteo', 'Raw'),
                       os.path.join(dirname, 'Meteo', 'Input'),
                       os.path.join(dirname, 'Meteo', 'Output'),
                       os.path.join(dirname, 'Water Levels')]

            for f in folders:
                if not os.path.exists(f):
                    os.makedirs(f)

            # ---- project.what ----

            fname = os.path.join(dirname, '%s.what' % name)
            projet = Projet(fname)

            projet.name = self.name.text()
            projet.author = self.author.text()
            projet.created = self.date.text()
            projet.modified = self.date.text()
            projet.version = self.createdby.text()
            projet.lat = self.Lat_SpinBox.value()
            projet.lon = self.Lon_SpinBox.value()

            projet.close()

            print('Creating file %s.what' % name)
            print('---------------')

            self.close()
            self.NewProjectSignal.emit(fname)
        except:
            raise

    def browse_saveIn_folder(self):
        folder = QtGui.QFileDialog.getExistingDirectory(
                self, 'Save in Folder', '../Projects')

        if folder:
            self.directory.setText(folder)

    # =========================================================================

    def reset_UI(self):

        self.name.clear()
        self.author.clear()

        save_in_folder = os.path.abspath(os.path.join('..', 'Projects'))
        self.directory.setText(save_in_folder)

        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)
        self.date = QtGui.QLabel('%02d/%02d/%d %02d:%02d' % now)

        self.Lat_SpinBox.setValue(0)
        self.Lon_SpinBox.setValue(0)

    def show(self):
        super(NewProject, self).show()
        self.raise_()

        qr = self.frameGeometry()
        if self.parentWidget():
            wp = self.parentWidget().frameGeometry().width()
            hp = self.parentWidget().frameGeometry().height()
            cp = self.parentWidget().mapToGlobal(QtCore.QPoint(wp/2., hp/2.))
        else:
            cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.setFixedSize(self.size())


# =============================================================================
# =============================================================================


if __name__ == '__main__':

    app = QtGui.QApplication(argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)

#    p = 'C:/Users/jnsebgosselin/Desktop/Project4Testing/Project4Testing.what'

    pm = ProjetManager()
#    pm.load_project(p)
    pm.show()
    pm.data_manager.show()

    app.exec_()
