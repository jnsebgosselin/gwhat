# -*- coding: utf-8 -*-

# Copyright © 2014-2017 Jean-Sebastien Gosselin
# email: jean-sebastien.gosselin@ete.inrs.ca
#
# This file is part of WHAT (Well Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
#
# SearchProgressBar is based on the class FileProgressBar from Spyder.
# Present in spyder.widgets.findinfiles
# Copyright © Spyder Project Contributors
# https://github.com/spyder-ide/spyder

# ---- Standard library imports

from urllib.request import URLError, urlopen
from datetime import datetime
import sys
import time
import os
import re

# ---- Third party imports

from bs4 import BeautifulSoup
import numpy as np
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import QObject, Qt, QPoint, QEvent, QThread
from PyQt5.QtWidgets import (QWidget, QLabel, QDoubleSpinBox, QComboBox,
                             QFrame, QGridLayout, QTableWidget, QCheckBox,
                             QTabWidget, QSpinBox, QPushButton, QDesktopWidget,
                             QApplication, QHeaderView, QTableWidgetItem,
                             QStyle, QFileDialog, QHBoxLayout)

# ---- Local imports

from WHAT.common import IconDB, StyleDB
from WHAT.meteo.weather_stationlist import WeatherSationList
from WHAT.widgets.waitingspinner import QWaitingSpinner


