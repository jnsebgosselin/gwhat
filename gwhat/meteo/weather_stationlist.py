# -*- coding: utf-8 -*-

# Copyright © 2014-2017 Jean-Sebastien Gosselin
# email: jean-sebastien.gosselin@ete.inrs.ca
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# The CheckBoxDelegate and its implementation in the WeatherStationModel is
# based on the codes provided by StackOverflow users Frodon and drexiya.
# https://stackoverflow.com/questions/17748546

# https://github.com/spyder-ide/spyder

# ---- Imports: standard libraries

import os
import csv
from copy import copy
import sys

# ---- Imports: third parties

import numpy as np
import xlsxwriter
from PyQt5.QtCore import (Qt, QAbstractTableModel, QVariant, QEvent, QPoint,
                          QRect)
from PyQt5.QtWidgets import (QApplication, QTableView, QCheckBox, QStyle,
                             QWidget, QStyledItemDelegate, QItemDelegate,
                             QStyleOptionButton, QHeaderView)


# ---- Imports: local

from gwhat.common.utils import calc_dist_from_coord


class WeatherSationList(list):
    """
    The weather station list contains the following information:
    station names, station ID , year at which the data records begin and year
    at which the data records end, the provinces to which each station belongs,
    the climate ID and the Proximity value in km for the original search
    location. Note that the station ID is not the same as the Climate ID
    of the station.
    """

    HEADER = ['staName', 'stationId', 'StartYear', 'EndYear', 'Province',
              'ClimateID', 'Latitude (dd)', 'Longitude (dd)', 'Elevation (m)']

    KEYS = ['Name', 'Station ID', 'DLY First Year', 'DLY Last Year',
            'Province', 'ID', 'Latitude', 'Longitude', 'Elevation']
    DTYPES = [str, str, int, int, str, str, float, float, float]

    def __init__(self, filelist=None, *args, **kwargs):
        super(WeatherSationList, self).__init__(*args, **kwargs)
        if filelist:
            self.load_stationlist_from_file(filelist)

    def __getitem__(self, key):
        if type(key) == str:
            try:
                idx = self.KEYS.index(key)
            except ValueError:
                return None
            else:
                return np.array(self)[:, idx].astype(self.DTYPES[idx])
        else:
            return super(WeatherSationList, self).__getitem__(key)

    def add_stations(self, stations):
        for station in stations:
            if type(station) == list and len(station) != len(self.HEADER):
                raise TypeError
            else:
                self.append(station)

    def remove_stations_at(self, index):
        return self.pop(index)

    def load_stationlist_from_file(self, filelist, overwrite=True):
        if overwrite:
            self.clear()

        if not os.path.exists(filelist):
            print("%s not found." % filelist)
            return

        for d in [',', '\t']:
            try:
                with open(filelist, 'r') as f:
                    reader = list(csv.reader(f, delimiter=d))
                    assert reader[0] == self.HEADER
            except (AssertionError, IndexError):
                continue
            else:
                self.extend(reader[1:])
        else:
            return

    def get_file_content(self):
        file_content = copy(self)
        file_content.insert(0, self.HEADER)
        return file_content

    def save_to_file(self, filename):
        if filename:
            root, ext = os.path.splitext(filename)
            if ext in ['.xlsx', '.xls']:
                with xlsxwriter.Workbook(filename) as wb:
                    ws = wb.add_worksheet()
                    for i, row in enumerate(self.get_file_content()):
                        ws.write_row(i, 0, row)
            else:
                with open(filename, 'w', encoding='utf8')as f:
                    writer = csv.writer(f, delimiter=',', lineterminator='\n')
                    writer.writerows(self.get_file_content())

            print('Station list saved successfully in %s' % filename)

    def format_list_in_html(self):
        """Format the content of the weather station list into a HTML table."""
        html = "<table>"
        html += "<tr>"
        for attrs in self.HEADER:
            html += '<th>%s</th>' % attrs
        html += "<tr>"
        for station in self:
            html += "<tr>"
            for attrs in station:
                html += '<td>%s</td>' % attrs
            html += "</tr>"
        html += "</table>"

        return html


