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

# ---- Standard library imports

import os
import csv
from copy import copy

# ---- Third party imports

import xlsxwriter

# ---- Local imports


class WeatherSationList(list):
    """
    The weather station list contains the following information:
    station names, station ID , year at which the data records begin and year
    at which the data records end, the provinces to which each station belongs,
    the climate ID and the Proximity value in km for the original search
    location.

    All these information can be found on the Government of Canada
    website in the address bar of the web browser when a station is
    selected. Note that the station ID is not the same as the Climate ID
    of the station. For example, the ID for the station Abercorn is 5308,
    as it can be found in the following address:

    http://climate.weather.gc.ca/climateData/dailydata_e.html?timeframe=
    2&Prov=QUE&StationID=5308&dlyRange=1950-12-01|1985-01-31&Year=
    1985&Month=1&Day=01
    """

    HEADER = ['staName', 'stationId', 'StartYear', 'EndYear', 'Province',
              'ClimateID', 'Proximity (km)']

    def __init__(self, filelist=None, *args, **kwargs):
        super(WeatherSationList, self).__init__(*args, **kwargs)
        self._list = []
        self._filename = None
        if filelist:
            self.load_stationlist_from_file(filelist)

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
            except AssertionError:
                continue
            else:
                self.extend(reader[1:])
        else:
            return

    def get_file_content(self):
        file_content = copy(self.HEADER)
        file_content = file_content.extend(self)
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


if __name__ == '__main__':
    pass