class StationFinder(QObject):

    searchFinished = QSignal(list)
    sig_newstation_found = QSignal(list)
    ConsoleSignal = QSignal(str)

    PAGE_NRESULT = 100  # Number of results per page (maximu m possible is 100)

    def __init__(self, parent=None):
        super(StationFinder, self).__init__(parent)

        self.prov = None
        self.lat = 45.40
        self.lon = 73.15
        self.rad = 25
        self.year_min = 1960
        self.year_max = 2015
        self.nbr_of_years = 5
        self.search_by = 'proximity'  # options are: 'proximity' or 'province'

        self.stationlist = WeatherSationList()
        self.stop_searching = False
        self.isOffline = False
        self.debug_mode = False
        self.station_nbr_found = 0

    def get_base_url(self):
        """Produce the base url that is used to access the CDCD database."""

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
        url += '&selRowPerPage=%d' % self.PAGE_NRESULT

        if self.search_by == 'proximity':
            url += '&cmdProxSubmit=Search'
        elif self.search_by == 'province':
            url += '&cmdProvSubmit=Search'

        return url

    def get_html_from_url(self, url):
        try:
            with urlopen(url) as f:
                html = f.read().decode('utf-8', 'replace')

            return html

        except URLError as e:
            if hasattr(e, 'reason'):
                msg = 'Failed to reach a server.'
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
                print(msg)
                print('Reason: ', e.reason)
            elif hasattr(e, 'code'):
                msg = 'The server couldn\'t fulfill the request.'
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
                print(msg)
                print('Error code: ', e.code)

            return None

    def search_envirocan(self):
        """
        Search on the Government of Canada website for weather stations with
        daily weather data around a decimal degree Lat & Lon coordinate with a
        radius given in km. The results are returned in a list formatted ready
        to be read by Search4Stations widget.

        A signal is emitted with the list if the process is completed
        successfully. If no results are found, only the header is return with
        an empty list of station. If an error is raised, an empty list is
        returned.
        """

        print('Searching weather station on www.http://climate.weather.gc.ca.')
        self.stationlist.clear()

        # ---- Fetch data.

        if self.isOffline:
            with open('url.txt') as f:
                html = f.read()
        else:
            html = self.get_html_from_url(self.get_base_url())
            if self.debug_mode:
                # write downloaded content to local file.
                with open('url.txt', 'w') as local_file:
                    local_file.write(html)

        if html is None:
            print('The search for weather station has failed.')
            self.searchFinished.emit(self.stationlist)
            return self.stationlist

        # ---- Get the number of stations found.

        try:
            nsta = int(findUnique('>(.*?)stations found', html))
            print('%d weather stations found.' % nsta)
            self.station_nbr_found = nsta
        except TypeError:
            self.station_nbr_found = 0
            msg = 'No weather station found.'
            print(msg)
            self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
            self.searchFinished.emit(self.stationlist)
            return

        # ---- Fetch stations page per page.

        Npage = int(np.ceil(nsta/self.PAGE_NRESULT))
        print('Total number of page = % d' % Npage)

        staCount = 0  # global station counter
        for page in range(Npage):
            if self.stop_searching:
                self.searchFinished.emit(self.stationlist)
                return

            print('Page :', page)
            if self.isOffline:
                with open('url4page0.txt') as f:
                    html = f.read()
            else:
                startRow = (self.PAGE_NRESULT*page) + 1
                url = self.get_base_url() + '&startRow=%d' % startRow
                html = self.get_html_from_url(url)
                if self.debug_mode:
                    # Write the results in a local file.
                    filename = 'url4page%d.txt' % page
                    with open(filename, 'w') as local_file:
                        local_file.write(html)

            # ---- Find wheather station data.

            soup = BeautifulSoup(html, 'html.parser')
            while True:
                tag = soup.find("form", attrs={
                        "method": "post",
                        "action": "/climate_data/interform_e.html",
                        "id": "stnRequest%d" % staCount})
                if tag is None:
                    break

                # ---- Station ID and Province

                station_id = tag.find(
                        "input", attrs={"name": "StationID"})["value"]
                province = tag.find(
                        "input", attrs={"name": "Prov"})["value"]

                # ---- Min and Max Years

                dly_range = tag.find(
                        "input", attrs={"name": "dlyRange"})["value"]

                if dly_range == "|":
                    # There is no daily data for this station.
                    start_year = None
                    end_year = None
                    year_range = None
                else:
                    start_year = int(dly_range[:4])
                    end_year = int(dly_range[11:15])
                    year_range = end_year - start_year + 1

                # ---- Station Name

                station_name = tag.findAll(
                        'div', class_="col-lg-3 col-md-3 col-sm-3 col-xs-3")
                station_name = station_name[0].string

                staCount += 1

                if year_range is None:
                    print("Not adding %s (no daily data)" % station_name)
                else:
                    if year_range < self.nbr_of_years:
                        print("Not adding %s (not enough data)" % station_name)
                    else:
                        print("Adding %s to list..." % station_name)

                        if self.stop_searching:
                            self.searchFinished.emit(self.stationlist)
                            return self.stationlist

                        data = self.get_station_info(province, station_id)
                        new_station = [station_name,
                                       station_id,
                                       '%d' % start_year,
                                       '%d' % end_year,
                                       province,
                                       data['Climate ID'],
                                       '%0.3f' % data['Latitude'],
                                       '%0.3f' % data['Longitude'],
                                       '%0.1f' % data['Elevation']]

                        if self.stop_searching:
                            self.searchFinished.emit(self.stationlist)
                            return self.stationlist
                        else:
                            self.stationlist.append(new_station)
                            self.sig_newstation_found.emit(new_station)

        msg = ('%d weather stations with daily data for at least %d years'
               ' between %d and %d'
               ) % (len(self.stationlist), self.nbr_of_years,
                    self.year_min, self.year_max)
        self.ConsoleSignal.emit('<font color=green>%s</font>' % msg)
        print(msg)

        print('Searching for weather station is finished.')
        self.searchFinished.emit(self.stationlist)

        return self.stationlist

    def get_station_info(self, Prov, StationID):
        """
        Fetch weather station information from its Station ID and Province.
        """

        url = ('http://climate.weather.gc.ca/'
               'climate_data/daily_data_e.html?'
               "timeframe=2&Prov=%s&StationID=%s") % (Prov, StationID)

        if self.isOffline:
            with open('urlsinglestation.txt', 'r') as f:
                html = f.read()
                time.sleep(0.25)
        else:
            html = self.get_html_from_url(url)
            if self.debug_mode:
                # Write the downloaded content to a local file.
                with open('urlsinglestation.txt', 'w') as local_file:
                    local_file.write(html)

        soup = BeautifulSoup(html, 'html.parser')
        data = {}

        # ---- Station Name

        tag = soup.find(
                'p', class_="text-center table-header pdng-md mrgn-bttm-0")
        data['Station Name'] = tag.contents[0]

        # ---- Latitude

        tag = soup.find('div', class_="col-lg-6 col-md-7 col-sm-7 col-xs-6",
                        attrs={"aria-labelledby": "latitude"})
        degree = int(tag.contents[0])
        minute = int(tag.contents[2])
        second = float(tag.contents[4])
        data['Latitude'] = dms2decdeg(degree, minute, second)

        # ---- Longitude

        tag = soup.find('div', class_="col-lg-6 col-md-7 col-sm-7 col-xs-6",
                        attrs={"aria-labelledby": "longitude"})
        degree = int(tag.contents[0])
        minute = int(tag.contents[2])
        second = float(tag.contents[4])
        data['Longitude'] = dms2decdeg(degree, minute, second)

        # ---- Elevation

        tag = soup.find('div', class_="col-lg-6 col-md-7 col-sm-7 col-xs-6",
                        attrs={"aria-labelledby": "elevation"})
        data['Elevation'] = float(tag.contents[0])

        # ---- Climate ID

        tag = soup.find('div', class_="col-lg-6 col-md-7 col-sm-7 col-xs-6",
                        attrs={"aria-labelledby": "climateid"})
        data['Climate ID'] = tag.contents[0].strip()

        # ---- Min/Max Years

        tag = soup.find('script', attrs={'type': "text/javascript"})
        maxmindates = findUnique('var maxMin = (.*?);', tag.string)[1:-1]
        maxmindates = maxmindates.replace('"', '').split(',')
        data['Minimum Year'] = int(maxmindates[0])
        data['Maximum Year'] = int(maxmindates[3])

        return data


