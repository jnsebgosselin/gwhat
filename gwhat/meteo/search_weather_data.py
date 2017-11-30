# -*- coding: utf-8 -*-

# Copyright © 2014-2017 Jean-Sebastien Gosselin
# email: jean-sebastien.gosselin@ete.inrs.ca
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports

from datetime import datetime
import sys
import os

# ---- Third party imports

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (QWidget, QLabel, QDoubleSpinBox, QComboBox,
                             QFrame, QGridLayout, QSpinBox, QPushButton,
                             QDesktopWidget, QApplication,
                             QFileDialog, QGroupBox)

# ---- Local imports

from gwhat.common import IconDB, StyleDB
from gwhat.meteo.weather_stationlist import WeatherSationView
from gwhat.meteo.weather_station_finder import (WeatherStationFinder,
                                                PROV_NAME_ABB)


class WeatherStationBrowser(QWidget):
    """
    Widget that allows the user to browse and select ECCC climate stations.
    """

    ConsoleSignal = QSignal(str)
    staListSignal = QSignal(list)

    PROV_NAME = [x[0].title() for x in PROV_NAME_ABB]
    PROV_ABB = [x[1] for x in PROV_NAME_ABB]

    def __init__(self, parent=None):
        super(WeatherStationBrowser, self).__init__(parent)
        self.stn_finder = WeatherStationFinder()
        self.station_table = WeatherSationView()
        self.__initUI__()
        self.station_table.set_geocoord((self.lat, -self.lon))
        self.proximity_grpbox_toggled()

    @property
    def stationlist(self):
        return self.station_table.get_stationlist()

    @property
    def search_by(self):
        return ['proximity', 'province'][self.tab_widg.currentIndex()]

    @property
    def prov(self):
        if self.prov_widg.currentIndex() == 0:
            return self.PROV_ABB
        else:
            return self.PROV_ABB[self.prov_widg.currentIndex()-1]

    @property
    def lat(self):
        return self.lat_spinBox.value()

    def set_lat(self, x, silent=True):
        if silent:
            self.lat_spinBox.blockSignals(True)
        self.lat_spinBox.setValue(x)
        self.lat_spinBox.blockSignals(False)

    @property
    def lon(self):
        return self.lon_spinBox.value()

    def set_lon(self, x, silent=True):
        if silent:
            self.lon_spinBox.blockSignals(True)
        self.lon_spinBox.setValue(x)
        self.lon_spinBox.blockSignals(False)

    @property
    def rad(self):
        return int(self.radius_SpinBox.currentText()[:-3])

    @property
    def prox(self):
        if self.prox_grpbox.isChecked():
            return (self.lat, -self.lon, self.rad)
        else:
            return None

    @property
    def year_min(self):
        return int(self.minYear.value())

    def set_yearmin(self, x, silent=True):
        if silent:
            self.minYear.blockSignals(True)
        self.minYear.setValue(x)
        self.minYear.blockSignals(False)

    @property
    def year_max(self):
        return int(self.maxYear.value())

    def set_yearmax(self, x, silent=True):
        if silent:
            self.maxYear.blockSignals(True)
        self.maxYear.setValue(x)
        self.maxYear.blockSignals(False)

    @property
    def nbr_of_years(self):
        return int(self.nbrYear.value())

    def set_yearnbr(self, x, silent=True):
        if silent:
            self.nbrYear.blockSignals(True)
        self.nbrYear.setValue(x)
        self.nbrYear.blockSignals(False)

    def __initUI__(self):
        self.setWindowTitle('Weather Stations Browser')
        self.setWindowIcon(IconDB().master)
        self.setWindowFlags(Qt.Window)

        now = datetime.now()

        # ---- Tab Widget Search

        # ---- Proximity filter groupbox

        label_Lat = QLabel('Latitude :')
        label_Lat2 = QLabel('North')

        self.lat_spinBox = QDoubleSpinBox()
        self.lat_spinBox.setAlignment(Qt.AlignCenter)
        self.lat_spinBox.setSingleStep(0.1)
        self.lat_spinBox.setValue(0)
        self.lat_spinBox.setMinimum(0)
        self.lat_spinBox.setMaximum(180)
        self.lat_spinBox.setSuffix(u' °')
        self.lat_spinBox.valueChanged.connect(self.search_filters_changed)

        label_Lon = QLabel('Longitude :')
        label_Lon2 = QLabel('West')

        self.lon_spinBox = QDoubleSpinBox()
        self.lon_spinBox.setAlignment(Qt.AlignCenter)
        self.lon_spinBox.setSingleStep(0.1)
        self.lon_spinBox.setValue(0)
        self.lon_spinBox.setMinimum(0)
        self.lon_spinBox.setMaximum(180)
        self.lon_spinBox.setSuffix(u' °')
        self.lon_spinBox.valueChanged.connect(self.search_filters_changed)

        self.radius_SpinBox = QComboBox()
        self.radius_SpinBox.addItems(['25 km', '50 km', '100 km', '200 km'])
        self.radius_SpinBox.currentIndexChanged.connect(
                self.search_filters_changed)

        prox_search_grid = QGridLayout()
        row = 0
        prox_search_grid.addWidget(label_Lat, row, 1)
        prox_search_grid.addWidget(self.lat_spinBox, row, 2)
        prox_search_grid.addWidget(label_Lat2, row, 3)
        row += 1
        prox_search_grid.addWidget(label_Lon, row, 1)
        prox_search_grid.addWidget(self.lon_spinBox, row, 2)
        prox_search_grid.addWidget(label_Lon2, row, 3)
        row += 1
        prox_search_grid.addWidget(QLabel('Search Radius :'), row, 1)
        prox_search_grid.addWidget(self.radius_SpinBox, row, 2)

        prox_search_grid.setColumnStretch(0, 100)
        prox_search_grid.setColumnStretch(4, 100)
        prox_search_grid.setRowStretch(row+1, 100)
        prox_search_grid.setHorizontalSpacing(20)
        prox_search_grid.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        self.prox_grpbox = QGroupBox("Proximity filter :")
        self.prox_grpbox.setCheckable(True)
        self.prox_grpbox.setChecked(False)
        self.prox_grpbox.toggled.connect(self.proximity_grpbox_toggled)
        self.prox_grpbox.setLayout(prox_search_grid)

        # ---- Province filter

        prov_names = ['All']
        prov_names.extend(self.PROV_NAME)
        self.prov_widg = QComboBox()
        self.prov_widg.addItems(prov_names)
        self.prov_widg.setCurrentIndex(0)
        self.prov_widg.currentIndexChanged.connect(self.search_filters_changed)

        layout = QGridLayout()
        layout.addWidget(self.prov_widg, 2, 1)
        layout.setColumnStretch(2, 100)
        layout.setVerticalSpacing(10)

        prov_grpbox = QGroupBox("Province filter :")
        prov_grpbox.setLayout(layout)

        # ---- Data availability filter

        # Number of years with data

        self.nbrYear = QSpinBox()
        self.nbrYear.setAlignment(Qt.AlignCenter)
        self.nbrYear.setSingleStep(1)
        self.nbrYear.setMinimum(0)
        self.nbrYear.setValue(3)
        self.nbrYear.valueChanged.connect(self.search_filters_changed)

        subgrid1 = QGridLayout()
        subgrid1.addWidget(self.nbrYear, 0, 0)
        subgrid1.addWidget(QLabel('years of data between'), 0, 1)

        subgrid1.setHorizontalSpacing(10)
        subgrid1.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
        subgrid1.setColumnStretch(2, 100)

        # Year range

        self.minYear = QSpinBox()
        self.minYear.setAlignment(Qt.AlignCenter)
        self.minYear.setSingleStep(1)
        self.minYear.setMinimum(1840)
        self.minYear.setMaximum(now.year)
        self.minYear.setValue(1840)
        self.minYear.valueChanged.connect(self.minYear_changed)

        label_and = QLabel('and')
        label_and.setAlignment(Qt.AlignCenter)

        self.maxYear = QSpinBox()
        self.maxYear.setAlignment(Qt.AlignCenter)
        self.maxYear.setSingleStep(1)
        self.maxYear.setMinimum(1840)
        self.maxYear.setMaximum(now.year)
        self.maxYear.setValue(now.year)
        self.maxYear.valueChanged.connect(self.maxYear_changed)

        subgrid2 = QGridLayout()
        subgrid2.addWidget(self.minYear, 0, 0)
        subgrid2.addWidget(label_and, 0, 1)
        subgrid2.addWidget(self.maxYear, 0, 2)

        subgrid2.setHorizontalSpacing(10)
        subgrid2.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
        subgrid2.setColumnStretch(4, 100)

        # Subgridgrid assembly

        grid = QGridLayout()

        grid.addWidget(QLabel('Search for stations with at least'), 0, 0)
        grid.addLayout(subgrid1, 1, 0)
        grid.addLayout(subgrid2, 2, 0)

        grid.setVerticalSpacing(5)
        grid.setRowStretch(0, 100)
        # grid.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        self.year_widg = QGroupBox("Data Availability filter :")
        self.year_widg.setLayout(grid)

        # ---- Toolbar

        self.btn_search = QPushButton('Search')
        self.btn_search.setIcon(IconDB().search)
        self.btn_search.setIconSize(IconDB().iconSize2)
        self.btn_search.setToolTip('Search for weather stations in the online '
                                   'CDCD with the criteria given above.')
        self.btn_search.clicked.connect(self.btn_search_isClicked)
        self.btn_search.hide()

        btn_addSta = QPushButton('Add')
        btn_addSta.setIcon(IconDB().add2list)
        btn_addSta.setIconSize(IconDB().iconSize2)
        btn_addSta.setToolTip('Add selected found weather stations to the '
                              'current list of weather stations.')
        btn_addSta.clicked.connect(self.btn_addSta_isClicked)

        btn_save = QPushButton('Save')
        btn_save.setIcon(IconDB().save)
        btn_save.setIconSize(IconDB().iconSize2)
        btn_save.setToolTip('Save current found stations info in a csv file.')
        btn_save.clicked.connect(self.btn_save_isClicked)

        toolbar_grid = QGridLayout()
        toolbar_widg = QWidget()

        for col, btn in enumerate([self.btn_search, btn_addSta, btn_save]):
            toolbar_grid.addWidget(btn, 0, col+1)

        toolbar_grid.setColumnStretch(toolbar_grid.columnCount(), 100)
        toolbar_grid.setSpacing(5)
        toolbar_grid.setContentsMargins(0, 30, 0, 0)  # (L, T, R, B)

        toolbar_widg.setLayout(toolbar_grid)

        # ---- Left Panel

        panel_title = QLabel('<b>Weather Station Search Criteria :</b>')

        left_panel = QFrame()
        left_panel_grid = QGridLayout()

        left_panel_grid.addWidget(panel_title, 0, 0)
        left_panel_grid.addWidget(self.prox_grpbox, 1, 0)
        left_panel_grid.addWidget(prov_grpbox, 2, 0)
        left_panel_grid.addWidget(self.year_widg, 3, 0)
        left_panel_grid.setRowStretch(4, 100)
        left_panel_grid.addWidget(toolbar_widg, 5, 0)

        left_panel_grid.setVerticalSpacing(20)
        left_panel_grid.setContentsMargins(0, 0, 0, 0)   # (L, T, R, B)
        left_panel.setLayout(left_panel_grid)

        # ----- Main grid

        # Widgets

        vLine1 = QFrame()
        vLine1.setFrameStyle(StyleDB().VLine)

        # Grid

        main_layout = QGridLayout(self)

        main_layout.addWidget(left_panel, 0, 0)
        main_layout.addWidget(vLine1, 0, 1)
        main_layout.addWidget(self.station_table, 0, 2)

        main_layout.setContentsMargins(10, 10, 10, 10)  # (L,T,R,B)
        main_layout.setRowStretch(0, 100)
        main_layout.setHorizontalSpacing(15)
        main_layout.setVerticalSpacing(5)
        main_layout.setColumnStretch(col, 100)

    def show(self):
        super(WeatherStationBrowser, self).show()
        qr = self.frameGeometry()
        if self.parent():
            parent = self.parent()

            wp = parent.frameGeometry().width()
            hp = parent.frameGeometry().height()
            cp = parent.mapToGlobal(QPoint(wp/2., hp/2.))
        else:
            cp = QDesktopWidget().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # -------------------------------------------------------------------------

    def minYear_changed(self):
        min_yr = min_yr = max(self.minYear.value(), 1840)

        now = datetime.now()
        max_yr = now.year

        self.maxYear.setRange(min_yr, max_yr)
        self.search_filters_changed()

    def maxYear_changed(self):
        min_yr = 1840

        now = datetime.now()
        max_yr = min(self.maxYear.value(), now.year)

        self.minYear.setRange(min_yr, max_yr)
        self.search_filters_changed()

    # -------------------------------------------------------------------------

    def btn_save_isClicked(self):
        ddir = os.path.join(os.getcwd(), 'weather_station_list.csv')
        filename, ftype = QFileDialog().getSaveFileName(
                self, 'Save normals', ddir, '*.csv;;*.xlsx;;*.xls')
        self.station_table.save_stationlist(filename)

    def btn_addSta_isClicked(self):
        rows = self.station_table.get_checked_rows()
        if len(rows) > 0:
            staList = self.station_table.get_content4rows(rows)
            self.staListSignal.emit(staList)
            print('Selected stations sent to list')
        else:
            msg = 'No station currently selected'
            print(msg)

    def btn_search_isClicked(self):
        """
        Use the WeatherStationFinder class to question the list of climate
        station in the ECCC network and show the resulting list of stations
        in the GUI.
        """
        stn_finder = WeatherStationFinder()
        stnlist = stn_finder.get_stationlist(
                prov=self.prov, prox=self.prox,
                yrange=(self.year_min, self.year_max, self.nbr_of_years))

        self.station_table.populate_table(stnlist)
        return stnlist

    def proximity_grpbox_toggled(self):
        if self.prox_grpbox.isChecked():
            self.station_table.set_geocoord((self.lat, -self.lon))
        else:
            self.station_table.set_geocoord(None)
        self.search_filters_changed()

    def search_filters_changed(self):
        stnlist = self.stn_finder.get_stationlist(
                prov=self.prov, prox=self.prox,
                yrange=(self.year_min, self.year_max, self.nbr_of_years))
        self.station_table.populate_table(stnlist)


if __name__ == '__main__':

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(10)
    app.setFont(ft)

    stn_browser = WeatherStationBrowser()
    stn_browser.show()

    stn_browser.set_lat(45.40)
    stn_browser.set_lon(73.15)
    stn_browser.set_yearmin(1980)
    stn_browser.set_yearmax(2015)
    stn_browser.set_yearnbr(20)
    stn_browser.search_filters_changed()

    sys.exit(app.exec_())
