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

try:
    from urllib2 import urlopen, URLError
except ImportError:
    from urllib.request import URLError, urlopen
from datetime import datetime
import sys
import csv
import time
import os

# Third party imports :

import xlsxwriter
import numpy as np
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import QObject, Qt, QPoint, QEvent, QThread
from PyQt5.QtWidgets import (QWidget, QLabel, QDoubleSpinBox, QComboBox,
                             QFrame, QGridLayout, QTableWidget, QCheckBox,
                             QTabWidget, QSpinBox, QPushButton, QDesktopWidget,
                             QApplication, QHeaderView, QTableWidgetItem,
                             QStyle, QFileDialog)

# Local imports :

import common.database as db
from common import IconDB, StyleDB


# =============================================================================


class StationFinder(QObject):

    searchFinished = QSignal(list)
    newStationFound = QSignal(list)
    ConsoleSignal = QSignal(str)

    def __init__(self, parent=None):
        super(StationFinder, self).__init__(parent)

        self.prov = None
        self.lat = 45.40
        self.lon = 73.15
        self.rad = 25
        self.year_min = 1960
        self.year_max = 2015
        self.nbr_of_years = 5
        self.search_by = 'proximity'
        # options are: 'proximity' or 'province'
        self.stationlist = []

        self.stop_searching = False
        self.isOffline = False
        self.debug_mode = False

    def search_envirocan(self):
        """
        Search on the Government of Canada website for weather stations with
        daily meteo data around a decimal degree Lat & Lon coordinate with a
        radius given in km.

        The results are returned in a list formatted ready to be
        read by WHAT UI. A signal is emitted with the list if the process is
        completed successfully.

        If no results are found, only the header is return with an empty
        list of station.

        If an error is raised, an empty list is returned.
        """

        print('Searching weather station on www.http://climate.weather.gc.ca.')

        Nmax = 100  # Number of results per page (maximu m possible is 100)

        self.stationlist = []
        # [station_name, station_id, start_year,
        #  end_year, province, climate_id, station_proxim]

        # ----------------------------------------------------- define url ----

        # Last updated: May 25th, 2016

        url = ('http://climate.weather.gc.ca/historical_data/'
               'search_historic_data_stations_e.html?')

        if self.search_by == 'proximity':
            url += 'searchType=stnProx&timeframe=1&txtRadius=%d' % self.rad
            url += '&selCity=&selPark=&optProxType=custom'

            deg, mnt, sec = decdeg2dms(np.abs(self.lat))
            url += '&txtCentralLatDeg=%d' % deg
            url += '&txtCentralLatMin=%d' % mnt
            url += '&txtCentralLatSec=%d' % sec

            deg, mnt, sec = decdeg2dms(np.abs(self.lon))
            url += '&txtCentralLongDeg=%d' % deg
            url += '&txtCentralLongMin=%d' % mnt
            url += '&txtCentralLongSec=%d' % sec
        elif self.search_by == 'province':
            url += 'searchType=stnProv&timeframe=1&lstProvince=%s' % self.prov

        url += '&optLimit=yearRange'
        url += '&StartYear=%d' % self.year_min
        url += '&EndYear=%d' % self.year_max
        url += '&Year=2013&Month=6&Day=4'
        url += '&selRowPerPage=%d' % Nmax

        if self.search_by == 'proximity':
            url += '&cmdProxSubmit=Search'
        elif self.search_by == 'province':
            url += '&cmdProvSubmit=Search'

        # ----------------------------------------------------- fetch data ----

        try:
            if self.isOffline:
                with open('url.txt', 'r') as f:
                    stnresults = f.read()
            else:
                with urlopen(url) as f:
                    stnresults = f.read().decode('utf-8', 'replace')

                if self.debug_mode:
                    # write downloaded content to local file for
                    # debugging purpose:
                    with open('url.txt', 'w') as local_file:
                        local_file.write(stnresults)

            # ---- Number of Stations Found ----

            if self.search_by == 'proximity':
                txt2find = 'stations found within a search radius'
            if self.search_by == 'province':
                txt2find = 'stations found in'

            indx_e = stnresults.find(txt2find, 0)
            if indx_e == -1:
                msg = 'No weather station found.'
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
                print(msg)
                self.searchFinished.emit(self.stationlist)
                return

            # Go backward from indx_e and find where the number starts to
            # fetch the total number of weather station found :

            indx_0 = np.copy(indx_e)
            while 1:
                indx_0 += -1
                if stnresults[indx_0] == '>':
                    indx_0 += 1
                    break
            Nsta = int(stnresults[indx_0:indx_e])
            print('%d weather stations found.' % Nsta)

            # Fetch stations page per page :

            Npage = int(np.ceil(Nsta / float(Nmax)))
            print('Total number of page = % d' % Npage)

            staCount = 0  # global station counter
            for page in range(Npage):
                if self.stop_searching:
                    self.searchFinished.emit(self.stationlist)
                    return

                print('Page :', page)
                startRow = (Nmax * page) + 1
                url4page = url + '&startRow=%d' % startRow
                if self.isOffline:
                    with open('url.txt') as f:
                        stnresults = f.read()
                else:
                    f = urlopen(url4page)
                    stnresults = f.read().decode('utf-8')

                    if self.debug_mode:
                        # Write result in a local file for debugging purposes:
                        filename = 'url4page%d.txt' % page
                        with open(filename, 'w') as local_file:
                            local_file.write(stnresults)

                # Scan each row of the current page :
                while 1:

                    # ---- Location of station information block ----

                    indx_e = 0
                    txt2find = ('<form action="/climate_data/'
                                'interform_e.html" method="post" '
                                'id="stnRequest%d">') % staCount

                    n = len(txt2find)
                    indx_0 = stnresults.find(txt2find, indx_e)
                    if indx_0 == -1:
                        # No result left on this page. Break the loop and
                        # iterate to the next page if it exists
                        break
                    else:
                        indx_e = indx_0 + n

                    # ---- StartDate and EndDate ----

                    txt2find = 'name="dlyRange" value="'
                    n = len(txt2find)
                    indx_0 = stnresults.find(txt2find, indx_e)
                    indx_e = stnresults.find('|', indx_0)

                    start_year = stnresults[indx_0+n:indx_0+n+4]
                    end_year = stnresults[indx_e+1:indx_e+1+4]

                    # ---- StationID ----

                    txt2find = 'name="StationID" value="'
                    indx_0 = stnresults.find(txt2find, indx_e) + len(txt2find)
                    indx_e = stnresults.find('"', indx_0)

                    station_id = stnresults[indx_0:indx_e].strip()

                    # ---- Province ----

                    txt2find = 'name="Prov" value="'
                    indx_0 = stnresults.find(txt2find, indx_e) + len(txt2find)
                    indx_e = stnresults.find('"', indx_0)

                    province = stnresults[indx_0:indx_e].strip()

                    # ---- Station Name ----

                    txt2find = ('<div class="col-lg-3 col-md-3'
                                ' col-sm-3 col-xs-3">')
                    indx_0 = stnresults.find(txt2find, indx_e) + len(txt2find)
                    indx_e = stnresults.find('</div>', indx_0)

                    station_name = stnresults[indx_0:indx_e].strip()

                    # ---- Proximity ----

                    if self.search_by == 'proximity':
                        txt2find = ('<div class="col-lg-2 col-md-2'
                                    ' col-sm-2 col-xs-2">')
                        indx_0 = (stnresults.find(txt2find, indx_e) +
                                  len(txt2find))
                        indx_e = stnresults.find('</div>', indx_0)

                        station_proxim = stnresults[indx_0:indx_e].strip()
                    elif self.search_by == 'province':
                        station_proxim = 0

                    if start_year.isdigit():  # daily data exist
                        year_range = int(end_year)-int(start_year)+1
                        if year_range >= self.nbr_of_years:

                            print("Adding %s to list..." % station_name)

                            # ---- Climate ID ----

                            if self.stop_searching:
                                self.searchFinished.emit(self.stationlist)
                                return

                            staInfo = self.get_staInfo(province, station_id)
                            climate_id = staInfo[5]

                            # ---- Send Signal to UI ----
                            new_station = [station_name, station_id,
                                           start_year, end_year, province,
                                           climate_id, station_proxim]

                            if self.stop_searching:
                                self.searchFinished.emit(self.stationlist)
                                return self.stationlist
                            else:
                                self.stationlist.append(new_station)
                                self.newStationFound.emit(new_station)
                        else:
                            print("Not adding %s (not enough data)"
                                  % station_name)
                    else:
                        print("Not adding %s (no daily data)"
                              % station_name)

                    staCount += 1

            msg = ('%d weather stations with daily data for at least %d years'
                   ' between %d and %d'
                   ) % (len(self.stationlist), self.nbr_of_years,
                        self.year_min, self.year_max)
            self.ConsoleSignal.emit('<font color=green>%s</font>' % msg)
            print(msg)

        except URLError as e:
            if hasattr(e, 'reason'):
                msg = 'Failed to reach a server.'
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
                print(msg)

                print('Reason: ', e.reason)
                print()

            elif hasattr(e, 'code'):
                msg = 'The server couldn\'t fulfill the request.'
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
                print(msg)

                print('Error code: ', e.code)
                print()

        print('Searching for weather station is finished.')
        self.searchFinished.emit(self.stationlist)

        return self.stationlist

    def get_staInfo(self, Prov, StationID):
        """
        Fetch the Climate Id for a given station. This ID is used to identify
        the station in the CDCD, but not for downloading the data from
        the server.

        This information is not available when doing a search for stations
        and need to be fetch for each station individually.
        """

        url = ('http://climate.weather.gc.ca/'
               'climate_data/daily_data_e.html?'
               "timeframe=2&Prov=%s&StationID=%s") % (Prov, StationID)

        if self.isOffline:
            with open('urlsinglestation.txt', 'r') as f:
                urlread = f.read()
                time.sleep(0.25)
        else:
            f = urlopen(url)
            urlread = f.read().decode('utf-8')

            if self.debug_mode:
                # write downloaded content to local file for
                # debugging purpose:
                with open('urlsinglestation.txt', 'w') as local_file:
                    local_file.write(urlread)

        # ---- Station Name ----

        txt2find = '<p class="text-center table-header pdng-md mrgn-bttm-0">'
        n = len(txt2find)
        indx_0 = urlread.find(txt2find, 0) + n
        indx_e = urlread.find('<br/>', indx_0)

        staName = urlread[indx_0:indx_e]
        staName = staName.strip()

        # ---- Climate ID ----

        txt2find = ('aria-labelledby="climateid">')
        n = len(txt2find)

        indx_0 = urlread.find(txt2find, 0) + n
        indx_e = urlread.find('</div>', indx_0)

        climate_id = urlread[indx_0:indx_e]
        climate_id = climate_id.strip()

        # ---- Start Year ----

        txt2find = '<option value="'
        n = len(txt2find)
        indx_0 = urlread.find(txt2find, indx_e) + n

        startYear = urlread[indx_0:indx_0+4]

        # ---- End Year ----

        txt2find = '" selected="'
        indx_e = urlread.find(txt2find, indx_0)

        endYear = urlread[indx_e-4:indx_e]

        # ---- Proximity ----

        proximity = np.nan

        print('%s (%s) : %s - %s' % (staName, climate_id, startYear, endYear))

        staInfo = [staName, StationID, startYear, endYear,
                   Prov, climate_id, proximity]

        return staInfo