class Search4Stations(QWidget):
    """
    Widget that allows the user to search for weather stations on the
    Government of Canada website.
    """

    ConsoleSignal = QSignal(str)
    staListSignal = QSignal(list)

    def __init__(self, parent=None):
        super(Search4Stations, self).__init__()

        self.isOffline = False  # For testing and debugging.
        self.__initUI__()
        self.station_table.setGeoCoord((self.lat, self.lon))

        # Setup gap fill worker and thread :
        self.finder = StationFinder()
        self.thread = QThread()
        self.finder.moveToThread(self.thread)
        self.finder.sig_newstation_found.connect(self.add_new_station)
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

        self.progressbar = SearchProgressBar(self)
        self.progressbar.hide()
        self.station_table = WeatherStationDisplayTable(0, self)

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
        left_panel_grid.addWidget(self.tab_widg, 1, 0)
        left_panel_grid.addWidget(self.year_widg, 2, 0)
        left_panel_grid.setRowStretch(3, 100)
        left_panel_grid.addWidget(toolbar_widg, 4, 0)

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
        main_layout.addWidget(self.progressbar, 1, 0, 1, 3)

        main_layout.setContentsMargins(10, 10, 10, 10)  # (L,T,R,B)
        main_layout.setRowStretch(0, 100)
        main_layout.setHorizontalSpacing(15)
        main_layout.setVerticalSpacing(5)
        main_layout.setColumnStretch(col, 100)

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
        Initiate the seach for weather stations. It grabs the info from the
        interface and send it to the method "search_envirocan".
        """
        if self.finder.stop_searching:
            print("The thread is in the process of being stopped: do nothing.")
            return

        if self.thread.isRunning():
            print('Telling the thread to stop searching.')
            self.finder.stop_searching = True
            self.progressbar.setText("Stopping the search process...")
            self.btn_search.setIcon(IconDB().search)
            self.btn_search.setEnabled(False)
            return

        # Update UI state.
        self.year_widg.setEnabled(False)
        self.tab_widg.setEnabled(False)
        self.btn_search.setIcon(IconDB().stop)
        self.station_table.clearContents()
        self.progressbar.show()
        self.progressbar.setText("Searching for weather stations...")
        if self.search_by == 'proximity':
            self.station_table.setGeoCoord((self.lat, self.lon))
        else:
            self.station_table.setGeoCoord(None)

        # Set the attributes of the finder.
        self.finder.prov = self.prov
        self.finder.lat = self.lat
        self.finder.lon = self.lon
        self.finder.rad = self.rad
        self.finder.year_min = self.year_min
        self.finder.year_max = self.year_max
        self.finder.nbr_of_years = self.nbr_of_years
        self.finder.search_by = self.search_by

        # Start searching for weather station.
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

        # Reset the UI.

        self.finder.stop_searching = False
        self.btn_search.setEnabled(True)
        self.btn_search.setIcon(IconDB().search)
        self.year_widg.setEnabled(True)
        self.tab_widg.setEnabled(True)
        self.progressbar.hide()

    def add_new_station(self, info):
        self.station_table.insert_row_at_end(info)
        text = "%d stations found:" % self.finder.station_nbr_found
        text += " fetching info for station %s." % info[0]
        self.progressbar.setText(text)


class SearchProgressBar(QWidget):
    """
    Simple progress spinner with a label.
    SearchProgressBar is based on the class FileProgressBar from Spyder.
    Copyright © Spyder Project Contributors
    https://github.com/spyder-ide/spyder
    """

    def __init__(self, parent):
        super(SearchProgressBar, self).__init__(parent)

        self.status_text = QLabel(self)
        self.spinner = QWaitingSpinner(self, centerOnParent=False)
        self.spinner.setNumberOfLines(10)
        self.spinner.setInnerRadius(2)
        self.spinner.setLineLength(8)
        layout = QHBoxLayout(self)
        layout.addWidget(self.spinner)
        layout.addWidget(self.status_text)
        layout.setContentsMargins(0, 0, 0, 0)

    def setText(self, text):
        self.status_text.setText(text)

    def reset(self):
        self.setText("Searching for stations...")

    def showEvent(self, event):
        """Override Qt method to start the waiting spinner."""
        super(SearchProgressBar, self).showEvent(event)
        self.spinner.start()

    def hideEvent(self, event):
        """Override Qt method to stop the waiting spinner."""
        super(SearchProgressBar, self).hideEvent(event)
        self.spinner.stop()


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
            dist = latlon_to_dist(lat1, lon1, lat2, lon2)

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

        item = self.NumTableWidgetItem(row_data[8], float(row_data[8]))
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

# ---- Utility functions


def latlon_to_dist(lat1, lon1, lat2, lon2):
    """
    Computes the horizontal distance in km between 2 points from geographic
    coordinates given in decimal degrees.

    source:
    www.stackoverflow.com/questions/19412462 (last accessed on 17/01/2014)
    """
    from math import sin, cos, sqrt, atan2, radians

    r = 6373  # r is the Earth radius in km.

    # Convert decimal degrees to radians.
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Compute the horizontal distance between the two points in km.
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2))**2
    c = 2 * atan2(np.sqrt(a), sqrt(1-a))

    dist = r * c

    return dist


def findUnique(pattern, string):
    """
    Return the first result found for the regex search or return None if
    nothing is found.
    """
    result = re.findall(pattern, string)
    if len(result) > 0:
        return result[0].strip()
    else:
        return None


def decdeg2dms(dd):
    """
    Convert decimal degree lat/lon coordinate to decimal, minute,
    second format.
    """

    mnt, sec = divmod(dd*3600, 60)
    deg, mnt = divmod(mnt, 60)

    return deg, mnt, sec


def dms2decdeg(deg, mnt, sec):
    """
    Convert decimal, minute, second format lat/lon coordinate to decimal
    degree.
    """

    dd = deg + mnt/60. + sec/3600.

    return dd


if __name__ == '__main__':

    # ---- Test StationFinder

    if False:
        finder = StationFinder()
        finder.isOffline = False
        finder.lat = 45.40
        finder.lon = 73.15
        finder.year_min = 1960
        finder.year_max = 2015
        finder.nbr_of_years = 10
        finder.search_envirocan()
        print(finder.stationlist)

    # ---- Test Search4Stations

    if True:
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
        # search4sta.finder.debug_mode = True

        search4sta.show()

        sys.exit(app.exec_())
