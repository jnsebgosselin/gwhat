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

import os
from datetime import datetime

# Third party imports :

from PySide import QtGui, QtCore

# Local imports :

for i in range(2):
    try:
        from common import IconDB, QToolButtonSmall
        import common.widgets as myqt
        from hydrograph4 import LatLong2Dist
        import projet.reader_waterlvl as wlrd
        import meteo.weather_reader as wxrd
        break
    except ImportError:  # to run this module standalone
        import sys
        import platform
        from os.path import dirname, realpath, basename
        print('Running module %s as a script...' % basename(__file__))
        sys.path.append(dirname(dirname(realpath(__file__))))


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class DataManager(QtGui.QWidget):

    wldsetChanged = QtCore.Signal(dict)
    wxdsetChanged = QtCore.Signal(dict)

    def __init__(self, parent=None, projet=None, pm=None):
        super(DataManager, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowIcon(IconDB().master)

        self.new_waterlvl_win = NewWaterLvl(parent, projet)
        self.new_waterlvl_win.newDatasetCreated.connect(self.new_wldset_added)

        self.new_weather_win = NewWXDataDialog(parent, projet)
        self.new_weather_win.newDatasetCreated.connect(self.new_wxdset_added)

        self.__initUI__()

        self.set_projet(projet)
        if pm:
            pm.currentProjetChanged.connect(self.set_projet)
            self.set_projet(pm.projet)

    # =========================================================================

    @property
    def workdir(self):
        if self.projet is None:
            return os.path.dirname(os.getcwd())
        else:
            return os.path.dirname(self.projet.filename)

    @property
    def projet(self):
        return self._projet

    def set_projet(self, projet):
        if projet is None:
            self._projet = None
        else:
            self._projet = projet

            self.update_wldsets()
            self.update_wxdsets()

            self.update_wldset_info()
            self.update_wxdset_info()

            self.wldset_changed()

        self.new_waterlvl_win.set_projet(projet)
        self.new_weather_win.set_projet(projet)

    # ========================================================== utilities ====

    def emit_warning(self, msg):
        btn = QtGui.QMessageBox.Ok
        QtGui.QMessageBox.warning(self, 'Warning', msg, btn)

    # ========================================================= WL Dataset ====

    @property
    def wldsets(self):
        return self.projet.wldsets

    def wldataset_count(self):
        return len(self.projet.wldsets)

    def import_wldataset(self):
        if self.projet is None:
            msg = ('Please first select a valid WHAT project or '
                   'create a new one.')
            btn = QtGui.QMessageBox.Ok
            QtGui.QMessageBox.warning(self, 'Create dataset', msg, btn)
            return
        else:
            self.new_waterlvl_win.show()

    # ---------------------------------------------------------------------

    def new_wldset_added(self):
        self.update_wldsets()
        self.update_wldset_info()
        self.wldset_changed()

    def update_wldsets(self, name=None):
        self.wldsets_cbox.blockSignals(True)
        self.wldsets_cbox.clear()
        self.wldsets_cbox.addItems(self.projet.wldsets)
        if name:
            self.wldsets_cbox.setCurrentIndex(self.wldsets_cbox.findText(name))
        self.wldsets_cbox.blockSignals(False)

    def update_wldset_info(self):
        self.well_info_widget.clear()
        wldset = self.get_current_wldset()
        if wldset is not None:
            name = wldset['Well']
            lat = wldset['Latitude']
            lon = wldset['Longitude']
            alt = wldset['Elevation']
            mun = wldset['Municipality']

            html = wlrd.generate_HTML_table(name, lat, lon, alt, mun)
            self.well_info_widget.setText(html)

    def wldset_changed(self):
        self.wldsetChanged.emit(self.get_current_wldset())

    # ---------------------------------------------------------------------

    def get_current_wldset(self):
        if self.wldsets_cbox.currentIndex() == -1:
            return None
        else:
            return self.projet.get_wldset(self.wldsets_cbox.currentText())

    def del_current_wldset(self):
        if self.wldsets_cbox.count() > 0:
            name = self.wldsets_cbox.currentText()
            msg = ('Do you want to delete dataset <i>%s</i>? ' +
                   'All data will be deleted from the project database, ' +
                   'but the original data files will be preserved') % name
            reply = QtGui.QMessageBox.question(
                self, 'Delete current dataset', msg,
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.No:
                return

            self.projet.del_wldset(name)
            self.update_wldsets()
            self.update_wldset_info()
            self.wldset_changed()

    # ========================================================= WX Dataset ====

    @property
    def wxdsets(self):
        return self.projet.wxdsets

    def wxdataset_count(self):
        return len(self.projet.wxdsets)

    def import_wxdataset(self):
        if self.projet is None:
            msg = ('Please first select a valid WHAT project or '
                   'create a new one.')
            btn = QtGui.QMessageBox.Ok
            QtGui.QMessageBox.warning(self, 'Create dataset', msg, btn)
            return
        else:
            self.new_weather_win.show()

    def new_wxdset_added(self):
        self.update_wxdsets()
        self.update_wxdset_info()
        self.wxdset_changed()

    def update_wxdsets(self, name=None, silent=False):
        self.wxdsets_cbox.blockSignals(True)
        self.wxdsets_cbox.clear()
        self.wxdsets_cbox.addItems(self.projet.wxdsets)
        if name:
            self.wxdsets_cbox.setCurrentIndex(self.wxdsets_cbox.findText(name))
        self.wxdsets_cbox.blockSignals(False)

    def update_wxdset_info(self):
        self.meteo_info_widget.clear()
        if self.wxdsets_cbox.count() > 0:
            wxdset = self.get_current_wxdset()

            staname = wxdset['Station Name']
            lat = wxdset['Latitude']
            lon = wxdset['Longitude']
            alt = wxdset['Elevation']
            prov = wxdset['Province']
            climID = wxdset['Climate Identifier']

            html = wxrd.generate_weather_HTML(staname, prov, lat,
                                              climID, lon, alt)
            self.meteo_info_widget.setText(html)

    def wxdset_changed(self):
        self.wxdsetChanged.emit(self.get_current_wxdset())

    # ---------------------------------------------------------------------

    def del_current_wxdset(self):
        if self.wxdsets_cbox.count() > 0:
            name = self.wxdsets_cbox.currentText()
            msg = ('Do you want to delete weather dataset <i>%s</i>? ' +
                   'All data will be deleted from the project database, ' +
                   'but the original data files will be preserved') % name
            reply = QtGui.QMessageBox.question(
                self, 'Delete current dataset', msg,
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.No:
                return

            self.projet.del_wxdset(name)
            self.update_wxdsets()
            self.update_wxdset_info()
            self.wxdset_changed()

    def get_current_wxdset(self):
        if self.wxdsets_cbox.currentIndex() == -1:
            return None
        else:
            return self.projet.get_wxdset(self.wxdsets_cbox.currentText())

    def set_current_wxdset(self, name):
        self.wxdsets_cbox.blockSignals(True)
        self.wxdsets_cbox.setCurrentIndex(self.wxdsets_cbox.findText(name))
        self.wxdsets_cbox.blockSignals(False)

        self.update_wxdset_info()
        self.wxdset_changed()

    def set_closest_wxdset(self):
        if self.wldataset_count() == 0:
            return None
        elif self.wxdataset_count() == 0:
            return None
        else:
            wldset = self.get_current_wldset()
            lat1 = wldset['Latitude']
            lon1 = wldset['Longitude']

            mindist = 10**16
            closest = None
            for name in self.wxdsets:
                wxdset = self.projet.get_wxdset(name)
                lat2 = wxdset['Latitude']
                lon2 = wxdset['Longitude']
                newdist = LatLong2Dist(lat1, lon1, lat2, lon2)

                if newdist < mindist:
                    closest = wxdset.name
                    mindist = newdist

            self.set_current_wxdset(closest)

    # =========================================================================

    def __initUI__(self):

        # ---------------------------------------- water level dataset ----

        self.wldsets_cbox = QtGui.QComboBox()
        self.wldsets_cbox.currentIndexChanged.connect(self.update_wldset_info)
        self.wldsets_cbox.currentIndexChanged.connect(self.wldset_changed)

        btn_load_wl = QToolButtonSmall(IconDB().importFile)
        btn_load_wl.setToolTip('Import a new WL dataset...')
        btn_load_wl.clicked.connect(self.import_wldataset)

        btn_del_wldset = QToolButtonSmall(IconDB().clear)
        btn_del_wldset.setToolTip('Delete current dataset.')
        btn_del_wldset.clicked.connect(self.del_current_wldset)

        # ---- toolbar ----

        wltb = QtGui.QGridLayout()
        wltb.setContentsMargins(0, 0, 0, 0)

        widgets = [self.wldsets_cbox, btn_load_wl, btn_del_wldset]

        for col, widg in enumerate(widgets):
            wltb.addWidget(widg, 0, col)

        # ---- info box -----

        self.well_info_widget = QtGui.QTextEdit()
        self.well_info_widget.setReadOnly(True)
        self.well_info_widget.setFixedHeight(150)

        # -------------------------------------------- weather dataset ----

        self.wxdsets_cbox = QtGui.QComboBox()
        self.wxdsets_cbox.currentIndexChanged.connect(self.update_wxdset_info)
        self.wxdsets_cbox.currentIndexChanged.connect(self.wxdset_changed)

        btn_load_meteo = QToolButtonSmall(IconDB().importFile)
        btn_load_meteo.setToolTip('Import a new weather dataset...')
        btn_load_meteo.clicked.connect(self.import_wxdataset)

        # btn_weather_dir.clicked.connect(self.select_meteo_file)

        btn_del_wxdset = QToolButtonSmall(IconDB().clear)
        btn_del_wxdset.setToolTip('Delete current dataset.')
        btn_del_wxdset.clicked.connect(self.del_current_wxdset)

        btn_closest_meteo = QToolButtonSmall(IconDB().closest_meteo)
        btn_closest_meteo.setToolTip('<p>Select the weather station closest'
                                     ' from the observation well.</p>')
        btn_closest_meteo.clicked.connect(self.set_closest_wxdset)

        # ---- toolbar ----

        wxtb = QtGui.QGridLayout()
        wxtb.setContentsMargins(0, 0, 0, 0)

        widgets = [self.wxdsets_cbox, btn_load_meteo, btn_del_wxdset,
                   btn_closest_meteo]

        for col, widg in enumerate(widgets):
            wxtb.addWidget(widg, 0, col)

        # ---- info box -----

        self.meteo_info_widget = QtGui.QTextEdit()
        self.meteo_info_widget.setReadOnly(True)
        self.meteo_info_widget.setFixedHeight(150)

        # ------------------------------------------- Main Right Panel ----

        layout = QtGui.QGridLayout()

        layout.addLayout(wltb, 0, 0)
        layout.addWidget(self.well_info_widget, 1, 0)

        layout.addLayout(wxtb, 2, 0)
        layout.addWidget(self.meteo_info_widget, 3, 0)

        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class NewDataset(myqt.DialogWindow):
    ConsoleSignal = QtCore.Signal(str)
    newDatasetCreated = QtCore.Signal(str)

    def __init__(self, dsetname, parent=None, projet=None):
        super(NewDataset, self).__init__(parent, resizable=False)

        self._dsetname = dsetname

        self.setModal(True)
        self.setWindowTitle('New %s dataset' % dsetname.lower())

        self.set_projet(projet)
        self.workdir = os.path.dirname(os.getcwd())
        self._dataset = None  # dataset

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

    @property
    def name(self):
        return self._name.text()

    # =========================================================================

    def __initUI__(self):

        # ------------------------------------------------- Dataset  ------

        self.directory = QtGui.QLineEdit()
        self.directory.setReadOnly(True)
        self.directory.setMinimumWidth(400)

        btn_browse = QToolButtonSmall(IconDB().openFile)
        btn_browse.setToolTip('Open file...')
        btn_browse.clicked.connect(self.select_dataset)

        msg = ('<font color=red size=2><i>Error : %s data file is '
               'not formatted correctly.</i></font>'
               ) % self._dsetname.capitalize()
        self._msg = QtGui.QLabel(msg)
        self._msg.setVisible(False)

        # ---- layout ----

        grp_dset = QtGui.QGridLayout()

        row = 0
        text = 'Select a valid %s dataset file :' % self._dsetname.lower()
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

        # ------------------------------------------------------ Info ----

        infogrp = self.__initInfoGroup__()

        # --------------------------------------------------- Toolbar ----

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
        layout.addWidget(infogrp, 1, 0)
        layout.addLayout(toolbar, 2, 0)

        layout.setRowMinimumHeight(3, 15)

    def __initInfoGroup__(self):
        return None

    # =========================================================================

    def select_dataset(self):
        pass

    def load_dataset(self, filename):
        pass

    def accept_dataset(self):
        pass

    # =========================================================================

    def close(self):
        super(NewDataset, self).close()
        self.clear()

    def clear(self):
        self.directory.clear()
        self._name.clear()
        self._dataset = None


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class NewWaterLvl(NewDataset):
    def __init__(self, parent=None, projet=None):
        super(NewWaterLvl, self).__init__('water level', parent, projet)

        warning = ('<i>Warning : Water levels must be in meter below '
                   'ground surface (mbgs)</i>')
        self.layout().addWidget(QtGui.QLabel(warning), 4, 0)

    def __initInfoGroup__(self):
        self._well = QtGui.QLineEdit()
        self._well.setAlignment(QtCore.Qt.AlignCenter)

        self._lat = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self._lat.setRange(-180, 180)

        self._lon = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self._lon.setRange(-180, 180)

        self._alt = myqt.QDoubleSpinBox(0, 3, 0.1, ' m')
        self._alt.setRange(-9999, 9999)

        self._mun = QtGui.QLineEdit()
        self._mun.setAlignment(QtCore.Qt.AlignCenter)

        # ---- layout ----

        self.grp_well = myqt.QGroupWidget()
        self.grp_well.setTitle('Well info')
        self.grp_well.setEnabled(False)

        row = 0
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

        return self.grp_well

    # -------------------------------------------------------------------------

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

    def select_dataset(self):
        filename, _ = QtGui.QFileDialog.getOpenFileName(
            self, 'Select a valid water level data file',
            self.workdir, '(*.xls *.xlsx)')

        for i in range(5):
            QtCore.QCoreApplication.processEvents()

        if filename:
            self.load_dataset(filename)

    # -------------------------------------------------------------------------

    def load_dataset(self, filename):
        if not os.path.exists(filename):
            print('Path does not exist. Cannot open %s.' % filename)
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

        self._dataset = wlrd.load_excel_datafile(filename)

        # Update GUI :

        QtGui.QApplication.restoreOverrideCursor()

        self.directory.setText(filename)
        if self._dataset is not None:
            self.grp_well.setEnabled(True)
            self._msg.setVisible(False)
            self.btn_ok.setEnabled(True)

            self._well.setText(self._dataset['Well'])
            self._mun.setText(self._dataset['Municipality'])
            self._lat.setValue(self._dataset['Latitude'])
            self._lon.setValue(self._dataset['Longitude'])
            self._alt.setValue(self._dataset['Elevation'])
            self._name.setText(self._dataset['Well'])
        else:
            self._msg.setVisible(True)
            self.btn_ok.setEnabled(False)
            self.grp_well.setEnabled(False)

            self._mun.clear()
            self._well.clear()
            self._lat.setValue(0)
            self._lon.setValue(0)
            self._alt.setValue(0)

    # -------------------------------------------------------------------------

    def accept_dataset(self):
        if self.name == '':
            msg = 'Please enter a valid name for the dataset.'
            btn = QtGui.QMessageBox.Ok
            QtGui.QMessageBox.warning(self, 'Save dataset', msg, btn)
            return

        if self.name in self.projet.wldsets:
            msg = ('The dataset <i>%s</i> already exists.'
                   ' Do you want tho replace the existing dataset?'
                   ' All data will be lost.') % self.name
            btn = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            reply = QtGui.QMessageBox.question(self, 'Save dataset', msg, btn)
            if reply == QtGui.QMessageBox.No:
                return
            else:
                self.projet.del_wldset(self.name)

        # Update dataset attributes from UI :

        self._dataset['Well'] = self.well
        self._dataset['Municipality'] = self.municipality
        self._dataset['Latitude'] = self.lat
        self._dataset['Longitude'] = self.lon
        self._dataset['Elevation'] = self.alt

        print('Saving dataset to project db.')
        self.projet.add_wldset(self.name, self._dataset)
        self.newDatasetCreated.emit(self.name)

        self.close()

    # =========================================================================

    def clear(self):
        super(NewWaterLvl, self).clear()
        self._well.clear()
        self._mun.clear()
        self._lat.setValue(0)
        self._lon.setValue(0)
        self._alt.setValue(0)


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class NewWXDataDialog(NewDataset):

    ConsoleSignal = QtCore.Signal(str)
    newDatasetCreated = QtCore.Signal(str)

    def __init__(self, parent=None, projet=None):
        super(NewWXDataDialog, self).__init__('daily weather', parent, projet)

    def __initInfoGroup__(self):

        self._staname = QtGui.QLineEdit()
        self._staname.setAlignment(QtCore.Qt.AlignCenter)

        self._staID = QtGui.QLineEdit()
        self._staID.setAlignment(QtCore.Qt.AlignCenter)

        self._lat = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self._lat.setRange(-180, 180)

        self._lon = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self._lon.setRange(-180, 180)

        self._alt = myqt.QDoubleSpinBox(0, 3, 0.1, ' m')

        self._prov = QtGui.QLineEdit()
        self._prov.setAlignment(QtCore.Qt.AlignCenter)

        # ---- layout ----

        self.grp_sta = myqt.QGroupWidget()
        self.grp_sta.setTitle('Station info')
        self.grp_sta.setEnabled(False)

        labels = ['Name :', 'ID :', 'Latitude :', 'Longitude :', 'Altitude :',
                  'Province :']
        widgets = [self._staname, self._staID, self._lat, self._lon, self._alt,
                   self._prov]

        for label, widget in zip(labels, widgets):
            row = self.grp_sta.rowCount()
            self.grp_sta.addWidget(QtGui.QLabel(label), row, 0)
            self.grp_sta.addWidget(widget, row, 1)

        self.grp_sta.layout().setColumnStretch(2, 100)
        self.grp_sta.layout().setSpacing(10)

        return self.grp_sta

    # -------------------------------------------------------------------------

    @property
    def staname(self):
        return self._staname.text()

    @property
    def staID(self):
        return self._staID.text()

    @property
    def prov(self):
        return self._prov.text()

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

    def select_dataset(self):
        filename, _ = QtGui.QFileDialog.getOpenFileName(
            self, 'Select a valid weather level data file',
            self.workdir, '(*.out)')

        for i in range(5):
            QtCore.QCoreApplication.processEvents()

        if filename:
            self.load_dataset(filename)

    # ---------------------------------------------------------------------

    def load_dataset(self, filename):
        if not os.path.exists(filename):
            print('Path does not exist. Cannot open %s.' % filename)
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

        self._dataset = wxrd.WXDataFrame(filename)

        # Update GUI :

        QtGui.QApplication.restoreOverrideCursor()

        self.directory.setText(filename)
        if self._dataset is not None:
            self.grp_sta.setEnabled(True)
            self._msg.setVisible(False)
            self.btn_ok.setEnabled(True)

            self._staname.setText(self._dataset['Station Name'])
            self._staID.setText(self._dataset['Climate Identifier'])
            self._prov.setText(self._dataset['Province'])
            self._lat.setValue(self._dataset['Latitude'])
            self._lon.setValue(self._dataset['Longitude'])
            self._alt.setValue(self._dataset['Elevation'])
            self._name.setText(self._dataset['Station Name'])
        else:
            self.btn_ok.setEnabled(False)
            self._msg.setVisible(True)
            self.grp_sta.setEnabled(False)

            self._staname.clear()
            self._prov.clear()
            self._lat.setValue(0)
            self._lon.setValue(0)
            self._alt.setValue(0)

    # --------------------------------------------------------------------

    def accept_dataset(self):
        if self.name == '':
            msg = 'Please enter a valid name for the dataset.'
            btn = QtGui.QMessageBox.Ok
            QtGui.QMessageBox.warning(self, 'Save dataset', msg, btn)
            return

        if self.name in self.projet.wxdsets:
            msg = ('The dataset <i>%s</i> already exists.'
                   ' Do you want tho replace the existing dataset?'
                   ' All data will be lost.') % self.name
            btn = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            reply = QtGui.QMessageBox.question(self, 'Save dataset', msg, btn)
            if reply == QtGui.QMessageBox.No:
                return
            else:
                self.projet.del_wxdset(self.name)

        # Update dataset attributes from UI :

        self._dataset['Station Name'] = self.staname
        self._dataset['Climate Identifier'] = self.staID
        self._dataset['Province'] = self.prov

        self._dataset['Latitude'] = self.lat
        self._dataset['Longitude'] = self.lon
        self._dataset['Elevation'] = self.alt

        print('Saving dataset to project db.')
        self.projet.add_wxdset(self.name, self._dataset)
        self.newDatasetCreated.emit(self.name)

        self.close()

    # =========================================================================

    def clear(self):
        super(NewWXDataDialog, self).clear()
        self._staname.clear()
        self._staID.clear()
        self._prov.clear()
        self._lat.setValue(0)
        self._lon.setValue(0)
        self._alt.setValue(0)


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


if __name__ == '__main__':
    from reader_projet import ProjetReader
    f = 'C:/Users/jnsebgosselin/Desktop/Project4Testing/Project4Testing.what'
    p = ProjetReader(f)

    app = QtGui.QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)
#
#    pm = ProjetManager(projet=f)
#    pm.show()

    dm = DataManager(projet=p)
    dm.show()

    app.exec_()
