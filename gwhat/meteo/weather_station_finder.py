# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: standard libraries

from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import csv
import time
import os


# ---- Imports: third parties

import numpy as np


# ---- Imports: local libraries

from gwhat.common.utils import calc_dist_from_coord
from gwhat.meteo.weather_stationlist import WeatherSationList
PROV_NAME_ABB = [('ALBERTA', 'AB'),
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


# ---- Base functions

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
    for name, abb in PROV_NAME_ABB:
        df['Province'][df['Province'] == name] = abb

    return df


# ---- API


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
