# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).

GWHAT is free software: you can redistribute it and/or modify
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

# ---- Imports: standard libraries

from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import csv
import time
import os


# ---- Imports: third parties

import numpy as np


# ---- Imports: local libraries

from gwhat.meteo.weather_stationlist import WeatherSationList


# ---- Base functions

def calc_dist_from_coord(lat1, lon1, lat2, lon2):
    """
    Compute the  horizontal distance in km between a location given in
    decimal degrees and a set of locations also given in decimal degrees.
    """
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2, lon2 = np.radians(lat2), np.radians(lon2)

    r = 6373  # r is the Earth radius in km

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

    return r * c


def read_stationlist_from_tor():
    """"Read and format the `Station Inventory En.csv` file from Tor ftp."""

    url = "ftp://client_climate@ftp.tor.ec.gc.ca/"
    url += "Pub/Get_More_Data_Plus_de_donnees/Station%20Inventory%20EN.csv"
    try:
        data = urlopen(url).read()
    except (HTTPError, URLError):
        return None
    try:
        data = data.decode('utf-8-sig').splitlines()
    except (UnicodeDecodeError, UnicodeError):
        return None
    data = list(csv.reader(data, delimiter=','))

    FIELDS_KEYS_TYPE = [('Name', 'Name', str),
                        ('Province', 'Province', str),
                        ('Climate ID', 'ID', str),
                        ('Station ID', 'Station ID', str),
                        ('DLY First Year', 'DLY First Year', int),
                        ('DLY Last Year', 'DLY Last Year', int),
                        ('Latitude (Decimal Degrees)', 'Latitude', float),
                        ('Longitude (Decimal Degrees)', 'Longitude', float),
                        ('Elevation (m)', 'Elevation', float)]

    df = {}
    columns = None
    for i, row in enumerate(data):
        if len(row) == 0:
            continue
        if row[0] == 'Name':
            columns = row
            data = np.array(data[i+1:])

            # Remove stations with no daily data
            hly_first_year = data[:, columns.index('DLY First Year')]
            data = data[~(hly_first_year == ''), :]

            break
    else:
        return None

    for field, key, atype in FIELDS_KEYS_TYPE:
        arr = data[:, columns.index(field)]
        if atype == float:
            arr[arr == ''] = np.nan
        else:
            arr[arr == ''] = 'NA'
        df[key] = arr.astype(atype)

    # Sanitarize station name.
    for i in range(len(df['Name'])):
        df['Name'][i].replace('\\', ' ').replace('/', ' ')

    # Determine station status.
    df['Status'] = np.zeros(len(df['Name'])).astype(str)
    df['Status'][df['DLY Last Year'] >= 2017] = 'Active'
    df['Status'][df['DLY Last Year'] < 2017] = 'Closed'

    # Format province value.
    NAME_ABB = [('ALBERTA', 'AB'),
                ('BRITISH COLUMBIA', 'BC'),
                ('MANITOBA', 'MB'),
                ('NEW BRUNSWICK', 'NB'),
                ('NEWFOUNDLAND', 'NL'),
                ('NORTHWEST TERRITORIES', 'NT'),
                ('NOVA SCOTIA', 'NS'),
                ('NUNAVUT', 'NU'),
                ('ONTARIO', 'ON'),
                ('PRINCE EDWARD ISLAND', 'PE'),
                ('QUEBEC', 'QC'),
                ('SASKATCHEWAN', 'SK'),
                ('YUKON TERRITORY', 'YT')]

    for name, abb in NAME_ABB:
        df['Province'][df['Province'] == name] = abb

    return df


class WeatherStationFinder(object):

    DATABASE_FILEPATH = 'climate_station_database.npy'

    def __init__(self, filelist=None, *args, **kwargs):
        super(WeatherStationFinder, self).__init__(*args, **kwargs)
        self._data = None
        self.load_database()

    # ---- Load and fetch database

    @property
    def data(self):
        """Content of the ECCC database."""
        return self._data

    def load_database(self):
        """
        Load the climate station list from a file if it exist or else fetch it
        from ECCC Tor ftp server.
        """
        if os.path.exists(self.DATABASE_FILEPATH):
            ts = time.time()
            self._data = np.load(self.DATABASE_FILEPATH).item()
            te = time.time()
            print("Station list loaded sucessfully in %0.2f sec." % (te-ts))
        else:
            self.fetch_database()

    def fetch_database(self):
        """
        Fetch and read the list of climate stations with daily data
        from the ECCC Tor ftp server and save the result on disk.
        """
        print("Fetching station list from ECCC Tor ftp server...")
        ts = time.time()
        self._data = read_stationlist_from_tor()
        np.save(self.DATABASE_FILEPATH, self._data)
        te = time.time()
        print("Station list fetched sucessfully in %0.2f sec." % (te-ts))

    # ---- Utility functions

    def get_stationlist(self, status=None, prov=None, prox=None, yrange=None):
        """
        Return a list of the stations in the ECCC database that
        fulfill the conditions specified in arguments.
        """
        N = len(self.data['Name'])
        results = np.ones(N)
        if prov:
            results = results * np.isin(self.data['Province'], prov)
        if status:
            results = results * (self.data['Status'] == status)
        if prox:
            lat1, lon1, max_dist = prox
            lat2, lon2 = self.data['Latitude'], self.data['Longitude']
            dists = calc_dist_from_coord(lat1, lon1, lat2, lon2)
            results = results * (dists <= max_dist)
        if yrange:
            arr_ymin = np.max(np.vstack([self.data['DLY First Year'],
                                         np.ones(N)*yrange[0]]), axis=0)
            arr_ymax = np.min(np.vstack([self.data['DLY Last Year'],
                                         np.ones(N)*yrange[1]]), axis=0)
            results = results * ((arr_ymax-arr_ymin+1) >= yrange[2])

        indexes = np.where(results == 1)[0]
        stations = np.vstack((self.data['Name'][indexes],
                              self.data['Station ID'][indexes],
                              self.data['DLY First Year'][indexes],
                              self.data['DLY Last Year'][indexes],
                              self.data['Province'][indexes],
                              self.data['ID'][indexes],
                              self.data['Latitude'][indexes],
                              self.data['Longitude'][indexes],
                              self.data['Elevation'][indexes],
                              )).transpose().tolist()

        stationlist = WeatherSationList()
        stationlist.add_stations(stations)

        return stationlist


if __name__ == '__main__':
    stn_browser = WeatherStationFinder()
    stnlist = stn_browser.get_stationlist(prov=['QC', 'ON'],
                                          prox=(45.40, -73.15, 25),
                                          yrange=(1960, 2015, 10))
