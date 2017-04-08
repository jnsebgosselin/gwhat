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

try:
    import mdat
    import mgui
    from mgui.icons import IconDB, QToolButtonSmall
    import mgui.widgets as myqt
except ImportError:  # to run this module standalone
    print('Running module as a standalone script...')
    import sys
    import platform
    from os.path import dirname, realpath
    root = dirname(dirname(realpath(__file__)))
    sys.path.append(root)

    import mdat as mdat
    from mgui.icons import IconDB, QToolButtonSmall
    import mgui.widgets as myqt


# =============================================================================


class DataManager(QtGui.QWidget):
    def __init__(self, parent=None, projet=None, pm=None):
        super(DataManager, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowIcon(IconDB().master)

        self.new_waterlvl_win = NewWaterLvl(parent, projet)
        self.new_waterlvl_win.newDatasetCreated.connect(self.update_wldsets)

        self.__initUI__()

        self.set_projet(projet)
        self.workdir = os.path.dirname(os.getcwd())

        if pm:
            pm.currentProjetChanged.connect(self.set_projet)
            self.set_projet(pm.projet)

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
            wldset = self.get_current_wldset()

            name = wldset.well
            lat = wldset.lat
            lon = wldset.lon
            alt = wldset.alt
            mun = wldset.mun

            html = mdat.waterlvl.generate_HTML_table(name, lat, lon, alt, mun)
            self.well_info_widget.clear()
            self.well_info_widget.setText(html)
        else:
            self.well_info_widget.clear()

    def get_current_wldset(self):
        if self.wl_datasets.currentIndex() == -1:
            return None
        else:
            return self.projet.get_wldset(self.wl_datasets.currentText())

    def del_current_wldset(self):
        if self.wl_datasets.count() > 0:
            name = self.wl_datasets.currentText()
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

    # =========================================================================

    def __initUI__(self):

        # ----------------------------------------------- data files panel ----

        self.wl_datasets = QtGui.QComboBox()
        self.wl_datasets.currentIndexChanged.connect(self.dataset_changed)

        btn_load_wl = QToolButtonSmall(IconDB().importFile)
        btn_load_wl.setToolTip('Import a new WL dataset...')
        btn_load_wl.clicked.connect(self.import_dataset)

        btn_del_wldset = QToolButtonSmall(IconDB().clear)
        btn_del_wldset.setToolTip('Delete current dataset.')
        btn_del_wldset.clicked.connect(self.del_current_wldset)

        self.well_info_widget = QtGui.QTextEdit()
        self.well_info_widget.setReadOnly(True)
        self.well_info_widget.setFixedHeight(150)

        self.meteo_datasets = QtGui.QComboBox()

        btn_load_meteo = QToolButtonSmall(IconDB().importFile)
        btn_load_meteo.setToolTip('Import a new weather dataset...')
        # btn_weather_dir.clicked.connect(self.select_meteo_file)

        btn_del_wxdset = QToolButtonSmall(IconDB().clear)
        btn_del_wxdset.setToolTip('Delete current dataset.')

        self.meteo_info_widget = QtGui.QTextEdit()
        self.meteo_info_widget.setReadOnly(True)
        self.meteo_info_widget.setFixedHeight(150)

        # ---- Layout ----

        layout = QtGui.QGridLayout()

        layout.addWidget(self.wl_datasets, 0, 0)
        layout.addWidget(btn_load_wl, 0, 1)
        layout.addWidget(btn_del_wldset, 0, 2)
        layout.addWidget(self.well_info_widget, 1, 0, 1, 3)

        layout.addWidget(self.meteo_datasets, 2, 0)
        layout.addWidget(btn_load_meteo, 2, 1)
        layout.addWidget(btn_del_wxdset, 2, 2)
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
        self._dset = None  # water level datset

        self.__initUI__()

    def __initUI__(self):

        # ------------------------------------------------------- Dataset  ----

        self.directory = QtGui.QLineEdit()
        self.directory.setReadOnly(True)
        self.directory.setMinimumWidth(400)

        btn_browse = QToolButtonSmall(IconDB().openFile)
        btn_browse.setToolTip('Open file...')
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

        self._dset = mdata.waterlvl.load_excel_datafile(filename)

        # Update GUI :

        QtGui.QApplication.restoreOverrideCursor()

        self.directory.setText(filename)
        if self._dset is not None:
            self.grp_well.setEnabled(True)
            self._msg.setVisible(False)
            self.btn_ok.setEnabled(True)

            self._well.setText(self._dset['well'])
            self._mun.setText(self._dset['municipality'])
            self._lat.setValue(self._dset['latitude'])
            self._lon.setValue(self._dset['longitude'])
            self._alt.setValue(self._dset['altitude'])
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

        elif self.name in self.projet.wldsets:
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

        self._dset['well'] = self.well
        self._dset['municipality'] = self.municipality
        self._dset['latitude'] = self.lat
        self._dset['longitude'] = self.lon
        self._dset['altitude'] = self.alt

        print('Saving dataset to project db.')
        self.projet.add_wldset(self.name, self._dset)
        self.newDatasetCreated.emit(self.name)

        self.close()

    # =========================================================================

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

        self._dset = None

# =============================================================================
# =============================================================================


# class NewWXDataDialog(myqt.DialogWindow):


# =============================================================================
# =============================================================================


if __name__ == '__main__':
    f = 'C:/Users/jnsebgosselin/Desktop/Project4Testing/Project4Testing.what'
    p = mdat.reader.ProjetReader(f)

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
