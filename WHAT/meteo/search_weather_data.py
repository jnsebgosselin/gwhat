# -*- coding: utf-8 -*-
"""
Copyright 2014-2016 Jean-Sebastien Gosselin
email: jnsebgosselin@gmail.com

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
except:
    from urllib.request import URLError, urlopen
from datetime import datetime
import sys
import csv

# Third party imports :

import numpy as np
from PySide import QtGui, QtCore

# Local imports :

try:
    import common.database as db
    from common import IconDB, StyleDB
    import common.widgets as myqt
except ImportError:  # to run this module standalone
    import sys
    from os.path import dirname, realpath, basename
    print('Running module %s as a standalone script...' % basename(__file__))
    sys.path.append(dirname(dirname(realpath(__file__))))

    from common import IconDB, StyleDB
    import common.database as db
    import common.widgets as myqt


# =============================================================================


class Tooltips():

    def __init__(self, language):  # ---------------------------- ENGLISH -----

        # ---- Search4Stations ----

        self.btn_addSta = ('Add selected found weather stations to the '
                           'current list of weather stations.')
        self.btn_search = ('Search for weather stations in the online CDCD ' +
                           'with the criteria given above.')

        # ---- WeatherStationDisplayTable ----

        self.chkbox_header = ('Check of uncheck all the weather stations ' +
                              'in the table.')

        if language == 'French':  # ------------------------------ FRENCH -----
            pass


# =============================================================================
class Search4Stations(QtGui.QWidget):
# =============================================================================

    '''
    Widget that allows the user to search for weather stations on the
    Government of Canada website.
    '''

    ConsoleSignal = QtCore.Signal(str)
    staListSignal = QtCore.Signal(list)

    def __init__(self, parent=None):  # =======================================
        super(Search4Stations, self).__init__(parent)

        self.initUI()

    def initUI(self):  # ======================================================

        # ------------------------------------------------------- DATABASE ----

        ttipDB = Tooltips('English')

        #----------------------------------------------------- MAIN WINDOW ----

        self.setWindowTitle('Search for Weather Stations')
        self.setWindowIcon(IconDB().master)
        self.setWindowFlags(QtCore.Qt.Window)

        #-------------------------------------------------- INIT VARIABLES ----

        now = datetime.now()

        self.station_table = WeatherStationDisplayTable(0, self)
        self.isOffline = False  # For testing and debugging purpose

        #---------------------------------------------- Tab Widget Search ----

        #---- Search by Proximity ----

        label_Lat = QtGui.QLabel('Latitude :')
        label_Lat2 = QtGui.QLabel('North')

        self.lat_spinBox = QtGui.QDoubleSpinBox()
        self.lat_spinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.lat_spinBox.setSingleStep(0.1)
        self.lat_spinBox.setValue(0)
        self.lat_spinBox.setMinimum(0)
        self.lat_spinBox.setMaximum(180)
        self.lat_spinBox.setSuffix(u' °')

        label_Lon = QtGui.QLabel('Longitude :')
        label_Lon2 = QtGui.QLabel('West')

        self.lon_spinBox = QtGui.QDoubleSpinBox()
        self.lon_spinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.lon_spinBox.setSingleStep(0.1)
        self.lon_spinBox.setValue(0)
        self.lon_spinBox.setMinimum(0)
        self.lon_spinBox.setMaximum(180)
        self.lon_spinBox.setSuffix(u' °')

        self.radius_SpinBox = QtGui.QComboBox()
        self.radius_SpinBox.addItems(['25 km', '50 km', '100 km', '200 km'])

#        self.radius_SpinBox = QtGui.QSpinBox()
#        self.radius_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
#        self.radius_SpinBox.setSingleStep(5)
#        self.radius_SpinBox.setValue(25)
#        self.radius_SpinBox.setMinimum(5)
#        self.radius_SpinBox.setMaximum(500)
#        self.radius_SpinBox.setSuffix(' km')

        prox_search_widg = QtGui.QWidget()
        prox_search_grid = QtGui.QGridLayout()

        row, col = 0, 1
        prox_search_grid.addWidget(label_Lat, row, col)
        prox_search_grid.addWidget(self.lat_spinBox, row, col+1)
        prox_search_grid.addWidget(label_Lat2, row, col+2)
        row += 1
        prox_search_grid.addWidget(label_Lon, row, col)
        prox_search_grid.addWidget(self.lon_spinBox, row, col+1)
        prox_search_grid.addWidget(label_Lon2, row, col+2)
        row += 1
        prox_search_grid.addWidget(QtGui.QLabel('Search Radius :'), row, col)
        prox_search_grid.addWidget(self.radius_SpinBox, row, col+1)

        prox_search_grid.setColumnStretch(0, 100)
        prox_search_grid.setColumnStretch(col+3, 100)
        prox_search_grid.setRowStretch(row + 1, 100)
        prox_search_grid.setHorizontalSpacing(20)
        prox_search_grid.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        prox_search_widg.setLayout(prox_search_grid)

        #---- Search by Province ----

        self.prov_widg = QtGui.QComboBox()
        self.prov_widg.addItems(['QC', 'AB'])

        prov_search_widg = QtGui.QFrame()
        prov_search_grid = QtGui.QGridLayout()

        prov_search_grid.addWidget(QtGui.QLabel('Province :'), 1, 1)
        prov_search_grid.addWidget(self.prov_widg, 1, 2)

#        prov_search_grid.setColumnStretch(0, 100)
        prov_search_grid.setColumnStretch(3, 100)
        prov_search_grid.setRowStretch(0, 100)
        prov_search_grid.setRowStretch(2, 100)

        prov_search_widg.setLayout(prov_search_grid)

        #---- Assemble TabWidget ----

        self.tab_widg = QtGui.QTabWidget()

        self.tab_widg.addTab(prox_search_widg, 'Proximity')
        self.tab_widg.addTab(prov_search_widg, 'Province')

        #--------------------------------------------------- Year Criteria ----

        label_date = QtGui.QLabel('Search for stations with data available')

        #---- subgrid year boundary ----

        label_between = QtGui.QLabel('between')
        label_between.setAlignment(QtCore.Qt.AlignCenter)

        self.minYear = QtGui.QSpinBox()
        self.minYear.setAlignment(QtCore.Qt.AlignCenter)
        self.minYear.setSingleStep(1)
        self.minYear.setMinimum(1840)
        self.minYear.setMaximum(now.year)
        self.minYear.setValue(1840)

        label_and = QtGui.QLabel('and')
        label_and.setAlignment(QtCore.Qt.AlignCenter)

        self.maxYear = QtGui.QSpinBox()
        self.maxYear.setAlignment(QtCore.Qt.AlignCenter)
        self.maxYear.setSingleStep(1)
        self.maxYear.setMinimum(1840)
        self.maxYear.setMaximum(now.year)
        self.maxYear.setValue(now.year)

        yearbound_widget = QtGui.QFrame()
        yearbound_grid = QtGui.QGridLayout()

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

        #---- subgrid min. nbr. of years ----

        label_4atleast = QtGui.QLabel('for at least')
        label_years = QtGui.QLabel('years')

        self.nbrYear = QtGui.QSpinBox()
        self.nbrYear.setAlignment(QtCore.Qt.AlignCenter)
        self.nbrYear.setSingleStep(1)
        self.nbrYear.setMinimum(0)
        self.nbrYear.setValue(3)

        subwidg1 = QtGui.QWidget()
        subgrid1 = QtGui.QGridLayout()

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

        #---- maingrid ----

        year_widg = QtGui.QFrame()
        year_widg.setFrameStyle(0)  # styleDB.frame

        year_grid = QtGui.QGridLayout()

        row = 1
        year_grid.addWidget(label_date, row, 0)
        row += 1
        year_grid.addWidget(yearbound_widget, row, 0)
        row += 1
        year_grid.addWidget(subwidg1, row, 0)

        year_grid.setVerticalSpacing(20)
        year_grid.setRowStretch(0, 100)
        year_grid.setContentsMargins(15, 0, 15, 0)  # (L, T, R, B)

        year_widg.setLayout(year_grid)

        # -------------------------------------------------------- TOOLBAR ----

        self.btn_search = QtGui.QPushButton('Search Stations')
        self.btn_search.setIcon(IconDB().search)
        self.btn_search.setIconSize(IconDB().iconSize2)
        self.btn_search.setToolTip(ttipDB.btn_search)

        btn_addSta = QtGui.QPushButton('Add Stations')
        btn_addSta.setIcon(IconDB().add2list)
        btn_addSta.setIconSize(IconDB().iconSize2)
        btn_addSta.setToolTip(ttipDB.btn_addSta)

        toolbar_grid = QtGui.QGridLayout()
        toolbar_widg = QtGui.QWidget()

        row = 0
        col = 1
        toolbar_grid.addWidget(self.btn_search, row, col)
        col += 1
        toolbar_grid.addWidget(btn_addSta, row, col)

        toolbar_grid.setColumnStretch(col+1, 100)
        toolbar_grid.setColumnStretch(0, 100)
        toolbar_grid.setSpacing(5)
        toolbar_grid.setContentsMargins(0, 30, 0, 0)  # (L, T, R, B)

        toolbar_widg.setLayout(toolbar_grid)

        # ---------------------------------------------------- Left Panel ----

        panel_title = QtGui.QLabel('<b>Weather Station Search Criteria :</b>')

        left_panel = QtGui.QFrame()
        left_panel_grid = QtGui.QGridLayout()

#        self.statusBar = QtGui.QStatusBar()
#        self.statusBar.setSizeGripEnabled(False)

        row = 0
        left_panel_grid.addWidget(panel_title, row, 0)
        row += 1
        left_panel_grid.addWidget(self.tab_widg, row, 0)
        row += 1
        left_panel_grid.addWidget(year_widg, row, 0)
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

        vLine1 = QtGui.QFrame()
        vLine1.setFrameStyle(StyleDB().VLine)

        # ---- GRID ----

        grid_search4stations = QtGui.QGridLayout()

        row = 0
        col = 0
        grid_search4stations.addWidget(left_panel, row, col)
        col += 1
        grid_search4stations.addWidget(vLine1, row, col)
        col += 1
        grid_search4stations.addWidget(self.station_table, row, col)

        grid_search4stations.setContentsMargins(10, 10, 10, 10)  # (L,T,R,B)
        grid_search4stations.setSpacing(15)
        grid_search4stations.setColumnStretch(col, 100)

        self.setLayout(grid_search4stations)

        # --------------------------------------------------------- EVENTS ----

        self.minYear.valueChanged.connect(self.minYear_changed)
        self.maxYear.valueChanged.connect(self.maxYear_changed)
        self.btn_search.clicked.connect(self.btn_search_isClicked)
        btn_addSta.clicked.connect(self.btn_addSta_isClicked)

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
            cp = parent.mapToGlobal(QtCore.QPoint(wp/2., hp/2.))
        else:
            cp = QtGui.QDesktopWidget().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.setFixedSize(self.size())

    # =========================================================================

    def minYear_changed(self):

        min_yr = min_yr = max(self.minYear.value(), 1840)

        now = datetime.now()
        max_yr = now.year

        self.maxYear.setRange(min_yr, max_yr)

    def maxYear_changed(self):  # =============================================

        min_yr = 1840

        now = datetime.now()
        max_yr = min(self.maxYear.value(), now.year)

        self.minYear.setRange(min_yr, max_yr)

    def btn_addSta_isClicked(self):  # ========================================

        rows = self.station_table.get_checked_rows()
        if len(rows) > 0:
            staList = self.station_table.get_content4rows(rows)
            self.staListSignal.emit(staList)
            print('Selected stations sent to list')
        else:
            msg = 'No station currently selected'
            print(msg)

    def btn_search_isClicked(self):  # ========================================
        """
        Initiate the seach for weather stations. It grabs the info from the
        interface and send it to the method "search_envirocan".
        """

        # ---- Generate New List ----

        # http://doc.qt.io/qt-5/qt.html#CursorShape-enum
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        msg = 'Searching for weather stations. Please wait...'
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)

        print('\n--------------------------------')
        print('SEARCHING FOR STATIONS')
        print('--------------------------------\n')

        QtCore.QCoreApplication.processEvents()
        QtCore.QCoreApplication.processEvents()

        self.search_envirocan()

        QtGui.QApplication.restoreOverrideCursor()

        print('\n--------------------------------\n')

    def search_envirocan(self):  # ============================================
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

        PROV = self.prov_widg.currentText()
        LAT = self.lat_spinBox.value()
        LON = self.lon_spinBox.value()
        RADIUS = self.radius_SpinBox.currentText()
        RADIUS = int(RADIUS[:-3])
        YearMin = self.minYear.value()
        YearMax = self.maxYear.value()
        nbrYear = self.nbrYear.value()

        Nmax = 100.  # Number of results per page (maximum possible is 100)

        staList = []  # [station_name, station_id, start_year,
                      #  end_year, province, climate_id, station_proxim]

        #------------------------------------------------------ define url ----

        # Last updated: May 25th, 2016

        url = ('http://climate.weather.gc.ca/historical_data/'
               'search_historic_data_stations_e.html?')

        if self.tab_widg.currentIndex() == 0:
            url += 'searchType=stnProx&timeframe=1&txtRadius=%d' % RADIUS
            url += '&selCity=&selPark=&optProxType=custom'

            deg, mnt, sec = decdeg2dms(np.abs(LAT))
            url += '&txtCentralLatDeg=%d' % deg
            url += '&txtCentralLatMin=%d' % mnt
            url += '&txtCentralLatSec=%d' % sec

            deg, mnt, sec = decdeg2dms(np.abs(LON))
            url += '&txtCentralLongDeg=%d' % deg
            url += '&txtCentralLongMin=%d' % mnt
            url += '&txtCentralLongSec=%d' % sec
        elif self.tab_widg.currentIndex() == 1:
            url += 'searchType=stnProv&timeframe=1&lstProvince=%s' % PROV

        url += '&optLimit=yearRange'
        url += '&StartYear=%d' % YearMin
        url += '&EndYear=%d' % YearMax
        url += '&Year=2013&Month=6&Day=4'
        url += '&selRowPerPage=%d' % Nmax

        if self.tab_widg.currentIndex() == 0:
            url += '&cmdProxSubmit=Search'
        elif self.tab_widg.currentIndex() == 1:
            url += '&cmdProvSubmit=Search'

        #------------------------------------------------------ fetch data ----

        try:
            if self.isOffline:
                with open('url.txt', 'r') as f:
                    stnresults = f.read()
            else:
                f = urlopen(url)
                stnresults = f.read().decode('utf-8', 'replace')

                # write downloaded content to local file for debugging purpose:
                with open('url.txt', 'w') as local_file:
                    local_file.write(stnresults)

            #-- Number of Stations Found --

            if self.tab_widg.currentIndex() == 0:
                txt2find = 'stations found within a search radius'
            if self.tab_widg.currentIndex() == 1:
                txt2find = 'locations match'

            indx_e = stnresults.find(txt2find, 0)
            if indx_e == -1:
                msg = 'No weather station found.'
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
                print(msg)

                return staList

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
                print('Page :', page)

                startRow = (Nmax * page) + 1
                url4page = url + '&startRow=%d' % startRow
                if self.isOffline:
                    with open('url.txt') as f:
                        stnresults = f.read()
                else:
                    f = urlopen(url4page)
                    stnresults = f.read().decode('utf-8')

                    # Write result in a local file for debugging purposes:

                    filename = 'url4page%d.txt' % page
                    with open(filename, 'w') as local_file:
                        local_file.write(stnresults)

                # Scan each row of the current page :
                while 1:

                    #---- Location of station information block ----

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

                    #---- StartDate and EndDate ----

                    txt2find = 'name="dlyRange" value="'
                    n = len(txt2find)
                    indx_0 = stnresults.find(txt2find, indx_e)
                    indx_e = stnresults.find('|', indx_0)

                    start_year = stnresults[indx_0+n:indx_0+n+4]
                    end_year = stnresults[indx_e+1:indx_e+1+4]

                    #---- StationID ----

                    txt2find = 'name="StationID" value="'
                    indx_0 = stnresults.find(txt2find, indx_e) + len(txt2find)
                    indx_e = stnresults.find('"', indx_0)

                    station_id = stnresults[indx_0:indx_e].strip()

                    #---- Province ----

                    txt2find = 'name="Prov" value="'
                    indx_0 = stnresults.find(txt2find, indx_e) + len(txt2find)
                    indx_e = stnresults.find('"', indx_0)

                    province = stnresults[indx_0:indx_e].strip()

                    #---- Station Name ----

                    txt2find = ('<div class="col-lg-3 col-md-3'
                                ' col-sm-3 col-xs-3">')
                    indx_0 = stnresults.find(txt2find, indx_e) + len(txt2find)
                    indx_e = stnresults.find('</div>', indx_0)

                    station_name = stnresults[indx_0:indx_e].strip()

                    #---- Proximity ----

                    if self.tab_widg.currentIndex() == 0:
                        txt2find = ('<div class="col-lg-2 col-md-2'
                                    ' col-sm-2 col-xs-2">')
                        indx_0 = (stnresults.find(txt2find, indx_e) +
                                  len(txt2find))
                        indx_e = stnresults.find('</div>', indx_0)

                        station_proxim = stnresults[indx_0:indx_e].strip()
                    elif self.tab_widg.currentIndex() == 1:
                        station_proxim = 0

                    if start_year.isdigit():  # daily data exist
                        if (int(end_year)-int(start_year)+1) >= nbrYear:

                            print("Adding %s to list..." % station_name)

                            #---- Climate ID ----

                            staInfo = self.get_staInfo(province,
                                                       station_id)
                            climate_id = staInfo[5]

                            #---- Send Signal to UI ----

                            staList.append([station_name, station_id,
                                            start_year, end_year, province,
                                            climate_id, station_proxim])

                            self.station_table.populate_table(staList)
                            QtCore.QCoreApplication.processEvents()
                            QtCore.QCoreApplication.processEvents()

                        else:
                            print("Not adding %s (not enough data)"
                                  % station_name)
                    else:
                        print("Not adding %s (no daily data)"
                              % station_name)

                    staCount += 1

            msg = ('%d weather stations with daily data for at least %d years'
                   ' between %d and %d'
                   ) % (len(staList), nbrYear, YearMin, YearMax)
            self.ConsoleSignal.emit('<font color=green>%s</font>' % msg)
            print(msg)

            QtCore.QCoreApplication.processEvents()
            QtCore.QCoreApplication.processEvents()

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

        return staList

    def get_staInfo(self, Prov, StationID):  # ================================
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
            with open('urlsingle.txt', 'r') as f:
                urlread = f.read()
        else:
            f = urlopen(url)
            urlread = f.read().decode('utf-8')

            # Write result in a local file for debugging purposes:

            with open('urlsinglestation.txt', 'w') as local_file:
                local_file.write(urlread)

        #---- Station Name ----

        txt2find = '<p class="text-center table-header pdng-md mrgn-bttm-0">'
        n = len(txt2find)
        indx_0 = urlread.find(txt2find, 0) + n
        indx_e = urlread.find('<br/>', indx_0)

        staName = urlread[indx_0:indx_e]
        staName = staName.strip()

        #---- Climate ID ----

        txt2find = ('aria-labelledby="climateid">')
        n = len(txt2find)

        indx_0 = urlread.find(txt2find, 0) + n
        indx_e = urlread.find('</div>', indx_0)

        climate_id = urlread[indx_0:indx_e]
        climate_id = climate_id.strip()

        #---- Start Year ----

        txt2find = '<option value="'
        n = len(txt2find)
        indx_0 = urlread.find(txt2find, indx_e) + n

        startYear = urlread[indx_0:indx_0+4]

        #---- End Year ----

        txt2find = '" selected="'
        indx_e = urlread.find(txt2find, indx_0)

        endYear = urlread[indx_e-4:indx_e]

        #---- Proximity ----

        proximity = np.nan

        print('%s (%s) : %s - %s' % (staName, climate_id, startYear, endYear))

        staInfo = [staName, StationID, startYear, endYear,
                   Prov, climate_id, proximity]

        return staInfo


# =============================================================================


class WeatherStationDisplayTable(QtGui.QTableWidget):
    """
    Widget for displaying a weather station list.

    #---- Inputs ----

    year_display_mode : 0 -> Years are displayed in a standard
                             QTableWidget cell
                        1 -> Years are displayed in a QComboBox
    """

    def __init__(self, year_display_mode=0, parent=None):  # ==================
        super(WeatherStationDisplayTable, self).__init__(parent)

        self.year_display_mode = year_display_mode
        self.initUI()

    def initUI(self):  # ======================================================

        ttipDB = Tooltips('English')

        # ----------------------------------------------------------- Style ----

        self.setFont(StyleDB().font1)
        self.setFrameStyle(StyleDB().frame)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setMinimumWidth(650)

        # --------------------------------------------------------- Header ----

        # http://stackoverflow.com/questions/9744975/
        # pyside-pyqt4-adding-a-checkbox-to-qtablewidget-
        # horizontal-column-header

        self.chkbox_header = QtGui.QCheckBox(self.horizontalHeader())
        self.chkbox_header.setToolTip(ttipDB.chkbox_header)
        self.horizontalHeader().installEventFilter(self)

        HEADER = ('', 'Weather Stations', 'Proximity \n (km)', 'From \n Year',
                  'To \n Year', 'Prov.', 'Climate ID', 'Station ID')

        self.setColumnCount(len(HEADER))
        self.setHorizontalHeaderLabels(HEADER)
        self.verticalHeader().hide()

        #---------------------------------------------- Column Size Policy ----

#        self.setColumnHidden(6, True)
        self.setColumnHidden(7, True)

        self.setColumnWidth(0, 32)
        self.setColumnWidth(3, 75)
        self.setColumnWidth(4, 75)
        self.setColumnWidth(5, 75)

        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)

        #---------------------------------------------------------- Events ----

        self.chkbox_header.stateChanged.connect(self.chkbox_header_isClicked)

    class NumTableWidgetItem(QtGui.QTableWidgetItem):  # ======================

        # To be able to sort numerical item within a given column.

        # http://stackoverflow.com/questions/12673598/
        # python-numerical-sorting-in-qtablewidget

            def __init__(self, text, sortKey):
                QtGui.QTableWidgetItem.__init__(
                    self, text, QtGui.QTableWidgetItem.UserType)
                self.sortKey = sortKey

            # Qt uses a simple < check for sorting items, override this to use
            # the sortKey
            def __lt__(self, other):
                return self.sortKey < other.sortKey

    def eventFilter(self, source, event):  # ==================================

        # http://stackoverflow.com/questions/13788452/
        # pyqt-how-to-handle-event-without-inheritance

        if (event.type() == QtCore.QEvent.Type.Resize):
            self.resize_chkbox_header()

        return QtGui.QWidget.eventFilter(self, source, event)

    def resize_chkbox_header(self):  # ========================================

        h = self.style().pixelMetric(QtGui.QStyle.PM_IndicatorHeight)
        w = self.style().pixelMetric(QtGui.QStyle.PM_IndicatorWidth)

        W = self.horizontalHeader().sectionSize(0)
        H = self.horizontalHeader().height()

        y0 = int((H - h) / 2)
        x0 = int((W - w) / 2)

        self.chkbox_header.setGeometry(x0, y0, w, h)

    def chkbox_header_isClicked(self):  # =====================================

        nrow = self.rowCount()

        for row in range(nrow):
            item = self.cellWidget(row, 0).layout().itemAtPosition(1, 1)
            widget = item.widget()
            widget.setCheckState(self.chkbox_header.checkState())

    def populate_table(self, staList):  # =====================================

        self.chkbox_header.setCheckState(QtCore.Qt.CheckState(False))

        nrow = len(staList)
        self.setRowCount(nrow)
        self.setSortingEnabled(False)

        for row in range(nrow):

            # More Options:

            # item.setFlags(QtCore.Qt.ItemIsEnabled &
            #               ~QtCore.Qt.ItemIsEditable)
            # item.setTextAlignment(QtCore.Qt.AlignLeft |
            #                       QtCore.Qt.AlignVCenter)

            # ---- Checkbox ----

            col = 0

            item = QtGui.QTableWidgetItem('')
            item.setFlags(~QtCore.Qt.ItemIsEditable & QtCore.Qt.ItemIsEnabled)
            self.setItem(row, col, item)

            chckbox_center = QtGui.QWidget()
            chckbox_grid = QtGui.QGridLayout()
            chckbox_grid.addWidget(QtGui.QCheckBox(), 1, 1)
            chckbox_grid.setColumnStretch(0, 100)
            chckbox_grid.setColumnStretch(2, 100)
            chckbox_grid.setContentsMargins(0, 0, 0, 0)  # [L, T, R, B]
            chckbox_center.setLayout(chckbox_grid)

#            print center_widg.layout().itemAtPosition(1,1)

            self.setCellWidget(row, col, chckbox_center)
#            self.setCellWidget(row, col, center_widg)

            # ---- Weather Station ----

            col += 1

            item = QtGui.QTableWidgetItem(staList[row][0])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setToolTip(staList[row][0])
            self.setItem(row, col, item)

            # ---- Proximity ----

            col += 1

            item = self.NumTableWidgetItem('%0.2f' % float(staList[row][6]),
                                           float(staList[row][6]))
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, col, item)

            # ---- From Year ----

            # ----
            min_year = int(staList[row][2])
            max_year = int(staList[row][3])
            yearspan = np.arange(min_year, max_year+1).astype(str)
            # ----

            col += 1

            item = QtGui.QTableWidgetItem(staList[row][2])
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(row, col, item)
            item.setTextAlignment(QtCore.Qt.AlignCenter)

            if self.year_display_mode == 1:

                item.setFlags(QtCore.Qt.ItemIsEnabled)

                self.fromYear = QtGui.QComboBox()
                self.fromYear.setFixedWidth(75)
                self.fromYear.setInsertPolicy(QtGui.QComboBox.NoInsert)
                self.fromYear.addItems(yearspan)
                self.fromYear.setMinimumContentsLength(4)
                self.fromYear.setSizeAdjustPolicy(
                    QtGui.QComboBox.AdjustToMinimumContentsLength)

                self.setCellWidget(row, col, self.fromYear)

            #c---- To Year ----

            col += 1

            item = QtGui.QTableWidgetItem(staList[row][3])

            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)

            self.setItem(row, col, item)

            if self.year_display_mode == 1:

                item.setFlags(QtCore.Qt.ItemIsEnabled)

                self.toYear = QtGui.QComboBox()
                self.toYear.setFixedWidth(75)
                self.toYear.setInsertPolicy(QtGui.QComboBox.NoInsert)
                self.toYear.addItems(yearspan)
                self.toYear.setCurrentIndex(len(yearspan)-1)
                self.toYear.setMinimumContentsLength(4)
                self.toYear.setSizeAdjustPolicy(
                    QtGui.QComboBox.AdjustToMinimumContentsLength)

                self.setCellWidget(row, col, self.toYear)

            # ---- Province ----

            col += 1

            item = QtGui.QTableWidgetItem(staList[row][4])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, col, item)

            # ---- Climate ID (hidden) ----

            col += 1

            item = QtGui.QTableWidgetItem(staList[row][5])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, col, item)

            # ---- Station ID ----

            col += 1

            item = QtGui.QTableWidgetItem(staList[row][1])
            self.setItem(row, col, item)

        self.setSortingEnabled(True)

    def get_checked_rows(self):

        nrow = self.rowCount()
        rows = []

        # http://www.qtfr.org/viewtopic.php?id=16337

        for row in range(nrow):
            item = self.cellWidget(row, 0).layout().itemAtPosition(1, 1)
            widget = item.widget()
            if widget.isChecked():
                rows.append(row)

        return rows

    def get_content4rows(self, rows):  # ======================================
        '''
        grabs weather station info that are selected and saving them
        in a list. The structure of "weather_stations.lst" is preserved
        in the process.
        '''

        staList = []

        for row in rows:

            # --------
            # staList structure:

            # [staName, stationId, StartYear, EndYear,
            #  Province, ClimateID, Proximity (km)]

            # staTable structure:

            # ('', 'Weather Stations', 'Proximity \n (km)', 'From \n Year',
            #  'To \n Year', 'Prov.', 'Climate ID', 'Station ID')
            # --------

            sta2add = [self.item(row, 1).text(),
                       self.item(row, 7).text(),
                       self.item(row, 3).text(),
                       self.item(row, 4).text(),
                       self.item(row, 5).text(),
                       self.item(row, 6).text(),
                       self.item(row, 2).text()]

            staList.append(sta2add)

        return staList

    def delete_rows(self, rows):  # ===========================================

        # Going in reverse order to preserve indexes while
        # scanning the rows if any are deleted.

        for row in reversed(rows):
            print('Removing %s (%s)' % (self.item(row, 1).text(),
                                        self.item(row, 6).text()))

            self.removeRow(row)

    def save_staList(self, filename):  # ======================================

        headerDB = [['staName', 'stationId', 'StartYear',
                     'EndYear', 'Province', 'ClimateID',
                     'Proximity (km)']]

        # ---- Grab the content of the entire table ----

        rows = range(self.rowCount())
        staList = self.get_content4rows(rows)

        # ---- Insert Header----

        staList.insert(0, headerDB.weather_stations[0])

        # ---- saving results ----

        with open(filename, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
            writer.writerows(staList)


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


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(10)
    app.setFont(ft)

    search4sta = Search4Stations()

    search4sta.lat_spinBox.setValue(45.4)
    search4sta.lon_spinBox.setValue(73.13)
    search4sta.isOffline = False

    search4sta.show()

#    search4sta.search_envirocan()
#    search4sta.get_staInfo('QC', 5406)

    sys.exit(app.exec_())