class WeatherSationView(QTableView):
    def __init__(self, parent=None, *args):
        super(WeatherSationView, self).__init__()
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setMinimumWidth(650)
        self.setSortingEnabled(True)

        self.chkbox_header = QCheckBox(self.horizontalHeader())
        self.chkbox_header.setToolTip('Check or uncheck all the weather '
                                      'stations in the table.')
        self.chkbox_header.stateChanged.connect(self.chkbox_header_isClicked)
        self.horizontalHeader().installEventFilter(self)
        self.verticalHeader().hide()

        self.set_geocoord(None)
        self.populate_table(WeatherSationList())

        self.setItemDelegateForColumn(0, CheckBoxDelegate(self))
        self.setColumnWidth(0, 32)
        self.setColumnWidth(3, 75)
        self.setColumnWidth(4, 75)
        self.setColumnWidth(5, 75)
        self.setColumnHidden(7, True)
        self.setColumnHidden(8, True)
        self.setColumnHidden(9, True)
        self.setColumnHidden(10, True)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    @property
    def geocoord(self):
        return self.__latlon

    def set_geocoord(self, latlon):
        self.__latlon = latlon
        self.setColumnHidden(2, latlon is None)
        if latlon and self.stationlist:
            prox = calc_dist_from_coord(self.geocoord[0], self.geocoord[1],
                                        self.stationlist['Latitude'],
                                        self.stationlist['Longitude'])

            model = self.model()
            model._data[:, 2] = prox
            model.dataChanged.emit(model.index(0, 2),
                                   model.index(model.rowCount(0), 2))

    def eventFilter(self, source, event):
        if (event.type() == QEvent.Resize):
            self.resize_chkbox_header()
        return QWidget.eventFilter(self, source, event)

    def chkbox_header_isClicked(self):
        model = self.model()
        model._checks[:] = int(self.chkbox_header.checkState() == Qt.Checked)
        model.dataChanged.emit(model.index(0, 0),
                               model.index(model.rowCount(0), 0))

    def resize_chkbox_header(self):
        h = self.style().pixelMetric(QStyle.PM_IndicatorHeight)
        w = self.style().pixelMetric(QStyle.PM_IndicatorWidth)
        W = self.horizontalHeader().sectionSize(0)
        H = self.horizontalHeader().height()
        y0 = (H - h)//2
        x0 = (W - w)//2
        self.chkbox_header.setGeometry(x0, y0, w, h)

    def populate_table(self, stationlist):
        self.stationlist = stationlist
        N = len(stationlist)
        M = len(WeatherSationModel.HEADER)
        if N == 0:
            data = np.empty((0, M))
        else:
            if self.geocoord:
                prox = calc_dist_from_coord(
                        self.geocoord[0], self.geocoord[1],
                        stationlist['Latitude'], stationlist['Longitude'])
                self.setColumnHidden(2, False)
            else:
                prox = np.empty(N).astype(str)
                self.setColumnHidden(2, True)

            data = np.vstack([np.arange(N).astype(int),
                              stationlist['Name'],
                              prox,
                              stationlist['DLY First Year'],
                              stationlist['DLY Last Year'],
                              stationlist['Province'],
                              stationlist['ID'],
                              stationlist['Station ID'],
                              stationlist['Latitude'],
                              stationlist['Longitude'],
                              stationlist['Elevation']
                              ]).transpose()

        checked = self.chkbox_header.checkState() == Qt.Checked
        self.setModel(WeatherSationModel(data, checked))
        self.model().sort(self.horizontalHeader().sortIndicatorSection(),
                          self.horizontalHeader().sortIndicatorOrder())

    # ---- Utility methods

    def get_row_from_climateid(self, climateid):
        idx = np.where(self.model()._data[:, 6] == climateid)[0]
        if len(idx) > 0:
            return idx[0]
        else:
            return None

    def get_checked_rows(self):
        return np.where(self.model()._checks == 1)[0]

    def get_content4rows(self, rows, daterange='full'):
        """
        Grab the weather station info for the specified rows and
        save the results in a list.
        """
        indexes = self.model()._data[rows, 0]
        stationlist = WeatherSationList()
        for index in indexes:
            stationlist.append(self.stationlist[int(index)])
        return stationlist

    def get_stationlist(self):
        """Get and format the content of the QTableView."""
        indexes = self.model()._data[:, 0]
        stationlist = WeatherSationList()
        for index in indexes:
            stationlist.append(self.stationlist[int(index)])
        return stationlist

    def save_stationlist(self, filename):
        """Save the content of the QTableWidget to file."""
        stationlist = self.get_stationlist()
        stationlist.save_to_file(filename)


