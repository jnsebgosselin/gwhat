# -*- coding: utf-8 -*-

# Copyright © 2014-2017 Jean-Sebastien Gosselin
# email: jean-sebastien.gosselin@ete.inrs.ca
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
#
# SearchProgressBar is based on the class FileProgressBar from Spyder.
# Present in spyder.widgets.findinfiles
# Copyright © Spyder Project Contributors
# https://github.com/spyder-ide/spyder

# ---- Standard library imports

from datetime import datetime
import sys
import time
import os
import re

# ---- Third party imports

import numpy as np
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtWidgets import (QWidget, QLabel, QDoubleSpinBox, QComboBox,
                             QFrame, QGridLayout, QTableWidget, QCheckBox,
                             QTabWidget, QSpinBox, QPushButton, QDesktopWidget,
                             QApplication, QHeaderView, QTableWidgetItem,
                             QStyle, QFileDialog)

# ---- Local imports

from gwhat.common import IconDB, StyleDB
from gwhat.common.utils import calc_dist_from_coord
from gwhat.meteo.weather_stationlist import WeatherSationList
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
        super(WeatherStationBrowser, self).__init__()

        self.isOffline = False  # For testing and debugging.
        self.__initUI__()
        self.station_table.setGeoCoord((self.lat, -self.lon))
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

    @property
    def lon(self):
        return self.lon_spinBox.value()

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

    @property
    def year_max(self):
        return int(self.maxYear.value())

    @property
    def nbr_of_years(self):
        return int(self.nbrYear.value())

    def __initUI__(self):
        self.setWindowTitle('Search for Weather Stations')
        self.setWindowIcon(IconDB().master)
        self.setWindowFlags(Qt.Window)

        now = datetime.now()
        self.station_table = WeatherStationDisplayTable(0, self)

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

        label_Lon = QLabel('Longitude :')
        label_Lon2 = QLabel('West')

        self.lon_spinBox = QDoubleSpinBox()
        self.lon_spinBox.setAlignment(Qt.AlignCenter)
        self.lon_spinBox.setSingleStep(0.1)
        self.lon_spinBox.setValue(0)
        self.lon_spinBox.setMinimum(0)
        self.lon_spinBox.setMaximum(180)
        self.lon_spinBox.setSuffix(u' °')

        self.radius_SpinBox = QComboBox()
        self.radius_SpinBox.addItems(['25 km', '50 km', '100 km', '200 km'])

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
        if self.parentWidget():
            parent = self.parentWidget()

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

    def maxYear_changed(self):
        min_yr = 1840

        now = datetime.now()
        max_yr = min(self.maxYear.value(), now.year)

        self.minYear.setRange(min_yr, max_yr)

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
            self.station_table.setGeoCoord((self.lat, -self.lon))
        else:
            self.station_table.setGeoCoord(None)


