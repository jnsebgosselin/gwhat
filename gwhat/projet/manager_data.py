# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Standard library imports

import os

# ---- Third party imports

from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (QWidget, QComboBox, QGridLayout, QTextEdit,
                             QLabel, QMessageBox, QLineEdit, QPushButton,
                             QFileDialog, QApplication, QGroupBox, QDialog)

# ---- Local imports

from gwhat.common import QToolButtonSmall
from gwhat.common import icons
import gwhat.common.widgets as myqt
from gwhat.hydrograph4 import LatLong2Dist
import gwhat.projet.reader_waterlvl as wlrd
import gwhat.meteo.weather_reader as wxrd


class DataManager(QWidget):

    wldsetChanged = QSignal(object)
    wxdsetChanged = QSignal(object)

    def __init__(self, parent=None, projet=None, pm=None):
        super(DataManager, self).__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowIcon(icons.get_icon('master'))
        self.setMinimumWidth(250)

        self.new_waterlvl_win = NewDatasetDialog(
                'water level', parent, projet)
        self.new_waterlvl_win.self.sig_new_dataset_imported.connect(
                self.new_wldset_imported)

        self.new_weather_win = NewDatasetDialog(
                'daily weather', parent, projet)
        self.new_weather_win.sig_new_dataset_imported.connect(
                self.new_wxdset_imported)

        self.__initUI__()

        self.set_projet(projet)
        if pm:
            pm.currentProjetChanged.connect(self.set_projet)
            self.set_projet(pm.projet)

    def __initUI__(self):

        # -------------------------------------------- water level dataset ----

        self.wldsets_cbox = QComboBox()
        self.wldsets_cbox.currentIndexChanged.connect(self.update_wldset_info)
        self.wldsets_cbox.currentIndexChanged.connect(self.wldset_changed)

        self.btn_load_wl = QToolButtonSmall(icons.get_icon('importFile'))
        self.btn_load_wl.setToolTip('Import a new WL dataset...')
        self.btn_load_wl.clicked.connect(self.import_wldataset)

        self.btn_del_wldset = QToolButtonSmall(icons.get_icon('clear'))
        self.btn_del_wldset.setToolTip('Delete current dataset.')
        self.btn_del_wldset.clicked.connect(self.del_current_wldset)

        # ---- toolbar ----

        wltb = QGridLayout()
        wltb.setContentsMargins(0, 0, 0, 0)

        widgets = [self.wldsets_cbox, self.btn_load_wl, self.btn_del_wldset]
        for col, widg in enumerate(widgets):
            wltb.addWidget(widg, 0, col)

        # ---- info box -----

        self.well_info_widget = QTextEdit()
        self.well_info_widget.setReadOnly(True)
        self.well_info_widget.setFixedHeight(100)

        # ------------------------------------------------ weather dataset ----

        self.wxdsets_cbox = QComboBox()
        self.wxdsets_cbox.currentIndexChanged.connect(self.update_wxdset_info)
        self.wxdsets_cbox.currentIndexChanged.connect(self.wxdset_changed)

        self.btn_load_meteo = QToolButtonSmall(icons.get_icon('importFile'))
        self.btn_load_meteo.setToolTip('Import a new weather dataset...')
        self.btn_load_meteo.clicked.connect(self.import_wxdataset)

        # btn_weather_dir.clicked.connect(self.select_meteo_file)

        self.btn_del_wxdset = QToolButtonSmall(icons.get_icon('clear'))
        self.btn_del_wxdset.setToolTip('Delete current dataset.')
        self.btn_del_wxdset.clicked.connect(self.del_current_wxdset)

        btn_closest_meteo = QToolButtonSmall(icons.get_icon('closest_meteo'))
        btn_closest_meteo.setToolTip('<p>Select the weather station closest'
                                     ' from the observation well.</p>')
        btn_closest_meteo.clicked.connect(self.set_closest_wxdset)

        # ---- toolbar ----

        wxtb = QGridLayout()
        wxtb.setContentsMargins(0, 0, 0, 0)

        widgets = [self.wxdsets_cbox, self.btn_load_meteo, self.btn_del_wxdset,
                   btn_closest_meteo]

        for col, widg in enumerate(widgets):
            wxtb.addWidget(widg, 0, col)

        # ---- info box -----

        self.meteo_info_widget = QTextEdit()
        self.meteo_info_widget.setReadOnly(True)
        self.meteo_info_widget.setFixedHeight(100)

        # ---------------------------------------------------- Main Layout ----

        layout = QGridLayout()

        layout.addWidget(QLabel('Water Level Dataset :'), 1, 0)
        layout.addLayout(wltb, 2, 0)
        layout.addWidget(self.well_info_widget, 3, 0)

        layout.setRowMinimumHeight(4, 10)

        layout.addWidget(QLabel('Weather Dataset :'), 5, 0)
        layout.addLayout(wxtb, 6, 0)
        layout.addWidget(self.meteo_info_widget, 7, 0)

        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

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
            self.wxdset_changed()

        self.new_waterlvl_win.set_projet(projet)
        self.new_weather_win.set_projet(projet)

    # ========================================================== utilities ====

    def emit_warning(self, msg):
        btn = QMessageBox.Ok
        QMessageBox.warning(self, 'Warning', msg, btn)

    # ---- WL Dataset

    @property
    def wldsets(self):
        return self.projet.wldsets

    def wldataset_count(self):
        return len(self.projet.wldsets)

    def import_wldataset(self):
        if self.projet is None:
            msg = ('Please first select a valid WHAT project or '
                   'create a new one.')
            btn = QMessageBox.Ok
            QMessageBox.warning(self, 'Create dataset', msg, btn)
            return
        else:
            self.new_waterlvl_win.show()

    def new_wldset_imported(self, name, dataset):
        """
        Receives the new water level dataset, saves it in the project and
        update the GUI.
        """
        print("Saving the new water level dataset in the project...", end=" ")
        self.projet.add_wldset(name, dataset)
        self.update_wldsets()
        self.update_wldset_info()
        self.wldset_changed()
        print("done")

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
            reply = QMessageBox.question(
                self, 'Delete current dataset', msg,
                QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.No:
                return

            self.projet.del_wldset(name)
            self.update_wldsets()
            self.update_wldset_info()
            self.wldset_changed()

    # ---- WX Dataset

    @property
    def wxdsets(self):
        return self.projet.wxdsets

    def wxdataset_count(self):
        return len(self.projet.wxdsets)

    def import_wxdataset(self):
        if self.projet is None:
            msg = ("Please first select a valid project or create a new one.")
            btn = QMessageBox.Ok
            QMessageBox.warning(self, 'Create dataset', msg, btn)
            return
        else:
            self.new_weather_win.show()

    def new_wxdset_imported(self, name, dataset):
        """
        Receives the new weather dataset, saves it in the project and
        update the GUI.
        """
        print("Saving the new weather dataset in the project.", end=" ")
        self.projet.add_wxdset(name, dataset)
        self.update_wxdsets()
        self.update_wxdset_info()
        self.wxdset_changed()
        print("done")

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
            reply = QMessageBox.question(
                self, 'Delete current dataset', msg,
                QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.No:
                return

            self.projet.del_wxdset(name)
            self.update_wxdsets()
            self.update_wxdset_info()
            self.wxdset_changed()

    def get_current_wxdset(self):
        """Return the currently selected weather dataset dataframe."""
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


class NewDatasetDialog(QDialog):
    ConsoleSignal = QSignal(str)
    sig_new_dataset_imported = QSignal(str, dict)

    def __init__(self, datatype, parent=None, projet=None):
        super(NewDatasetDialog, self).__init__(parent)

        if datatype.lower() not in ['water level', 'daily weather']:
            print("ERROR: datatype value must be :",
                  ['water level', 'daily weather'])
            raise ValueError
        self._datatype = datatype.lower()

        self.setWindowTitle('Import Dataset: %s' % datatype.title())
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowFlags(Qt.Window |
                            Qt.CustomizeWindowHint |
                            Qt.WindowCloseButtonHint)

        self.set_projet(projet)
        self.workdir = os.path.dirname(os.getcwd())
        self._dataset = None

        self.__initUI__()
        if datatype == 'water level':
            warning = ('<i>Warning : Water levels must be in meter below '
                       'ground surface (mbgs)</i>')
            self.layout().addWidget(QLabel(warning), 4, 0)

    def __initUI__(self):

        # ---- Select Dataset

        self.directory = QLineEdit()
        self.directory.setReadOnly(True)
        self.directory.setMinimumWidth(400)

        btn_browse = QToolButtonSmall(icons.get_icon('openFile'))
        btn_browse.setToolTip('Select a datafile...')
        btn_browse.clicked.connect(self.select_dataset)

        msg = ('<font color=red size=2><i>Error : %s data file is '
               'not formatted correctly.</i></font>'
               ) % self._datatype.capitalize()
        self._msg = QLabel(msg)
        self._msg.setVisible(False)

        # Select Dataset Layout

        grp_dset = QGridLayout()
        row = 0
        text = "Select a valid %s datafile :" % self._datatype.lower()
        grp_dset.addWidget(QLabel(text), row, 0, 1, 3)
        row += 1
        grp_dset.addWidget(QLabel("File name :"), row, 0)
        grp_dset.addWidget(self.directory, row, 1)
        grp_dset.addWidget(btn_browse, row, 3)
        row += 1
        grp_dset.addWidget(self._msg, row, 1, 1, 3)

        grp_dset.setContentsMargins(0, 0, 0, 15)
        grp_dset.setColumnStretch(2, 100)
        grp_dset.setVerticalSpacing(15)

        # ----- Station Info Groupbox

        self._stn_name = QLineEdit()
        self._stn_name.setAlignment(Qt.AlignCenter)

        self._sid = QLineEdit()
        self._sid.setAlignment(Qt.AlignCenter)

        self._lat = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self._lat.setRange(-180, 180)

        self._lon = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self._lon.setRange(-180, 180)

        self._alt = myqt.QDoubleSpinBox(0, 3, 0.1, ' m')
        self._alt.setRange(-9999, 9999)

        self._prov = QLineEdit()
        self._prov.setAlignment(Qt.AlignCenter)

        # Info Groubox Layout

        self.grp_info = myqt.QGroupWidget()
        self.grp_info.setTitle("Dataset info")
        self.grp_info.setEnabled(False)
        self.grp_info.layout().setColumnStretch(2, 100)
        self.grp_info.layout().setSpacing(10)

        if self._datatype == 'water level':
            labels = ['Well name :', 'Well ID :']
        else:
            labels = ['Station name :', 'Station ID :']
        labels.extend(['Latitude :', 'Longitude :',
                       'Altitude :', 'Province :'])
        widgets = [self._stn_name, self._sid, self._lat,
                   self._lon, self._alt, self._prov]
        for label, widget in zip(labels, widgets):
            self._add_info_field(label, widget)

        # ----- Toolbar

        self._dset_name = QLineEdit()

        self.btn_ok = QPushButton('Import')
        self.btn_ok.setMinimumWidth(100)
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.accept_dataset)

        btn_cancel = QPushButton('Cancel')
        btn_cancel.setMinimumWidth(100)
        btn_cancel.clicked.connect(self.close)

        # Tool layout

        toolbar = QGridLayout()

        toolbar.addWidget(QLabel('Dataset name :'), 0, 0)
        toolbar.addWidget(self._dset_name, 0, 1)
        toolbar.addWidget(self.btn_ok, 0, 3)
        toolbar.addWidget(btn_cancel, 0, 4)

        toolbar.setSpacing(10)
        toolbar.setColumnStretch(2, 100)
        toolbar.setContentsMargins(0, 15, 0, 0)  # (L, T, R, B)

        # ---- Main Layout

        layout = QGridLayout(self)

        layout.addLayout(grp_dset, 0, 0)
        layout.addWidget(self.grp_info, 1, 0)
        layout.addLayout(toolbar, 2, 0)

        layout.setRowMinimumHeight(3, 15)

    def _add_info_field(self, label, widget):
        """Add a new field to the Station Info group box."""
        layout = self.grp_info.layout()
        row = layout.rowCount()
        layout.addWidget(QLabel(label), row, 0)
        layout.addWidget(widget, row, 1)

    # ---- Properties

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
        """Name that will be use to reference the dataset in the project."""
        return self._dset_name.text()

    @property
    def station_name(self):
        """Common name of the climate or piezomatric station."""
        return self._stn_name.text()

    @property
    def station_id(self):
        """Unique identifier of the climate or piezomatric station."""
        return self._sid.text()

    @property
    def province(self):
        """Province where the station is located."""
        return self._prov.text()

    @property
    def latitude(self):
        """Latitude in decimal degree of the station location."""
        return self._lat.value()

    @property
    def longitude(self):
        """Longitude in decimal degree of the station location."""
        return self._lon.value()

    @property
    def altitude(self):
        """Elevation of the station in meters above see level."""
        return self._alt.value()

    # ---- Dataset Handlers

    def select_dataset(self):
        """Opens a dialog to select a single datafile."""

        if self._datatype == 'water level':
            exts = '(*.csv;*.xls;*.xlsx)'
        elif self._datatype == 'daily weather':
            exts = '(*.csv;*.out)'
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Select a %s data file' % self._datatype,
            self.workdir, exts)

        for i in range(5):
            QCoreApplication.processEvents()

        if filename:
            self.workdir = os.path.dirname(filename)
            self.load_dataset(filename)

    def load_dataset(self, filename):
        """Loads the dataset and displays the information in the UI."""
        if not os.path.exists(filename):
            print('Path does not exist. Cannot open %s.' % filename)
            return

        # Load the Data :

        QApplication.setOverrideCursor(Qt.WaitCursor)
        msg = 'Loading %s data...' % self._datatype
        print(msg)
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)
        for i in range(5):
            QCoreApplication.processEvents()

        if self._datatype == 'water level':
            self._dataset = wlrd.read_water_level_datafile(filename)
        elif self._datatype == 'daily weather':
            self._dataset = wxrd.WXDataFrame(filename)
        QApplication.restoreOverrideCursor()

        # Update the GUI :

        self.directory.setText(filename)
        if self._dataset is None:
            self._msg.setVisible(True)
            self.btn_ok.setEnabled(False)
            self.grp_info.setEnabled(False)
            self.clear(clear_directory=False)
        else:
            self.grp_info.setEnabled(True)
            self._msg.setVisible(False)
            self.btn_ok.setEnabled(True)

            if self._datatype == 'water level':
                self._stn_name.setText(self._dataset['Well'])
                self._sid.setText(self._dataset['Well ID'])
                self._prov.setText(self._dataset['Province'])
                self._lat.setValue(self._dataset['Latitude'])
                self._lon.setValue(self._dataset['Longitude'])
                self._alt.setValue(self._dataset['Elevation'])
                self._dset_name.setText(self._dataset['Well'])
            elif self._datatype == 'daily weather':
                self._stn_name.setText(self._dataset['Station Name'])
                self._sid.setText(self._dataset['Climate Identifier'])
                self._prov.setText(self._dataset['Province'])
                self._lat.setValue(self._dataset['Latitude'])
                self._lon.setValue(self._dataset['Longitude'])
                self._alt.setValue(self._dataset['Elevation'])
                self._dset_name.setText(self._dataset['Station Name'])

    def accept_dataset(self):
        """Accept and emit the dataset."""
        if self.name == '':
            msg = 'Please enter a valid name for the dataset.'
            btn = QMessageBox.Ok
            QMessageBox.warning(self, 'Save dataset', msg, btn)
            return

        if self._datatype == 'water level':
            is_dsetname_exists = self.name in self.projet.wldsets
            del_dset = self.projet.del_wldset
        elif self._datatype == 'daily weather':
            is_dsetname_exists = self.name in self.projet.wxdsets
            del_dset = self.projet.del_wxdset

        if is_dsetname_exists:
            msg = ('The dataset <i>%s</i> already exists.'
                   ' Do you want tho replace the existing dataset?'
                   ' All data will be lost.') % self.name
            btn = QMessageBox.Yes | QMessageBox.No
            reply = QMessageBox.question(self, 'Save dataset', msg, btn)
            if reply == QMessageBox.No:
                return
            else:
                del_dset(self.name)

        # Update dataset attributes from UI and emit dataset :

        if self._datatype == 'water level':
            self._dataset['Well'] = self.station_name
            self._dataset['Well ID'] = self.station_id
        elif self._datatype == 'daily weather':
            self._dataset['Station Name'] = self.station_name
            self._dataset['Climate Identifier'] = self.station_id
        self._dataset['Province'] = self.province
        self._dataset['Latitude'] = self.latitude
        self._dataset['Longitude'] = self.longitude
        self._dataset['Elevation'] = self.altitude

        self.sig_new_dataset_imported.emit(str, self._dataset)
        self.close()

    # ---- Display Handlers

    def close(self):
        super(NewDatasetDialog, self).close()
        self.clear()

    def clear(self, clear_directory=True):
        if clear_directory:
            self.directory.clear()
        self._dataset = None
        self._dset_name.clear()
        self._stn_name.clear()
        self._prov.clear()
        self._lat.setValue(0)
        self._lon.setValue(0)
        self._alt.setValue(0)
        self._sid.clear()


# ---- if __name__ == '__main__'

if __name__ == '__main__':
    from reader_projet import ProjetReader
    import sys
    f = ('C:/Users/jsgosselin/OneDrive/Research/'
         'PostDoc - MDDELCC/Outils/BRF MontEst/'
         'BRF MontEst.what')
    p = ProjetReader(f)

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)
#
#    pm = ProjetManager(projet=f)
#    pm.show()

    # dm = DataManager(projet=p)
    # dm.show()

    new_wldset = NewDatasetDialog('water level')
    new_wxdset = NewDatasetDialog('daily weather')

    new_wldset.show()
    new_wxdset.show()

    app.exec_()