# =============================================================================


class Search4Stations(QWidget):
    '''
    Widget that allows the user to search for weather stations on the
    Government of Canada website.
    '''

    ConsoleSignal = QSignal(str)
    staListSignal = QSignal(list)

    def __init__(self, parent=None):
        super(Search4Stations, self).__init__()
        self.__initUI__()

        # Setup gap fill worker and thread :
        self.finder = StationFinder()
        self.thread = QThread()
        self.finder.moveToThread(self.thread)
        self.finder.newStationFound.connect(
                self.station_table.insert_row_at_end)
        self.finder.searchFinished.connect(self.search_is_finished)

    @property
    def search_by(self):
        return ['proximity', 'province'][self.tab_widg.currentIndex()]

    @property
    def prov(self):
        return self.prov_widg.currentText()

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

        # ------------------------------------------------- INIT VARIABLES ----

        now = datetime.now()

        self.station_table = WeatherStationDisplayTable(0, self)
        self.isOffline = False  # For testing and debugging purpose

        # ---------------------------------------------- Tab Widget Search ----

        # ---- Search by Proximity ----

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

        prox_search_widg = QWidget()
        prox_search_grid = QGridLayout()

        row, col = 0, 1
        prox_search_grid.addWidget(label_Lat, row, col)
        prox_search_grid.addWidget(self.lat_spinBox, row, col+1)
        prox_search_grid.addWidget(label_Lat2, row, col+2)
        row += 1
        prox_search_grid.addWidget(label_Lon, row, col)
        prox_search_grid.addWidget(self.lon_spinBox, row, col+1)
        prox_search_grid.addWidget(label_Lon2, row, col+2)
        row += 1
        prox_search_grid.addWidget(QLabel('Search Radius :'), row, col)
        prox_search_grid.addWidget(self.radius_SpinBox, row, col+1)

        prox_search_grid.setColumnStretch(0, 100)
        prox_search_grid.setColumnStretch(col+3, 100)
        prox_search_grid.setRowStretch(row + 1, 100)
        prox_search_grid.setHorizontalSpacing(20)
        prox_search_grid.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        prox_search_widg.setLayout(prox_search_grid)

        # ---- Search by Province ----

        self.prov_widg = QComboBox()
        self.prov_widg.addItems(['QC', 'AB'])

        prov_search_widg = QFrame()
        prov_search_grid = QGridLayout()

        prov_search_grid.addWidget(QLabel('Province :'), 1, 1)
        prov_search_grid.addWidget(self.prov_widg, 1, 2)

