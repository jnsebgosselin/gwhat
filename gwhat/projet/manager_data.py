# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------


# ---- Standard Library imports
import os
import os.path as osp

# ---- Third party imports
import numpy as np
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (
    QWidget, QCheckBox, QComboBox, QGridLayout, QLabel, QMessageBox,
    QLineEdit, QPushButton, QFileDialog, QApplication, QDialog, QGroupBox)

# ---- Local library imports
from gwhat.config.main import CONF
from gwhat.config.ospath import (
    get_select_file_dialog_dir, set_select_file_dialog_dir)
from gwhat.meteo.weather_viewer import WeatherViewer, ExportWeatherButton
from gwhat.utils.icons import QToolButtonSmall
from gwhat.utils import icons
import gwhat.common.widgets as myqt
from gwhat.common.utils import calc_dist_from_coord
from gwhat.projet.reader_waterlvl import WLDataset
from gwhat.projet.reader_projet import INVALID_CHARS, is_dsetname_valid
from gwhat.meteo.weather_reader import WXDataFrame
from gwhat.widgets.buttons import ToolBarWidget
from gwhat.widgets.spinboxes import StrSpinBox


class DataManager(QWidget):

    wldsetChanged = QSignal(object)
    wxdsetChanged = QSignal(object)
    sig_new_console_msg = QSignal(str)

    def __init__(self, parent=None, projet=None, pm=None, pytesting=False):
        super(DataManager, self).__init__(parent)
        self._pytesting = pytesting
        self._projet = projet
        self._confirm_before_deleting_dset = True

        self._wldset = None
        self._wxdset = None

        self.setWindowFlags(Qt.Window)
        self.setWindowIcon(icons.get_icon('master'))
        self.setMinimumWidth(250)

        self.weather_avg_graph = None

        self.new_waterlvl_win = NewDatasetDialog(
            'water level', parent, projet)
        self.new_waterlvl_win.sig_new_dataset_imported.connect(
            self.add_new_wldset)

        self.new_weather_win = NewDatasetDialog(
            'daily weather', parent, projet)
        self.new_weather_win.sig_new_dataset_imported.connect(
            self.add_new_wxdset)

        self.setup_manager()

        self.set_projet(projet)
        if pm:
            pm.currentProjetChanged.connect(self.set_projet)
            self.set_projet(pm.projet)

    def close(self):
        """Close this data manager."""
        if self.weather_avg_graph is not None:
            CONF.set('weather_normals_viewer',
                     'graphs_labels_language',
                     self.weather_avg_graph.get_language())
            self.weather_avg_graph.close()

    def setup_manager(self):
        """Setup the layout of the manager."""
        layout = QGridLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.setup_wldset_mngr(), 0, 0)
        layout.addWidget(self.setup_wxdset_mngr(), 2, 0)

    def setup_wldset_mngr(self):
        """Setup the manager for the water level datasets."""

        # Setup the toolbar.
        self.wldsets_cbox = QComboBox()
        self.wldsets_cbox.currentIndexChanged.connect(self.wldset_changed)

        self.btn_load_wl = QToolButtonSmall(icons.get_icon('importFile'))
        self.btn_load_wl.setToolTip('Import a new water level dataset...')
        self.btn_load_wl.clicked.connect(self.select_wldatasets)

        self.btn_del_wldset = QToolButtonSmall('delete_data')
        self.btn_del_wldset.setToolTip('Delete current dataset.')
        self.btn_del_wldset.clicked.connect(self.del_current_wldset)

        wl_toolbar = ToolBarWidget()
        for widg in [self.btn_load_wl, self.btn_del_wldset]:
            wl_toolbar.addWidget(widg)

        # Setup the dataset information box.
        self.well_info_widget = StrSpinBox()

        # ---- Setup the main layout.
        grpbox = QGroupBox('Water Level Dataset')
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
        self.wxdsets_cbox.currentIndexChanged.connect(self.wxdset_changed)

        self.btn_load_meteo = QToolButtonSmall(icons.get_icon('importFile'))
        self.btn_load_meteo.setToolTip('Import a new weather dataset...')
        self.btn_load_meteo.clicked.connect(self.select_wxdatasets)

        self.btn_del_wxdset = QToolButtonSmall('delete_data')
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

        self.btn_export_weather = ExportWeatherButton()
        self.btn_export_weather.setIconSize(icons.get_iconsize('small'))

        wx_toolbar = ToolBarWidget()
        for widg in [self.btn_load_meteo,
                     self.btn_del_wxdset, btn_closest_meteo,
                     btn_weather_normals, self.btn_export_weather]:
            wx_toolbar.addWidget(widg)

        # ---- Info Box

        self.meteo_info_widget = StrSpinBox()

        # ---- Main Layout

        grpbox = QGroupBox('Weather Dataset')
        layout = QGridLayout(grpbox)
        layout.setSpacing(5)

        layout.addWidget(self.wxdsets_cbox, 1, 0)
        layout.addWidget(self.meteo_info_widget, 2, 0)
        layout.addWidget(wx_toolbar, 3, 0)

        return grpbox

    @property
    def projet(self):
        """Return the projet object."""
        return self._projet

    def set_projet(self, projet):
        """Set the namespace for the projet hdf5 file."""
        self._projet = projet
        self._wldset = None
        self._wxdset = None
        if projet is not None:
            self.update_wldsets(projet.get_last_opened_wldset())
            self.update_wxdsets(projet.get_last_opened_wxdset())
            self.wldset_changed()

        self.btn_export_weather.set_model(self.get_current_wxdset())

        self.new_waterlvl_win.set_projet(projet)
        self.new_weather_win.set_projet(projet)

    # ---- Utilities

    def emit_warning(self, msg):
        btn = QMessageBox.Ok
        QMessageBox.warning(self, 'Warning', msg, btn)

    def confirm_del_dataset(self, dsetname, dsettype):
        """
        Show a message box asking the user confirmation before deleting
        a dataset. Return the user's answer and whether the
        'do not show this message again' checkbox has been checked or not.
        """
        msg_box = QMessageBox(
            QMessageBox.Question,
            "Delete {} dataset '{}'".format(dsettype, dsetname),
            ("Do you want to delete the {} dataset <i>{}</i>?<br><br>"
             "All data will be deleted from the project, but the "
             "original data files will be preserved.<br>"
             ).format(dsettype, dsetname),
            buttons=QMessageBox.Yes | QMessageBox.Cancel,
            parent=self)
        checkbox = QCheckBox("Don't show this message again.")
        msg_box.setCheckBox(checkbox)

        reply = msg_box.exec_()
        return reply, not checkbox.isChecked()

    # ---- WL Dataset
    @property
    def wldsets(self):
        """Return a list of all the wldset saved in the project."""
        return [] if self.projet is None else self.projet.wldsets

    def wldataset_count(self):
        """Return the total number of wldset saved in the project."""
        return len(self.wldsets)

    def select_wldatasets(self):
        """
        Open a file dialog to allow the user to select one or more input
        water level datafiles.
        """
        if self.projet is None:
            QMessageBox.warning(
                self, 'Import Dataset Error',
                "Please select a valid project first or create a new one.",
                QMessageBox.Ok)
            return

        dialog = QFileDialog(self)
        dialog.setWindowTitle('Select Water Level Data Files')
        dialog.setNameFilters(['(*.csv;*.xls;*.xlsx)'])
        dialog.setDirectory(get_select_file_dialog_dir())
        dialog.setFileMode(QFileDialog.ExistingFiles)
        if dialog.exec_():
            set_select_file_dialog_dir(dialog.directory().absolutePath())
            filenames = dialog.selectedFiles()
            self.import_wldatasets(filenames)

    def import_wldatasets(self, filenames):
        """Import water level datasets from a list of files."""
        self.new_waterlvl_win.load_datasets(filenames)
        if self._pytesting:
            self.new_waterlvl_win.show()
        else:
            self.new_waterlvl_win.exec_()

    def add_new_wldset(self, name, dataset):
        """
        Add a new water level dataset to the project and update the GUI.
        """
        print("Add new water level dataset to the project...")
        if name in self.projet.wldsets:
            self.projet.del_wldset(name)
            self._wldset = None
        self.projet.add_wldset(name, dataset)
        self.update_wldsets(name)
        self.wldset_changed()
        print("New water level dataset added successfully.")

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
        QApplication.processEvents()
        self.update_wldset_info()
        self.wldsetChanged.emit(self.get_current_wldset())

    def get_current_wldset(self):
        """Return the currently selected water level dataset."""
        if self.wldsets_cbox.currentIndex() == -1:
            self._wldset = None
        else:
            cbox_text = self.wldsets_cbox.currentText()
            if self._wldset is None or self._wldset.name != cbox_text:
                self._wldset = self.projet.get_wldset(cbox_text)
        return self._wldset

    def set_current_wldset(self, name):
        """Set the current water level from its name."""
        self.wldsets_cbox.blockSignals(True)
        self.wldsets_cbox.setCurrentIndex(self.wldsets_cbox.findText(name))
        self.wldsets_cbox.blockSignals(False)
        self.wldset_changed()

    def del_current_wldset(self):
        """Delete the currently selected water level dataset."""
        if self.wldsets_cbox.count() > 0:
            dsetname = self.wldsets_cbox.currentText()
            if self._confirm_before_deleting_dset:
                reply, dont_show_again = self.confirm_del_dataset(
                    dsetname, 'water level')
                if reply == QMessageBox.Cancel:
                    return
                elif reply == QMessageBox.Yes:
                    self._confirm_before_deleting_dset = dont_show_again
            self._wldset = None
            self.projet.del_wldset(dsetname)
            self.update_wldsets()
            self.wldset_changed()
            self.sig_new_console_msg.emit((
                "<font color=black>Water level dataset <i>{}</i> deleted "
                "successfully.</font>").format(dsetname))

    # ---- WX Dataset
    @property
    def wxdsets(self):
        """Return a list of all the weather datasets saved in the project."""
        return [] if self.projet is None else self.projet.wxdsets

    def wxdataset_count(self):
        """Return the total number of weather datasets saved in the project."""
        return len(self.wxdsets)

    def select_wxdatasets(self):
        """
        Open a file dialog to allow the user to select one or more input
        weather datafiles.
        """
        if self.projet is None:
            QMessageBox.warning(
                self, 'Import Dataset Error',
                "Please select a valid project first or create a new one.",
                QMessageBox.Ok)
            return

        dialog = QFileDialog(self)
        dialog.setWindowTitle('Select Weather Data Files')
        dialog.setNameFilters(['(*.csv;*.xls;*.xlsx)'])
        dialog.setDirectory(get_select_file_dialog_dir())
        dialog.setFileMode(QFileDialog.ExistingFiles)
        if dialog.exec_():
            set_select_file_dialog_dir(dialog.directory().absolutePath())
            filenames = dialog.selectedFiles()
            self.import_wxdatasets(filenames)

    def import_wxdatasets(self, filenames):
        """Import weather datasets from a list of files."""
        self.new_weather_win.load_datasets(filenames)
        if self._pytesting:
            self.new_weather_win.show()
        else:
            self.new_weather_win.exec_()

    def add_new_wxdset(self, name, dataset):
        """
        Add a new weather dataset to the project and update the GUI.
        """
        print("Add new weather dataset to the project...")
        if name in self.projet.wxdsets:
            self.projet.del_wxdset(name)
            self._wxdset = None
        self.projet.add_wxdset(name, dataset)
        self.update_wxdsets(name)
        self.wxdset_changed()
        print("New weather dataset added successfully.")

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
            model = ["Station : %s" % wxdset.metadata['Station Name'],
                     "Station ID : %s" % wxdset.metadata['Station ID'],
                     "Latitude : %0.3f°" % wxdset.metadata['Latitude'],
                     "Longitude : %0.3f°" % wxdset.metadata['Longitude'],
                     "Elevation : %0.1f m" % wxdset.metadata['Elevation'],
                     "Location : %s" % wxdset.metadata['Location']]
        else:
            model = None
        self.meteo_info_widget.set_model(model)

    def wxdset_changed(self):
        """Handle when the currently selected weather dataset changed."""
        QApplication.processEvents()
        self.update_wxdset_info()
        self.btn_export_weather.set_model(self.get_current_wxdset())
        self.wxdsetChanged.emit(self.get_current_wxdset())

    def del_current_wxdset(self):
        """Delete the currently selected weather dataset."""
        if self.wxdsets_cbox.count() > 0:
            dsetname = self.wxdsets_cbox.currentText()
            if self._confirm_before_deleting_dset:
                reply, dont_show_again = self.confirm_del_dataset(
                    dsetname, 'weather')
                if reply == QMessageBox.Cancel:
                    return
                elif reply == QMessageBox.Yes:
                    self._confirm_before_deleting_dset = dont_show_again
            self._wxdset = None
            self.projet.del_wxdset(dsetname)
            self.update_wxdsets()
            self.wxdset_changed()
            self.sig_new_console_msg.emit((
                "<font color=black>Weather dataset <i>{}</i> deleted "
                "successfully.</font>").format(dsetname))

    def get_current_wxdset(self):
        """Return the currently selected weather dataset dataframe."""
        if self.wxdsets_cbox.currentIndex() == -1:
            self._wxdset = None
        else:
            cbox_text = self.wxdsets_cbox.currentText()
            if self._wxdset is None or self._wxdset.name != cbox_text:
                self._wxdset = self.projet.get_wxdset(cbox_text)
        return self._wxdset

    def set_current_wxdset(self, name):
        """Set the current weather dataset from its name."""
        self.wxdsets_cbox.blockSignals(True)
        self.wxdsets_cbox.setCurrentIndex(self.wxdsets_cbox.findText(name))
        self.wxdsets_cbox.blockSignals(False)
        self.wxdset_changed()

    def set_closest_wxdset(self):
        """
        Set the weather dataset of the station that is closest to the
        groundwater observation well.
        """
        if self._wldset is None or self.wxdataset_count() == 0:
            return None

        dist = calc_dist_from_coord(self._wldset['Latitude'],
                                    self._wldset['Longitude'],
                                    self.projet.get_wxdsets_lat(),
                                    self.projet.get_wxdsets_lon())
        closest_station = self.wxdsets[np.argmin(dist)]
        self.set_current_wxdset(closest_station)
        return closest_station

    def show_weather_normals(self):
        """Show the weather normals for the current weather dataset."""
        if self.get_current_wxdset() is None:
            return
        if self.weather_avg_graph is None:
            self.weather_avg_graph = WeatherViewer()
            self.weather_avg_graph.set_language(
                CONF.get('weather_normals_viewer', 'graphs_labels_language'))
        self.weather_avg_graph.set_weather_dataset(self.get_current_wxdset())
        self.weather_avg_graph.show()
        self.weather_avg_graph.raise_()