class WeatherSationModel(QAbstractTableModel):

    HEADER = ('', 'Weather Stations', 'Proximity\n(km)', 'From \n Year',
              'To \n Year', 'Prov.', 'Climate ID', 'Station ID',
              'Lat.\n(dd)', 'Lon.\n(dd)', 'Elev.\n(m)')

    def __init__(self, data, checked=False):
        super(WeatherSationModel, self).__init__()
        self._data = data
        self._checks = np.ones(len(data)).astype(int) * int(checked)

    def rowCount(self, x):
        return len(self._data)

    def columnCount(self, x):
        return len(self.HEADER)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return self._checks[index.row()]
            elif index.column() == 2:
                return '%0.1f' % float(self._data[index.row(), 2])
            else:
                return str(self._data[index.row(), index.column()])
        if role == Qt.TextAlignmentRole and index.column() != 1:
            return Qt.AlignCenter
        else:
            return QVariant()

    def setData(self, index, value, role=Qt.DisplayRole):
        if index.column() == 0:
            self._checks[index.row()] = value
        return value

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADER[section]
        else:
            return QVariant()

    def flags(self, index):
        if index.column() == 0:
            return (Qt.ItemIsEditable | Qt.ItemIsEnabled)
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def sort(self, column, direction):
        """Sort data according to the selected column and direction."""
        self.layoutAboutToBeChanged.emit()
        if column == 0:
            idx = np.argsort(self._checks)
        elif column == 2:
            idx = np.argsort(self._data[:, column].astype(float))
        else:
            idx = np.argsort(self._data[:, column])
        if direction == Qt.DescendingOrder:
            idx = np.flipud(idx)
        self._data = self._data[idx, :]
        self._checks = self._checks[idx]
        self.layoutChanged.emit()


class CheckBoxDelegate(QStyledItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox in every
    cell of the column to which is is applied.

    CheckBoxDelegate and its implementation in the WeatherStationModel is
    based on the codes provided by StackOverflow users Frodon and drexiya.
    https://stackoverflow.com/questions/17748546
    """
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """
        This is needed otherwise an editor is created if the user clicks in
        this cell.
        """
        return None

    def paint(self, painter, option, index):
        """Paint a checkbox without the label."""

        # print(index.data())
        # checked = True
        check_box_style_option = QStyleOptionButton()

        if int(index.flags() & Qt.ItemIsEditable) > 0:
            check_box_style_option.state |= QStyle.State_Enabled
        else:
            check_box_style_option.state |= QStyle.State_ReadOnly

        if bool(index.data()) is True:
            check_box_style_option.state |= QStyle.State_On
        else:
            check_box_style_option.state |= QStyle.State_Off

        check_box_style_option.rect = self.getCheckBoxRect(option)
        check_box_style_option.state |= QStyle.State_Enabled

        QApplication.style().drawControl(QStyle.CE_CheckBox,
                                         check_box_style_option,
                                         painter)

    def getCheckBoxRect(self, option):
        """Calculate the size and position of the checkbox."""
        cb_rect = QApplication.style().subElementRect(
                QStyle.SE_CheckBoxIndicator, QStyleOptionButton(), None)
        x = option.rect.x() + option.rect.width()/2 - cb_rect.width()/2
        y = option.rect.y() + option.rect.height()/2 - cb_rect.height()/2

        return QRect(QPoint(x, y), cb_rect.size())

    def editorEvent(self, event, model, option, index):
        """
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton and this cell is editable.
        Otherwise do nothing.
        """
        if not int(index.flags() & Qt.ItemIsEditable) > 0:
            return False

        if (event.type() == QEvent.MouseButtonPress
                and event.button() == Qt.LeftButton):
            model.setData(index, int(not bool(index.data())), Qt.EditRole)
            return True
        else:
            return super(CheckBoxDelegate, self).editorEvent(event, model,
                                                             option, index)


if __name__ == '__main__':
    # fname = ("C:\\Users\\jsgosselin\\OneDrive\\GWHAT\\gwhat\\tests\\"
    #          "@ new-prô'jèt!\\weather_station_list.lst")
    # stationlist = WeatherSationList(fname)
    # filecontent = stationlist.get_file_content()

    from gwhat.meteo.weather_station_finder import WeatherStationFinder
    stn_browser = WeatherStationFinder()
    stationlist = stn_browser.get_stationlist()

    app = QApplication(sys.argv)
    view = WeatherSationView()
    view.populate_table(stationlist)
    view.show()

    sys.exit(app.exec_())
