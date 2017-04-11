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

import os
import csv

# Third party imports :

import h5py


class ProjetReader(object):
    def __init__(self, filename):
        self.__db = None
        self.load_projet(filename)

    def __del__(self):
        self.close_projet()

    @property
    def db(self):  # project data base
        return self.__db

    @property
    def filename(self):
        return self.db.filename

    # =========================================================================

    def load_projet(self, filename):
        self.close_projet()

        print('\nLoading "%s"...' % os.path.basename(filename))

        try:
            self.__db = h5py.File(filename, mode='a')
        except:
            self.convert_projet_format(filename)

        # for newly created project and backward compatibility :

        for key in ['name', 'author', 'created', 'modified', 'version']:
            if key not in list(self.db.attrs.keys()):
                self.db.attrs[key] = 'None'

        for key in ['latitude', 'longitude']:
            if key not in list(self.db.attrs.keys()):
                self.db.attrs[key] = 0

        for key in ['wldsets', 'wxdsets']:
            if key not in list(self.db.keys()):
                self.db.create_group(key)

        print('Project "%s" loaded succesfully\n' % self.name)

    def convert_projet_format(self, filename):
        try:
            print('Old file format. Converting to the new format...')
            with open(filename, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f, delimiter='\t'))

                name = reader[0][1]
                author = reader[1][1]
                created = reader[2][1]
                modified = reader[3][1]
                version = reader[4][1]
                lat = float(reader[6][1])
                lon = float(reader[7][1])
        except:
            self.__db = None
            raise ValueError('Project file is not valid!')
        else:
            os.remove(filename)

            self.__db = db = h5py.File(filename, mode='w')

            db.attrs['name'] = name
            db.attrs['author'] = author
            db.attrs['created'] = created
            db.attrs['modified'] = modified
            db.attrs['version'] = version
            db.attrs['latitude'] = lat
            db.attrs['longitude'] = lon

            print('Projet converted to the new format successfully.')

    def close_projet(self):
        try:
            self.db.close()
        except:
            pass  # projet is None or already closed

    # =========================================================================

    @property
    def name(self):
        return self.db.attrs['name']

    @name.setter
    def name(self, x):
        self.db.attrs['name'] = x

    @property
    def author(self):
        return self.db.attrs['author']

    @author.setter
    def author(self, x):
        self.db.attrs['author'] = x

    @property
    def created(self):
        return self.db.attrs['created']

    @created.setter
    def created(self, x):
        self.db.attrs['created'] = x

    @property
    def modified(self):
        return self.db.attrs['modified']

    @modified.setter
    def modified(self, x):
        self.db.attrs['modified'] = x

    @property
    def version(self):
        return self.db.attrs['version']

    @version.setter
    def version(self, x):
        self.db.attrs['version'] = x

    # -------------------------------------------------------------------------

    @property
    def lat(self):
        return self.db.attrs['latitude']

    @lat.setter
    def lat(self, x):
        self.db.attrs['latitude'] = x

    @property
    def lon(self):
        return self.db.attrs['longitude']

    @lon.setter
    def lon(self, x):
        self.db.attrs['longitude'] = x

    # =========================================================================

    @property
    def wldsets(self):
        return list(self.db['wldsets'].keys())

    def get_wldset(self, name):
        if name in self.wldsets:
            return WLDataFrame(self.db['wldsets/%s' % name])
        else:
            return None

    def add_wldset(self, name, df):
        grp = self.db['wldsets'].create_group(name)

        grp.create_dataset('Time', data=df['Time'])
        grp.create_dataset('WL', data=df['WL'])
        grp.create_dataset('BP', data=df['BP'])
        grp.create_dataset('ET', data=df['ET'])

        grp.attrs['filename'] = df['filename']
        grp.attrs['well'] = df['well']
        grp.attrs['latitude'] = df['latitude']
        grp.attrs['longitude'] = df['longitude']
        grp.attrs['altitude'] = df['altitude']
        grp.attrs['municipality'] = df['municipality']

        grp.create_group('brf')
        grp.create_group('hydrographs')

        print('created new dataset sucessfully')

        return WLDataFrame(grp)

    def del_wldset(self, name):
        del self.db['wldsets/%s' % name]

    # =========================================================================

    @property
    def wxdsets(self):
        return list(self.db['wxdsets'].keys())

    def get_wxdset(self, name):
        if name in self.wxdsets:
            return WXDataReader(self.db['wxdsets/%s' % name])
        else:
            return None

    def add_wxdset(self, name, df):
        grp = self.db['wxdsets'].create_group(name)

    def del_wxdset(self, name):
        del self.db['wxdsets/%s' % name]


class WLDataFrame(object):
    # This is a wrapper around the h5py group that is used to store
    # water level datasets.
    def __init__(self, dset):
        self.dset = dset

    @property
    def filename(self):
        return self.dset.attrs['filename']

    # -------------------------------------------------------------------------

    @property
    def well(self):
        return self.dset.attrs['well']

    @property
    def mun(self):
        return self.dset.attrs['municipality']

    @property
    def lat(self):
        return self.dset.attrs['latitude']

    @property
    def lon(self):
        return self.dset.attrs['longitude']

    @property
    def alt(self):
        return self.dset.attrs['altitude']

    # -------------------------------------------------------------------------

    @property
    def Time(self):
        return self.dset['Time'].value

    @property
    def WL(self):
        return self.dset['WL'].value

    @property
    def BP(self):
        if len(self.dset['BP']) == 0:
            return None
        else:
            return self.dset['BP'].value

    @property
    def ET(self):
        if len(self.dset['ET']) == 0:
            return None
        else:
            return self.dset['ET'].value


class WXDataFrame(object):
    # This is a wrapper around the h5py group that is used to store
    # weather datasets.
    def __init__(self, dset):
        self.dset = dset

    @property
    def station(self):
        return self.dset.attrs['station']