class NewDatasetDialog(QDialog):
    """
    A dialog window where water level and weather datasets can be imported
    into the project.
    """

    ConsoleSignal = QSignal(str)
    sig_new_dataset_imported = QSignal(str, object)
    sig_new_dataset_loaded = QSignal(str)

    DATATYPES = ['water level', 'daily weather']

    def __init__(self, datatype, parent=None, projet=None):
        super(NewDatasetDialog, self).__init__(parent)

        if datatype.lower() not in self.DATATYPES:
            raise ValueError("datatype value must be :", self.DATATYPES)
        self._datatype = datatype.lower()

        self.setWindowTitle('Import {} Datasets'.format(datatype.title()))
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowFlags(Qt.Window |
                            Qt.CustomizeWindowHint |
                            Qt.WindowCloseButtonHint)

        self.set_projet(projet)
        self._dataset = None
        self._len_filenames = 0
        self._queued_filenames = []
        self._import_progress = 0

        self.__initUI__()

    def __initUI__(self):
        # Setup the guid to select an input dataset file.
        self.directory = QLineEdit()
        self.directory.setReadOnly(True)
        self.directory.setMinimumWidth(400)

        self.btn_browse = QToolButtonSmall(icons.get_icon('folder_open'))
        self.btn_browse.setToolTip('Select a datafile...')
        self.btn_browse.clicked.connect(self.select_dataset)

        url_i = "https://gwhat.readthedocs.io/en/latest/manage_data.html"
        msg = ("<font color=red size=2><i>"
               "This %s data file is not formatted correctly. "
               "Please consult the <a href=\"%s\">documentation</a> "
               "for detailed information on how to format your input "
               "data files correctly."
               "</i></font>"
               ) % (self._datatype.lower(), url_i)
        self._error_lbl = QLabel(msg)
        self._error_lbl.setVisible(False)
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setOpenExternalLinks(True)

        # Select Dataset Layout.
        grp_dset = QGridLayout()
        grp_dset.addWidget(QLabel("File name :"), 1, 0)
        grp_dset.addWidget(self.directory, 1, 1)
        grp_dset.addWidget(self.btn_browse, 1, 2)
        grp_dset.addWidget(self._error_lbl, 2, 1)

        grp_dset.setContentsMargins(0, 0, 0, 15)
        grp_dset.setColumnStretch(1, 100)
        grp_dset.setVerticalSpacing(15)

        # Set the station info groupbox.
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

        # Setup the info groubox layout.
        self.grp_info = QGroupBox("Dataset info :")
        self.grp_info.setEnabled(False)
        grp_info_layout = QGridLayout(self.grp_info)
        grp_info_layout.setColumnStretch(2, 100)

        if self._datatype == 'water level':
            labels = ['Well name :', 'Well ID :', 'Latitude :', 'Longitude :',
                      'Altitude :', 'Province :']
        else:
            labels = ['Station name :', 'Station ID :', 'Latitude :',
                      'Longitude :', 'Altitude :', 'Location :']
        widgets = [self._stn_name, self._sid, self._lat,
                   self._lon, self._alt, self._prov]
        for label, widget in zip(labels, widgets):
            self._add_info_field(label, widget)

        # Setup the dataset name.
        self._dset_name = QLineEdit()
        self._dset_name.setEnabled(False)

        dataset_name_layout = QGridLayout()
        dataset_name_layout.setContentsMargins(0, 15, 0, 0)
        dataset_name_layout.setColumnStretch(1, 1)
        dataset_name_layout.addWidget(QLabel('Dataset name :'), 0, 0)
        dataset_name_layout.addWidget(self._dset_name, 0, 1)

        # Setup the toolbar.
        self._progress_label = QLabel("File {} of {}".format(
            self._import_progress, self._len_filenames))

        self.btn_ok = QPushButton('Import')
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.accept_dataset)

        self.btn_skip = QPushButton('Skip')
        self.btn_skip.setEnabled(False)
        self.btn_skip.clicked.connect(self.load_next_queued_dataset)

        btn_cancel = QPushButton('Cancel')
        btn_cancel.clicked.connect(self.close)

        toolbar = QGridLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.addWidget(self._progress_label, 0, 0)
        toolbar.setColumnStretch(1, 100)
        toolbar.addWidget(self.btn_ok, 0, 2)
        toolbar.addWidget(self.btn_skip, 0, 3)
        toolbar.addWidget(btn_cancel, 0, 4)

        # Setup the main layout.
        layout = QGridLayout(self)

        layout.addLayout(grp_dset, 0, 0)
        layout.addWidget(self.grp_info, 1, 0)
        layout.setRowStretch(2, 100)
        layout.addLayout(dataset_name_layout, 3, 0)
        layout.addLayout(toolbar, 4, 0)

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
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Select a {} data file'.format(self._datatype),
            get_select_file_dialog_dir(),
            '(*.csv;*.xls;*.xlsx)')
        if filename:
            set_select_file_dialog_dir(osp.dirname(filename))
            self.load_dataset(filename)

    def load_dataset(self, filename):
        """Load the dataset and display the information in the UI."""
        if not osp.exists(filename):
            print('Path does not exist. Cannot open %s.' % filename)
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.ConsoleSignal.emit(
            "<font color=black>Loading %s data...</font>" % self._datatype)
        for i in range(5):
            QCoreApplication.processEvents()

        try:
            if self._datatype == 'water level':
                self._dataset = WLDataset(filename)
            elif self._datatype == 'daily weather':
                self._dataset = WXDataFrame(filename)
        except Exception as e:
            print(e)
            self._dataset = None

        self.update_gui(filename)
        QApplication.restoreOverrideCursor()
        self.sig_new_dataset_loaded.emit(filename)

    def load_datasets(self, filenames):
        """Start the process of loading datasets from a list of file names."""
        self._len_filenames = len(filenames)
        self._queued_filenames = filenames
        self._import_progress = 1
        current_filename = self._queued_filenames.pop(0)
        self.btn_skip.setEnabled(len(self._queued_filenames) > 0)
        self.load_dataset(current_filename)

    def update_gui(self, filename=None):
        """
        Display the values stored in the dataset. Disable the UI and show
        an error message if the dataset is not valid.
        """
        self._progress_label.setText("File {} of {}".format(
            self._import_progress, self._len_filenames))

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
            if self._datatype == 'water level':
                self._prov.setText(self._dataset['Province'])
                self._lat.setValue(self._dataset['Latitude'])
                self._lon.setValue(self._dataset['Longitude'])
                self._alt.setValue(self._dataset['Elevation'])
                self._stn_name.setText(self._dataset['Well'])
                self._sid.setText(self._dataset['Well ID'])
                dsetname = '{} ({})'.format(
                    self._dataset['Well'],
                    self._dataset['Well ID'])
            elif self._datatype == 'daily weather':
                self._prov.setText(self._dataset.metadata['Location'])
                self._lat.setValue(self._dataset.metadata['Latitude'])
                self._lon.setValue(self._dataset.metadata['Longitude'])
                self._alt.setValue(self._dataset.metadata['Elevation'])
                self._stn_name.setText(self._dataset.metadata['Station Name'])
                self._sid.setText(self._dataset.metadata['Station ID'])
                dsetname = self._dataset.metadata['Station Name']
                dsetname = '{} ({})'.format(
                    self._dataset.metadata['Station Name'],
                    self._dataset.metadata['Station ID'])
            # We replace the invalid characters to avoid problems when
            # saving the dataset to the hdf5 format.
            for char in INVALID_CHARS:
                dsetname = dsetname.replace(char, '_')
            self._dset_name.setText(dsetname)

        # self._error_lbl.setVisible(
        #     self._dataset is None and self.directory.text() != '')
        self.btn_ok.setEnabled(self._dataset is not None)
        self.grp_info.setEnabled(self._dataset is not None)
        self._dset_name.setEnabled(self._dataset is not None)

    def load_next_queued_dataset(self):
        """Load the data from the next data file in the queue."""
        self._import_progress += 1
        current_filename = self._queued_filenames.pop(0)
        self.btn_skip.setEnabled(len(self._queued_filenames) > 0)
        self.load_dataset(current_filename)

    def accept_dataset(self):
        """Accept and emit the dataset."""
        if not is_dsetname_valid(self.name):
            msg = ('''
                   <p>Please enter a valid name for the dataset.</p>
                   <p>A dataset name must be at least one charater long
                   and can't contain any of the following special
                   characters:</p>
                   <center>\\ / : * ? " < > |</center>
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
                   ' Do you want to replace the existing dataset?'
                   ' All data will be lost.') % self.name
            btn = QMessageBox.Yes | QMessageBox.No
            reply = QMessageBox.question(self, 'Save dataset', msg, btn)
            if reply == QMessageBox.No:
                return

        # Update dataset attributes from UI and emit dataset.
        self._update_attributes_from_ui()
        self.sig_new_dataset_imported.emit(self.name, self._dataset)

        if len(self._queued_filenames):
            self.load_next_queued_dataset()
        else:
            self.hide()
            self.close()

    # ---- Display Handlers
    def close(self):
        """Qt method override."""
        super(NewDatasetDialog, self).close()
        self._dataset = None
        self.directory.clear()
        self.update_gui()

    def _update_attributes_from_ui(self):
        if self._datatype == 'water level':
            self._dataset['Well'] = self.station_name
            self._dataset['Well ID'] = self.station_id
            self._dataset['Province'] = self.province
            self._dataset['Latitude'] = self.latitude
            self._dataset['Longitude'] = self.longitude
            self._dataset['Elevation'] = self.altitude
        elif self._datatype == 'daily weather':
            self._dataset.metadata['Station Name'] = self.station_name
            self._dataset.metadata['Station ID'] = self.station_id
            self._dataset.metadata['Location'] = self.province
            self._dataset.metadata['Latitude'] = self.latitude
            self._dataset.metadata['Longitude'] = self.longitude
            self._dataset.metadata['Elevation'] = self.altitude


if __name__ == '__main__':
    import sys
    from gwhat.projet.reader_projet import ProjetReader

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)

    dm = DataManager(projet=ProjetReader(
        "C:\\Users\\User\\gwhat\\Projects\\Example\\Example.gwt"))
    dm.show()

    app.exec_()
