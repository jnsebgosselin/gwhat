# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Imports: Standard Libraries

import os
import os.path as osp

# ---- Import: Third Party Libraries

from PyQt5.QtCore import Qt, QCoreApplication, QSize
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (QWidget, QComboBox, QGridLayout, QLabel,
                             QMessageBox, QLineEdit, QPushButton,
                             QFileDialog, QApplication, QDialog, QGroupBox)

# ---- Local library imports

from gwhat.meteo.weather_viewer import WeatherViewer, ExportWeatherButton
from gwhat.common.icons import QToolButtonSmall
from gwhat.common import icons
import gwhat.common.widgets as myqt
from gwhat.hydrograph4 import LatLong2Dist
import gwhat.projet.reader_waterlvl as wlrd
from gwhat.projet.reader_projet import INVALID_CHARS, is_dsetname_valid
import gwhat.meteo.weather_reader as wxrd
from gwhat.widgets.buttons import ToolBarWidget
from gwhat.widgets.spinboxes import StrSpinBox


class DataManager(QWidget):

    wldsetChanged = QSignal(object)
    wxdsetChanged = QSignal(object)

    def __init__(self, parent=None, projet=None, pm=None, pytesting=False):
        super(DataManager, self).__init__(parent)
        self._pytesting = pytesting
        self._projet = projet

        self.setWindowFlags(Qt.Window)
        self.setWindowIcon(icons.get_icon('master'))
        self.setMinimumWidth(250)

        self.weather_avg_graph = None

        self.new_waterlvl_win = NewDatasetDialog(
                'water level', parent, projet)
        self.new_waterlvl_win.sig_new_dataset_imported.connect(
                self.new_wldset_imported)

        self.new_weather_win = NewDatasetDialog(
                'daily weather', parent, projet)
        self.new_weather_win.sig_new_dataset_imported.connect(
                self.new_wxdset_imported)

        self.setup_manager()

        self.set_projet(projet)
        if pm:
            pm.currentProjetChanged.connect(self.set_projet)
            self.set_projet(pm.projet)

    def setup_manager(self):
        """Setup the layout of the manager."""
        layout = QGridLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.setup_wldset_mngr(), 0, 0)
        layout.addWidget(self.setup_wxdset_mngr(), 2, 0)

    def setup_wldset_mngr(self):
        """Setup the manager for the water level datasets."""

        # ---- Toolbar

        self.wldsets_cbox = QComboBox()
        self.wldsets_cbox.currentIndexChanged.connect(self.update_wldset_info)
        self.wldsets_cbox.currentIndexChanged.connect(self.wldset_changed)

        self.btn_load_wl = QToolButtonSmall(icons.get_icon('importFile'))
        self.btn_load_wl.setToolTip('Import a new water level dataset...')
        self.btn_load_wl.clicked.connect(self.import_wldataset)

        self.btn_del_wldset = QToolButtonSmall(icons.get_icon('clear'))
        self.btn_del_wldset.setToolTip('Delete current dataset.')
        self.btn_del_wldset.clicked.connect(self.del_current_wldset)

        wl_toolbar = ToolBarWidget()
        for widg in [self.btn_load_wl, self.btn_del_wldset]:
            wl_toolbar.addWidget(widg)

        # ---- Info Box

        self.well_info_widget = StrSpinBox()

        # ---- Main Layout

        grpbox = QGroupBox('Water Level Dataset : ')
        layout = QGridLayout(grpbox)
        layout.setSpacing(5)

        layout.addWidget(self.wldsets_cbox, 1, 0)
        layout.addWidget(self.well_info_widget, 2, 0)
        layout.addWidget(wl_toolbar, 3, 0)

        return grpbox

    def setup_wxdset_mngr(self):
        """Setup the manager for the weather datasets."""

        # ---- Toolbar

        self.wxdsets_cbox = QComboBox()
        self.wxdsets_cbox.currentIndexChanged.connect(self.update_wxdset_info)
        self.wxdsets_cbox.currentIndexChanged.connect(self.wxdset_changed)

        self.btn_load_meteo = QToolButtonSmall(icons.get_icon('importFile'))
        self.btn_load_meteo.setToolTip('Import a new weather dataset...')
        self.btn_load_meteo.clicked.connect(self.import_wxdataset)

        self.btn_del_wxdset = QToolButtonSmall(icons.get_icon('clear'))
        self.btn_del_wxdset.setToolTip('Delete current dataset.')
        self.btn_del_wxdset.clicked.connect(self.del_current_wxdset)

        btn_closest_meteo = QToolButtonSmall(icons.get_icon('closest_meteo'))
        btn_closest_meteo.setToolTip('<p>Select the weather station closest'
                                     ' from the observation well.</p>')
        btn_closest_meteo.clicked.connect(self.set_closest_wxdset)

        btn_weather_normals = QToolButtonSmall(icons.get_icon('meteo'))
        btn_weather_normals.setToolTip(
            "Show the normals for the current weather dataset.")
        btn_weather_normals.clicked.connect(self.show_weather_normals)

        self.btn_export_weather = ExportWeatherButton(workdir=self.workdir)
        self.btn_export_weather.setIconSize(QSize(20, 20))

        wx_toolbar = ToolBarWidget()
        for widg in [self.btn_load_meteo,
                     self.btn_del_wxdset, btn_closest_meteo,
                     btn_weather_normals, self.btn_export_weather]:
            wx_toolbar.addWidget(widg)

        # ---- Info Box

        self.meteo_info_widget = StrSpinBox()

        # ---- Main Layout

        grpbox = QGroupBox('Weather Dataset : ')
        layout = QGridLayout(grpbox)
        layout.setSpacing(5)

        layout.addWidget(self.wxdsets_cbox, 1, 0)
        layout.addWidget(self.meteo_info_widget, 2, 0)
        layout.addWidget(wx_toolbar, 3, 0)

        return grpbox

    @property
    def workdir(self):
        """Return the path where the project hdf5 file is saved."""
        if self.projet is None:
            return osp.dirname(os.getcwd())
        else:
            return osp.dirname(self.projet.filename)

    @property
    def projet(self):
        """Return the projet object."""
        return self._projet

    def set_projet(self, projet):
        """Set the namespace for the projet hdf5 file."""
        self._projet = projet
        if projet is not None:
            self.update_wldsets()
            self.update_wxdsets()

            self.update_wldset_info()
            self.update_wxdset_info()

            self.wldset_changed()

        self.btn_export_weather.set_model(self.get_current_wxdset())
        self.btn_export_weather.set_workdir(self.workdir)

        self.new_waterlvl_win.set_projet(projet)
        self.new_weather_win.set_projet(projet)

    # ---- Utilities

    def emit_warning(self, msg):
        btn = QMessageBox.Ok
        QMessageBox.warning(self, 'Warning', msg, btn)

    # ---- WL Dataset

    @property
    def wldsets(self):
        """Return a list of all the wldset saved in the project."""
        return [] if self.projet is None else self.projet.wldsets

    def wldataset_count(self):
        """Return the total number of wldset saved in the project."""
        return len(self.wldsets)

    def import_wldataset(self):
        """Open a dialog window to import a water level dataset from a file."""
        if self.projet is None:
            msg = ("Please first select a valid project or create a new one.")
            btn = QMessageBox.Ok
            QMessageBox.warning(self, 'Create dataset', msg, btn)
            return
        else:
            if self._pytesting:
                self.new_waterlvl_win.show()
            else:
                self.new_waterlvl_win.exec_()

    def new_wldset_imported(self, name, dataset):
        """
        Receives the new water level dataset, saves it in the project and
        update the GUI.
        """
        print("Saving the new water level dataset in the project...", end=" ")
        self.projet.add_wldset(name, dataset)
        self.update_wldsets(name)
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
        """Update the infos of the wldset."""
        wldset = self.get_current_wldset()
        if wldset is not None:
            model = ["Well : %s" % wldset['Well'],
                     "Well ID : %s" % wldset['Well ID'],
                     "Latitude : %0.3f°" % wldset['Latitude'],
                     "Longitude : %0.3f°" % wldset['Longitude'],
                     "Elevation : %0.1f m" % wldset['Elevation'],
                     "Municipality : %s" % wldset['Municipality'],
                     "Province : %s" % wldset['Province']]
        else:
            model = None
        self.well_info_widget.set_model(model)

    def wldset_changed(self):
        """Handle when the currently selected water level dataset changed."""
        self.wldsetChanged.emit(self.get_current_wldset())

    def get_current_wldset(self):
        """Return the currently selected water level dataset."""
        if self.wldsets_cbox.currentIndex() == -1:
            return None
        else:
            return self.projet.get_wldset(self.wldsets_cbox.currentText())

    def del_current_wldset(self):
        """Delete the currently selected water level dataset."""
        if self.wldsets_cbox.count() > 0:
            name = self.wldsets_cbox.currentText()
            msg = ('Do you want to delete the dataset <i>%s</i>?'
                   '<br><br>'
                   'All data will be deleted from the project database, '
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
        """Return a list of all the weather datasets saved in the project."""
        return [] if self.projet is None else self.projet.wxdsets

    def wxdataset_count(self):
        """Return the total number of weather datasets saved in the project."""
        return len(self.wxdsets)

    def import_wxdataset(self):
        """Open a dialog window to import a weather dataset from a file."""
        if self.projet is None:
            msg = ("Please first select a valid project or create a new one.")
            btn = QMessageBox.Ok
            QMessageBox.warning(self, 'Create dataset', msg, btn)
            return
        else:
            if self._pytesting:
                self.new_weather_win.show()
            else:
                self.new_weather_win.exec_()

    def new_wxdset_imported(self, name, dataset):
        """
        Receive the new weather dataset, save it in the project and
        update the GUI.
        """
        print("Saving the new weather dataset in the project.", end=" ")
        self.projet.add_wxdset(name, dataset)
        self.update_wxdsets(name)
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
        """Update the infos of the wxdset."""
        wxdset = self.get_current_wxdset()
        if wxdset is not None:
            model = ["Station : %s" % wxdset['Station Name'],
                     "Climate ID : %s" % wxdset['Climate Identifier'],
                     "Latitude : %0.3f°" % wxdset['Latitude'],
                     "Longitude : %0.3f°" % wxdset['Longitude'],
                     "Elevation : %0.1f m" % wxdset['Elevation'],
                     "Province : %s" % wxdset['Province']]
        else:
            model = None
        self.meteo_info_widget.set_model(model)

    def wxdset_changed(self):
        """Handle when the currently selected weather dataset changed."""
        self.btn_export_weather.set_model(self.get_current_wxdset())
        self.wxdsetChanged.emit(self.get_current_wxdset())

    def del_current_wxdset(self):
        """Delete the currently selected weather dataset."""
        if self.wxdsets_cbox.count() > 0:
            name = self.wxdsets_cbox.currentText()
            msg = ('Do you want to delete the weather dataset <i>%s</i>?'
                   '<br><br>'
                   'All data will be deleted from the project database, '
                   'but the original data files will be preserved') % name
            reply = QMessageBox.question(
                self, 'Delete current dataset', msg,
                QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
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
            return

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

    def show_weather_normals(self):
        """Show the weather normals for the current weather dataset."""
        if self.get_current_wxdset() is None:
            return
        if self.weather_avg_graph is None:
            self.weather_avg_graph = WeatherViewer()

        self.weather_avg_graph.set_workdir(self.workdir)
        self.weather_avg_graph.set_weather_dataset(self.get_current_wxdset())
        self.weather_avg_graph.show()


class NewDatasetDialog(QDialog):
    """
    A dialog window where water level and weather datasets can be imported
    into the project.
    """

    ConsoleSignal = QSignal(str)
    sig_new_dataset_imported = QSignal(str, object)

    DATATYPES = ['water level', 'daily weather']

    def __init__(self, datatype, parent=None, projet=None):
        super(NewDatasetDialog, self).__init__(parent)

        if datatype.lower() not in self.DATATYPES:
            raise ValueError("datatype value must be :", self.DATATYPES)
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

        self.btn_browse = QToolButtonSmall(icons.get_icon('openFile'))
        self.btn_browse.setToolTip('Select a datafile...')
        self.btn_browse.clicked.connect(self.select_dataset)

        url_i = "https://gwhat.readthedocs.io/en/latest/manage_data.html"
        msg = ("<font color=red size=2><i>"
               "The %s data file is not formatted correctly.<br>"
               "Please consult the <a href=\"%s\">documentation</a>"
               " for detailed information<br>"
               "on how to format your input data files correctly."
               "</i></font>"
               ) % (self._datatype.capitalize(), url_i)
        self._error_lbl = QLabel(msg)
        self._error_lbl.setVisible(False)
        self._error_lbl.setOpenExternalLinks(True)

        # Select Dataset Layout

        grp_dset = QGridLayout()
        row = 0
        text = "Select a valid %s datafile :" % self._datatype.lower()
        grp_dset.addWidget(QLabel(text), row, 0, 1, 3)
        row += 1
        grp_dset.addWidget(QLabel("File name :"), row, 0)
        grp_dset.addWidget(self.directory, row, 1)
        grp_dset.addWidget(self.btn_browse, row, 3)
        row += 1
        grp_dset.addWidget(self._error_lbl, row, 1, 1, 3)

        grp_dset.setContentsMargins(0, 0, 0, 15)
        grp_dset.setColumnStretch(1, 100)
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

        self.grp_info = QGroupBox("Dataset info :")
        self.grp_info.setEnabled(False)
        self.grp_info.setLayout(QGridLayout())
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
        self._dset_name.setEnabled(False)

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
        layout.setRowStretch(10, 100)
        layout.setColumnStretch(0, 100)

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
        """Load the dataset and display the information in the UI."""
        if not osp.exists(filename):
            print('Path does not exist. Cannot open %s.' % filename)
            return

        # Load the Data :

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.ConsoleSignal.emit(
            "<font color=black>Loading %s data...</font>" % self._datatype)
        for i in range(5):
            QCoreApplication.processEvents()

        try:
            if self._datatype == 'water level':
                self._dataset = wlrd.read_water_level_datafile(filename)
            elif self._datatype == 'daily weather':
                self._dataset = wxrd.WXDataFrame(filename)
        except Exception:
            self._dataset = None

        self.update_gui(filename)
        QApplication.restoreOverrideCursor()

    def update_gui(self, filename=None):
        """
        Display the values stored in the dataset. Disable the UI and show
        an error message if the dataset is not valid.
        """
        if filename is not None:
            self.directory.setText(filename)
        else:
            self.directory.clear()

        if self._dataset is None:
            self._dset_name.clear()
            self._stn_name.clear()
            self._prov.clear()
            self._lat.setValue(0)
            self._lon.setValue(0)
            self._alt.setValue(0)
            self._sid.clear()
        else:
            self._prov.setText(self._dataset['Province'])
            self._lat.setValue(self._dataset['Latitude'])
            self._lon.setValue(self._dataset['Longitude'])
            self._alt.setValue(self._dataset['Elevation'])
            if self._datatype == 'water level':
                self._stn_name.setText(self._dataset['Well'])
                self._sid.setText(self._dataset['Well ID'])
                dsetname = self._dataset['Well']
            elif self._datatype == 'daily weather':
                self._stn_name.setText(self._dataset['Station Name'])
                self._sid.setText(self._dataset['Climate Identifier'])
                dsetname = self._dataset['Station Name']
            # We replace the invalid characters to avoid problems when
            # saving the dataset to the hdf5 format.
            for char in INVALID_CHARS:
                dsetname = dsetname.replace(char, '_')
            self._dset_name.setText(dsetname)

        self._error_lbl.setVisible(
            self._dataset is None and self.directory.text() != '')
        self.btn_ok.setEnabled(self._dataset is not None)
        self.grp_info.setEnabled(self._dataset is not None)
        self._dset_name.setEnabled(self._dataset is not None)

    def accept_dataset(self):
        """Accept and emit the dataset."""
        if not is_dsetname_valid(self.name):
            msg = ('''
                   <p>Please enter a valid name for the dataset.<\p>
                   <p>A dataset name must be at least one charater long
                   and can't contain any of the following special
                   characters:<\p>
                   <center>\ / : * ? " < > |<\center>
                   ''')
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

        self.hide()
        self.sig_new_dataset_imported.emit(self.name, self._dataset)
        self.close()

    # ---- Display Handlers

    def close(self):
        """Qt method override."""
        super(NewDatasetDialog, self).close()
        self._dataset = None
        self.directory.clear()
        self.update_gui()


# %% if __name__ == '__main__'

if __name__ == '__main__':
    from reader_projet import ProjetReader
    import sys
    projet = ProjetReader("C:/Users/jsgosselin/gwhat/Projects/Example/Example.gwt")

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)

    # pm = ProjetManager(projet=f)
    # pm.show()

    dm = DataManager(projet=projet)
    dm.show()

    app.exec_()