class WeatherStationDisplayTable(QTableWidget):
    """
    Widget for displaying a weather station list.

    # ---- Inputs

    year_display_mode : 0 -> Years are displayed in a standard
                             QTableWidget cell
                        1 -> Years are displayed in a QComboBox
    """

    def __init__(self, year_display_mode=0, parent=None):
        super(WeatherStationDisplayTable, self).__init__(parent)

        self.year_display_mode = year_display_mode
        self.__initUI__()
        self.setGeoCoord(None)

    def __initUI__(self):
        self.setFont(StyleDB().font1)
        self.setFrameStyle(StyleDB().frame)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setMinimumWidth(650)

        # ---- Header

        # http://stackoverflow.com/questions/9744975/
        # pyside-pyqt4-adding-a-checkbox-to-qtablewidget-
        # horizontal-column-header

        self.chkbox_header = QCheckBox(self.horizontalHeader())
        self.chkbox_header.setToolTip('Check or uncheck all the weather '
                                      'stations in the table.')
        self.horizontalHeader().installEventFilter(self)

        HEADER = ('', 'Weather Stations', 'Proximity\n(km)', 'From \n Year',
                  'To \n Year', 'Prov.', 'Climate ID', 'Station ID',
                  'Lat.\n(dd)', 'Lon.\n(dd)', 'Elev.\n(m)')

        self.setColumnCount(len(HEADER))
        self.setHorizontalHeaderLabels(HEADER)
        self.verticalHeader().hide()

        # ---- Column Size Policy

        self.setColumnHidden(7, True)
        self.setColumnHidden(8, True)
        self.setColumnHidden(9, True)
        self.setColumnHidden(10, True)

        self.setColumnWidth(0, 32)
        self.setColumnWidth(3, 75)
        self.setColumnWidth(4, 75)
        self.setColumnWidth(5, 75)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # ---- Events

        self.chkbox_header.stateChanged.connect(self.chkbox_header_isClicked)

    def setGeoCoord(self, latlon):
        self.__latlon = latlon
        self.setColumnHidden(2, latlon is None)

    def geoCoord(self):
        return self.__latlon

    class NumTableWidgetItem(QTableWidgetItem):

        # To be able to sort numerical item within a given column.

        # http://stackoverflow.com/questions/12673598/
        # python-numerical-sorting-in-qtablewidget

            def __init__(self, text, sortKey):
                QTableWidgetItem.__init__(
                    self, text, QTableWidgetItem.UserType)
                self.sortKey = sortKey

            # Qt uses a simple < check for sorting items, override this to use
            # the sortKey
            def __lt__(self, other):
                return self.sortKey < other.sortKey

    def eventFilter(self, source, event):
        if (event.type() == QEvent.Resize):
            self.resize_chkbox_header()

        return QWidget.eventFilter(self, source, event)

    def resize_chkbox_header(self):

        h = self.style().pixelMetric(QStyle.PM_IndicatorHeight)
        w = self.style().pixelMetric(QStyle.PM_IndicatorWidth)

        W = self.horizontalHeader().sectionSize(0)
        H = self.horizontalHeader().height()

        y0 = int((H - h) / 2)
        x0 = int((W - w) / 2)

        self.chkbox_header.setGeometry(x0, y0, w, h)

    def chkbox_header_isClicked(self):
        nrow = self.rowCount()
        for row in range(nrow):
            item = self.cellWidget(row, 0).layout().itemAtPosition(1, 1)
            widget = item.widget()
            widget.setCheckState(self.chkbox_header.checkState())

    def clearContents(self):
        """Qt method override"""
        super(WeatherStationDisplayTable, self).clearContents()
        self.setRowCount(0)

    def insert_row_at_end(self, row_data):
        row = self.rowCount()
        self.insertRow(row)

        self.setSortingEnabled(False)

        # ---- Checkbox

        col = 0

        item = QTableWidgetItem('')
        item.setFlags(item.flags() & ~Qt.ItemIsEditable & Qt.ItemIsEnabled)
        self.setItem(row, col, item)

        chckbox = QCheckBox()
        chckbox.setCheckState(self.chkbox_header.checkState())

        chckbox_center = QWidget()
        chckbox_grid = QGridLayout(chckbox_center)
        chckbox_grid.addWidget(chckbox, 1, 1)
        chckbox_grid.setColumnStretch(0, 100)
        chckbox_grid.setColumnStretch(2, 100)
        chckbox_grid.setContentsMargins(0, 0, 0, 0)  # [L, T, R, B]

        self.setCellWidget(row, col, chckbox_center)

        # ---- Weather Station

        col += 1

        item = QTableWidgetItem(row_data[0])
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item.setToolTip(row_data[0])
        self.setItem(row, col, item)

        # ---- Proximity

        col += 1
        if self.geoCoord():
            lat1, lon1 = self.geoCoord()
            lat2, lon2 = float(row_data[6]), float(row_data[7])
            dist = calc_dist_from_coord(lat1, lon1, lat2, lon2)

            item = self.NumTableWidgetItem('%0.1f' % dist, dist)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)

        # ---- From Year

        min_year = int(row_data[2])
        max_year = int(row_data[3])
        yearspan = np.arange(min_year, max_year+1).astype(str)

        col += 1

        item = QTableWidgetItem(row_data[2])
        item.setFlags(item.flags() & Qt.ItemIsEnabled)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        if self.year_display_mode == 1:
            item.setFlags(item.flags() & Qt.ItemIsEnabled)

            self.fromYear = QComboBox()
            self.fromYear.setFixedWidth(75)
            self.fromYear.setInsertPolicy(QComboBox.NoInsert)
            self.fromYear.addItems(yearspan)
            self.fromYear.setMinimumContentsLength(4)
            self.fromYear.setSizeAdjustPolicy(
                    QComboBox.AdjustToMinimumContentsLength)

            self.setCellWidget(row, col, self.fromYear)

        # ---- To Year

        col += 1

        item = QTableWidgetItem(row_data[3])
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        if self.year_display_mode == 1:
            item.setFlags(item.flags() & Qt.ItemIsEnabled)

            self.toYear = QComboBox()
            self.toYear.setFixedWidth(75)
            self.toYear.setInsertPolicy(QComboBox.NoInsert)
            self.toYear.addItems(yearspan)
            self.toYear.setCurrentIndex(len(yearspan)-1)
            self.toYear.setMinimumContentsLength(4)
            self.toYear.setSizeAdjustPolicy(
                    QComboBox.AdjustToMinimumContentsLength)

            self.setCellWidget(row, col, self.toYear)

        # ---- Province

        col += 1

        item = QTableWidgetItem(row_data[4])
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        # ---- Climate ID

        col += 1

        item = QTableWidgetItem(row_data[5])
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        # ---- Station ID (hidden)

        col += 1

        item = QTableWidgetItem(row_data[1])
        self.setItem(row, col, item)

        # ---- Latitude

        col += 1

        item = self.NumTableWidgetItem(row_data[6], float(row_data[6]))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        # ---- Longitude

        col += 1

        item = self.NumTableWidgetItem(row_data[7], float(row_data[7]))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        # ---- Elevation

        col += 1

        try:
            item = self.NumTableWidgetItem(row_data[8], float(row_data[8]))
        except ValueError:
            item = QTableWidgetItem(row_data[8])
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        self.setSortingEnabled(True)

    def delete_rows(self, rows):
        # Going in reverse order to preserve indexes while
        # scanning the rows if any are deleted.
        for row in reversed(rows):
            print('Removing %s (%s)' % (self.item(row, 1).text(),
                                        self.item(row, 6).text()))
            self.removeRow(row)

    def populate_table(self, staList):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.clearContents()
        self.chkbox_header.setCheckState(Qt.CheckState(False))
        self.setSortingEnabled(False)
        for row_data in staList:
            self.insert_row_at_end(row_data)
        self.setSortingEnabled(True)
        QApplication.restoreOverrideCursor()

    # -------------------------------------------------------------------------

    def set_fromyear(self, year):
        for row in range(self.rowCount()):
            self.set_row_fromyear(row, year)

    def set_row_fromyear(self, row, year):
        if self.year_display_mode == 1:
            widget = self.cellWidget(row, 3)
            years = [widget.itemText(i) for i in range(widget.count())]

            try:
                index = years.index(str(year))
            except ValueError:
                index = 0
            finally:
                widget.setCurrentIndex(index)

    def set_toyear(self, year):
        for row in range(self.rowCount()):
            self.set_row_toyear(row, year)

    def set_row_toyear(self, row, year):
        if self.year_display_mode == 1:
            widget = self.cellWidget(row, 4)
            years = [widget.itemText(i) for i in range(widget.count())]

            try:
                index = years.index(str(year))
            except ValueError:
                index = len(years)-1
            finally:
                widget.setCurrentIndex(index)

    # -------------------------------------------------------------------------

    def get_row_from_climateid(self, climateid):
        for row in range(self.rowCount()):
            if self.item(row, 6).text() == str(climateid):
                return row

    def get_checked_rows(self):
        rows = []
        for row in range(self.rowCount()):
            item = self.cellWidget(row, 0).layout().itemAtPosition(1, 1)
            widget = item.widget()
            if widget.isChecked():
                rows.append(row)

        return rows

    # -------------------------------------------------------------------------

    def get_content4rows(self, rows, daterange='full'):
        """
        Grab the weather station info for the specified rows and
        save the results in a list.
        """

        stationlist = WeatherSationList()
        for row in rows:
            stationlist.append(
                    [self.item(row, 1).text(),   # 0: name
                     self.item(row, 7).text(),   # 1: database ID
                     self.item(row, 3).text(),   # 2: from year
                     self.item(row, 4).text(),   # 3: to year
                     self.item(row, 5).text(),   # 4: province
                     self.item(row, 6).text(),   # 5: climate ID
                     self.item(row, 8).text(),   # 7: latitude
                     self.item(row, 9).text(),   # 8: longitude
                     self.item(row, 10).text()   # 9: elevation
                     ])

            if daterange == 'selected':
                stationlist[-1][2] = self.cellWidget(row, 3).currentText()
                stationlist[-1][3] = self.cellWidget(row, 4).currentText()

        return stationlist

    def get_stationlist(self):
        """Get and format the content of the QTableWidget."""
        stationlist = WeatherSationList()
        stationlist.extend(self.get_content4rows(range(self.rowCount())))

        return stationlist

    def save_stationlist(self, filename):
        """Save the content of the QTableWidget to file."""
        stationlist = self.get_stationlist()
        stationlist.save_to_file(filename)


if __name__ == '__main__':

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(10)
    app.setFont(ft)

    stn_browser = WeatherStationBrowser()

    stn_browser.lat_spinBox.setValue(45.40)
    stn_browser.lon_spinBox.setValue(73.15)
    stn_browser.minYear.setValue(1980)
    stn_browser.maxYear.setValue(2015)
    stn_browser.nbrYear.setValue(20)

    # stn_browser.finder.isOffline = False
    # search4sta.finder.debug_mode = True

    stn_browser.show()

    sys.exit(app.exec_())