#        prov_search_grid.setColumnStretch(0, 100)
        prov_search_grid.setColumnStretch(3, 100)
        prov_search_grid.setRowStretch(0, 100)
        prov_search_grid.setRowStretch(2, 100)

        prov_search_widg.setLayout(prov_search_grid)

        # ---- Assemble TabWidget ----

        self.tab_widg = QTabWidget()

        self.tab_widg.addTab(prox_search_widg, 'Proximity')
        self.tab_widg.addTab(prov_search_widg, 'Province')

        # -------------------------------------------------- Year Criteria ----

        label_date = QLabel('Search for stations with data available')

        # ---- subgrid year boundary ----

        label_between = QLabel('between')
        label_between.setAlignment(Qt.AlignCenter)

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

        yearbound_widget = QFrame()
        yearbound_grid = QGridLayout()

        col = 0
        yearbound_grid.addWidget(label_between, 0, col)
        col += 1
        yearbound_grid.addWidget(self.minYear, 0, col)
        col += 1
        yearbound_grid.addWidget(label_and, 0, col)
        col += 1
        yearbound_grid.addWidget(self.maxYear, 0, col)

        yearbound_grid.setSpacing(10)
        yearbound_grid.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
        yearbound_grid.setColumnStretch(1, 100)
        yearbound_grid.setColumnStretch(3, 100)

        yearbound_widget.setLayout(yearbound_grid)

        # ---- subgrid min. nbr. of years ----

        label_4atleast = QLabel('for at least')
        label_years = QLabel('years')

        self.nbrYear = QSpinBox()
        self.nbrYear.setAlignment(Qt.AlignCenter)
        self.nbrYear.setSingleStep(1)
        self.nbrYear.setMinimum(0)
        self.nbrYear.setValue(3)

        subwidg1 = QWidget()
        subgrid1 = QGridLayout()

        col = 0
        subgrid1.addWidget(label_4atleast, 0, col)
        col += 1
        subgrid1.addWidget(self.nbrYear, 0, col)
        col += 1
        subgrid1.addWidget(label_years, 0, col)

        subgrid1.setSpacing(10)
        subgrid1.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
        subgrid1.setColumnStretch(col+1, 100)

        subwidg1.setLayout(subgrid1)

        # ---- maingrid ----

        self.year_widg = QFrame()
        self.year_widg.setFrameStyle(0)  # styleDB.frame

        year_grid = QGridLayout()

        row = 1
        year_grid.addWidget(label_date, row, 0)
        row += 1
        year_grid.addWidget(yearbound_widget, row, 0)
        row += 1
        year_grid.addWidget(subwidg1, row, 0)

        year_grid.setVerticalSpacing(20)
        year_grid.setRowStretch(0, 100)
        year_grid.setContentsMargins(15, 0, 15, 0)  # (L, T, R, B)

        self.year_widg.setLayout(year_grid)

        # -------------------------------------------------------- TOOLBAR ----

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

        # ---------------------------------------------------- Left Panel ----

        panel_title = QLabel('<b>Weather Station Search Criteria :</b>')

        left_panel = QFrame()
        left_panel_grid = QGridLayout()

#        self.statusBar = QStatusBar()
#        self.statusBar.setSizeGripEnabled(False)

        row = 0
        left_panel_grid.addWidget(panel_title, row, 0)
        row += 1
        left_panel_grid.addWidget(self.tab_widg, row, 0)
        row += 1
        left_panel_grid.addWidget(self.year_widg, row, 0)
        row += 1
        left_panel_grid.addWidget(toolbar_widg, row, 0)
#        row += 1
#        right_panel_grid.addWidget(self.statusBar, row, 0)

        left_panel_grid.setVerticalSpacing(20)
        left_panel_grid.setRowStretch(row+1, 100)
        left_panel_grid.setContentsMargins(0, 0, 0, 0)   # (L, T, R, B)
        left_panel.setLayout(left_panel_grid)

        # ------------------------------------------------------ MAIN GRID ----

        # ---- Widgets ----

        vLine1 = QFrame()
        vLine1.setFrameStyle(StyleDB().VLine)

        # ---- GRID ----

        main_layout = QGridLayout(self)

        row = 0
        col = 0
        main_layout.addWidget(left_panel, row, col)
        col += 1
        main_layout.addWidget(vLine1, row, col)
        col += 1
        main_layout.addWidget(self.station_table, row, col)

        main_layout.setContentsMargins(10, 10, 10, 10)  # (L,T,R,B)
        main_layout.setSpacing(15)
        main_layout.setColumnStretch(col, 100)

    # =========================================================================

    def show(self):
        super(Search4Stations, self).show()
        # self.activateWindow()
        # self.raise_()

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
        self.setFixedSize(self.size())

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

        station_list = self.station_table.get_staList()
        station_list.insert(0, db.FileHeaders().weather_stations[0])

        if ftype in ['*.xlsx', '*.xls']:
            wb = xlsxwriter.Workbook(filename)
            ws = wb.add_worksheet()
            for i, row in enumerate(station_list):
                ws.write_row(i, 0, row)
        elif ftype == '*.csv':
            with open(filename, 'w', encoding='utf8')as f:
                writer = csv.writer(f, delimiter=',', lineterminator='\n')
                writer.writerows(station_list)

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
        Initiate the seach for weather stations. It grabs the info from the
        interface and send it to the method "search_envirocan".
        """
        if self.finder.stop_searching:
            print("The thread is in the process of being stopped: do nothing.")
            return

        if self.thread.isRunning():
            print('Telling the thread to stop searching.')
            self.finder.stop_searching = True
            self.btn_search.setIcon(IconDB().search)
            self.btn_search.setEnabled(False)
            return

        # Update UI state :
        self.year_widg.setEnabled(False)
        self.tab_widg.setEnabled(False)
        self.btn_search.setIcon(IconDB().stop)
        self.station_table.clearContents()

        # Set the attributes of the finder:
        self.finder.prov = self.prov
        self.finder.lat = self.lat
        self.finder.lon = self.lon
        self.finder.rad = self.rad
        self.finder.year_min = self.year_min
        self.finder.year_max = self.year_max
        self.finder.nbr_of_years = self.nbr_of_years
        self.finder.search_by = self.search_by

        # Start searching for weather station :
        self.thread.started.connect(self.finder.search_envirocan)
        self.thread.start()

        msg = 'Searching for weather stations. Please wait...'
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)

    def search_is_finished(self, station_list):
        self.thread.quit()
        waittime = 0
        while self.thread.isRunning():
            print('Waiting for the finder thread to close.')
            time.sleep(0.1)
            waittime += 0.1
            if waittime > 15:
                msg = ('This function is not working as intended. '
                       'Please report a bug.')
                print(msg)
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
                return
        self.thread.started.disconnect(self.finder.search_envirocan)

        # ---- Reset the UI ----

        self.finder.stop_searching = False
        self.btn_search.setEnabled(True)
        self.btn_search.setIcon(IconDB().search)
        self.year_widg.setEnabled(True)
        self.tab_widg.setEnabled(True)


# =============================================================================


class WeatherStationDisplayTable(QTableWidget):
    """
    Widget for displaying a weather station list.

    #---- Inputs ----

    year_display_mode : 0 -> Years are displayed in a standard
                             QTableWidget cell
                        1 -> Years are displayed in a QComboBox
    """

    def __init__(self, year_display_mode=0, parent=None):
        super(WeatherStationDisplayTable, self).__init__(parent)

        self.year_display_mode = year_display_mode
        self.__initUI__()

    def __initUI__(self):
        self.setFont(StyleDB().font1)
        self.setFrameStyle(StyleDB().frame)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setMinimumWidth(650)

        # --------------------------------------------------------- Header ----

        # http://stackoverflow.com/questions/9744975/
        # pyside-pyqt4-adding-a-checkbox-to-qtablewidget-
        # horizontal-column-header

        self.chkbox_header = QCheckBox(self.horizontalHeader())
        self.chkbox_header.setToolTip('Check or uncheck all the weather '
                                      'stations in the table.')
        self.horizontalHeader().installEventFilter(self)

        HEADER = ('', 'Weather Stations', 'Proximity \n (km)', 'From \n Year',
                  'To \n Year', 'Prov.', 'Climate ID', 'Station ID')

        self.setColumnCount(len(HEADER))
        self.setHorizontalHeaderLabels(HEADER)
        self.verticalHeader().hide()

        # --------------------------------------------- Column Size Policy ----

#        self.setColumnHidden(6, True)
        self.setColumnHidden(7, True)

        self.setColumnWidth(0, 32)
        self.setColumnWidth(3, 75)
        self.setColumnWidth(4, 75)
        self.setColumnWidth(5, 75)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # --------------------------------------------------------- Events ----

        self.chkbox_header.stateChanged.connect(self.chkbox_header_isClicked)

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
        "Qt method override"
        super(WeatherStationDisplayTable, self).clearContents()
        self.setRowCount(0)

    def insert_row_at_end(self, row_data):
        row = self.rowCount()
        self.insertRow(row)

        # ---- Checkbox ----

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

        # ---- Weather Station ----

        col += 1

        item = QTableWidgetItem(row_data[0])
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item.setToolTip(row_data[0])
        self.setItem(row, col, item)

        # ---- Proximity ----

        col += 1

        item = self.NumTableWidgetItem('%0.2f' % float(row_data[6]),
                                       float(row_data[6]))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        # ---- From Year ----

        # ----
        min_year = int(row_data[2])
        max_year = int(row_data[3])
        yearspan = np.arange(min_year, max_year+1).astype(str)
        # ----

        col += 1

        item = QTableWidgetItem(row_data[2])
        item.setFlags(item.flags() & Qt.ItemIsEnabled)
        self.setItem(row, col, item)
        item.setTextAlignment(Qt.AlignCenter)

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

        # ---- To Year ----

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

        # ---- Province ----

        col += 1

        item = QTableWidgetItem(row_data[4])
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        # ---- Climate ID (hidden) ----

        col += 1

        item = QTableWidgetItem(row_data[5])
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, col, item)

        # ---- Station ID ----

        col += 1

        item = QTableWidgetItem(row_data[1])
        self.setItem(row, col, item)

    def delete_rows(self, rows):
        # Going in reverse order to preserve indexes while
        # scanning the rows if any are deleted.
        for row in reversed(rows):
            print('Removing %s (%s)' % (self.item(row, 1).text(),
                                        self.item(row, 6).text()))
            self.removeRow(row)

    def populate_table(self, staList):
        self.clearContents()
        self.chkbox_header.setCheckState(Qt.CheckState(False))
        self.setSortingEnabled(False)
        for row_data in staList:
            self.insert_row_at_end(row_data)
        self.setSortingEnabled(True)

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

    def get_content4rows(self, rows):
        ''' Grabs weather station info save them in a list.'''

        station_list = []
        for row in rows:
            station_list.append(
                    [self.item(row, 1).text(),   # 0: name
                     self.item(row, 7).text(),   # 1: database ID
                     self.item(row, 3).text(),   # 2: from year
                     self.item(row, 4).text(),   # 3: to year
                     self.item(row, 5).text(),   # 4: province
                     self.item(row, 6).text(),   # 5: climate ID
                     self.item(row, 2).text()])  # 6: proximity
            if self.year_display_mode == 1:
                station_list[0][2] = self.cellWidget(row, 3).currentText()
                station_list[0][3] = self.cellWidget(row, 4).currentText()

        return station_list

    def get_staList(self):
        station_list = []
        for row in range(self.rowCount()):
            station_list.append(
                    [self.item(row, 1).text(),   # 0: name
                     self.item(row, 7).text(),   # 1: database ID
                     self.item(row, 3).text(),   # 2: from year
                     self.item(row, 4).text(),   # 3: to year
                     self.item(row, 5).text(),   # 4: province
                     self.item(row, 6).text(),   # 5: climate ID
                     self.item(row, 2).text()])  # 6: proximity

        return station_list

    def save_staList(self, filename):
        station_list = self.get_staList()
        station_list.insert(0, db.FileHeaders().weather_stations[0])

        with open(filename, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',', lineterminator='\n')
            writer.writerows(station_list)


def decdeg2dms(dd):
    '''
    Convert decimal degree lat/lon coordinate to decimal, minute,
    second format.
    '''

    mnt, sec = divmod(dd*3600, 60)
    deg, mnt = divmod(mnt, 60)

    return deg, mnt, sec


def dms2decdeg(deg, mnt, sec):
    '''
    Convert decimal, minute, second format lat/lon coordinate to decimal
    degree.
    '''

    dd = deg + mnt/60. + sec/3600.

    return dd


if __name__ == '__main__':                                   # pragma: no cover

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(10)
    app.setFont(ft)

    search4sta = Search4Stations()

    search4sta.lat_spinBox.setValue(45.40)
    search4sta.lon_spinBox.setValue(73.15)
    search4sta.minYear.setValue(1980)
    search4sta.maxYear.setValue(2015)
    search4sta.nbrYear.setValue(20)
    search4sta.finder.isOffline = False

    search4sta.show()

#    search4sta.search_envirocan()
#    search4sta.get_staInfo('QC', 5406)

    sys.exit(app.exec_())
