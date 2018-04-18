# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# ---- Import: Standard Libraries

import os
import csv
import os.path as osp

# ---- Imports: Third Parties

import h5py
import numpy as np

# ---- Imports: Local Librairies

from gwhat.meteo.weather_reader import WXDataFrameBase


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

    @property
    def dirname(self):
        return os.path.dirname(self.filename)

    # =========================================================================

    def load_projet(self, filename):
        self.close_projet()

        print('\nLoading "%s"...' % os.path.basename(filename))

        try:
            # The condition below is required to circumvent a bug of h5py
            # https://github.com/h5py/h5py/issues/896
            if os.path.exists(filename):
                self.__db = h5py.File(filename, mode='a')
            else:
                self.__db = h5py.File(filename, mode='w')
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
        except AttributeError:
            # projet is None or already closed.
            pass

    # ---- Project Properties

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

    # ---- Water Levels Dataset Handlers

    @property
    def wldsets(self):
        return list(self.db['wldsets'].keys())

    def get_wldset(self, name):
        if name in self.wldsets:
            return WLDataFrameHDF5(self.db['wldsets/%s' % name])
        else:
            return None

    def add_wldset(self, name, df):
        try:
            grp = self.db['wldsets'].create_group(name)

            # Water level data
            grp.create_dataset('Time', data=df['Time'])
            grp.create_dataset('WL', data=df['WL'])
            grp.create_dataset('BP', data=df['BP'])
            grp.create_dataset('ET', data=df['ET'])

            # Piezometric well info
            grp.attrs['filename'] = df['filename']
            grp.attrs['Well'] = df['Well']
            grp.attrs['Well ID'] = df['Well ID']
            grp.attrs['Latitude'] = df['Latitude']
            grp.attrs['Longitude'] = df['Longitude']
            grp.attrs['Elevation'] = df['Elevation']
            grp.attrs['Municipality'] = df['Municipality']
            grp.attrs['Province'] = df['Province']

            # Master Recession Curve
            mrc = grp.create_group('mrc')
            mrc.attrs['exists'] = 0
            mrc.create_dataset('params', data=(0, 0), dtype='float64')
            mrc.create_dataset('peak_indx', data=np.array([]),
                               dtype='int16', maxshape=(None,))
            mrc.create_dataset('recess', data=np.array([]),
                               dtype='float64', maxshape=(None,))
            mrc.create_dataset('time', data=np.array([]),
                               dtype='float64', maxshape=(None,))

            # Barometric Response Function
            grp.create_group('brf')

            # GLUE (recharge, evapotranspiration, runoff, water levels)
            # Added in version 0.3.1 (see PR #184)
            grp.create_group('glue')

            # Hydrograph layout
            grp.create_group('layout')

            # Manual water level measurements
            mmeas = grp.create_group('manual')
            mmeas.create_dataset('Time', data=np.array([]), maxshape=(None,))
            mmeas.create_dataset('WL', data=np.array([]), maxshape=(None,))

            self.db.flush()

            print('New dataset created sucessfully')
        except Exception:
            print('Unable to save dataset to project db')
            del self.db['wldsets'][name]

        return WLDataFrameHDF5(grp)

    def del_wldset(self, name):
        del self.db['wldsets/%s' % name]

    # ---- Weather Dataset Handlers

    @property
    def wxdsets(self):
        return list(self.db['wxdsets'].keys())

    def get_wxdset(self, name):
        if name in self.wxdsets:
            return WXDataFrameHDF5(self.db['wxdsets/%s' % name])
        else:
            return None

    def add_wxdset(self, name, df):
        grp = self.db['wxdsets'].create_group(name)

        grp.attrs['filename'] = df['filename']
        grp.attrs['Station Name'] = df['Station Name']
        grp.attrs['Latitude'] = df['Latitude']
        grp.attrs['Longitude'] = df['Longitude']
        grp.attrs['Elevation'] = df['Elevation']
        grp.attrs['Province'] = df['Province']
        grp.attrs['Climate Identifier'] = df['Climate Identifier']

        grp.create_dataset('Time', data=df['Time'])
        grp.create_dataset('Year', data=df['Year'])
        grp.create_dataset('Month', data=df['Month'])
        grp.create_dataset('Day', data=df['Day'])
        grp.create_dataset('Tmax', data=df['Tmax'])
        grp.create_dataset('Tavg', data=df['Tavg'])
        grp.create_dataset('Tmin', data=df['Tmin'])
        grp.create_dataset('Ptot', data=df['Ptot'])
        grp.create_dataset('Rain', data=df['Rain'])
        grp.create_dataset('Snow', data=df['Snow'])
        grp.create_dataset('PET', data=df['PET'])

        grp.create_dataset('Missing Tmax', data=df['Missing Tmax'])
        grp.create_dataset('Missing Tmin', data=df['Missing Tmin'])
        grp.create_dataset('Missing Tavg', data=df['Missing Tavg'])
        grp.create_dataset('Missing Ptot', data=df['Missing Ptot'])

        grp_yrly = grp.create_group('yearly')
        for vbr in df['yearly'].keys():
            grp_yrly.create_dataset(vbr, data=df['yearly'][vbr])

        grp_mtly = grp.create_group('monthly')
        for vbr in df['monthly'].keys():
            grp_mtly.create_dataset(vbr, data=df['monthly'][vbr])

        grp_norm = grp.create_group('normals')
        for vbr in df['normals'].keys():
            grp_norm.create_dataset(vbr, data=df['normals'][vbr])

        print('New dataset created sucessfully')

        self.db.flush()

    def del_wxdset(self, name):
        del self.db['wxdsets/%s' % name]


class WLDataFrameHDF5(dict):
    """
    This is a wrapper around the h5py group that is used to store
    water level datasets. It mimick the structure of the DataFrame that
    is returned when loading water level dataset from an Excel file in
    reader_waterlvl module.
    """

    def __init__(self, dset, *args, **kwargs):
        super(WLDataFrameHDF5, self).__init__(*args, **kwargs)
        self.dset = dset

        # Make older datasets compatible with newer format :

        if 'Well ID' not in list(self.dset.attrs.keys()):
            # Added in version 0.2.1 (see PR #124).
            dset.attrs['Well ID'] = ""
            self.dset.file.flush()
        if 'Province' not in list(self.dset.attrs.keys()):
            # Added in version 0.2.1 (see PR #124).
            dset.attrs['Province'] = ""
            self.dset.file.flush()
        if 'glue' not in list(self.dset.keys()):
            # Added in version 0.3.1 (see PR #184)
            self.dset.create_group('glue')
            self.dset.file.flush()

    def __getitem__(self, key):
        if key in list(self.dset.attrs.keys()):
            return self.dset.attrs[key]
        else:
            return self.dset[key].value

    @property
    def name(self):
        return self.dset.name

    # ---- Manual measurents

    def set_wlmeas(self, time, wl):
        """Overwrite the water level measurements for this dataset."""
        try:
            self.dset['manual/Time'].resize(np.shape(time))
            self.dset['manual/Time'][:] = time
            self.dset['manual/WL'].resize(np.shape(wl))
            self.dset['manual/WL'][:] = wl
        except TypeError:
            del self.dset['manual']
            mmeas = self.dset.create_group('manual')
            mmeas.create_dataset('Time', data=time, maxshape=(None,))
            mmeas.create_dataset('WL', data=wl, maxshape=(None,))
        self.dset.file.flush()

    def get_wlmeas(self):
        """Get the water level measurements for this dataset."""
        grp = self.dset.require_group('manual')
        return grp['Time'].value, grp['WL'].value

    # ---- Master recession curve

    def set_mrc(self, A, B, peak_indx, time, recess):
        self.dset['mrc/params'][:] = (A, B)

        self.dset['mrc/peak_indx'].resize(np.shape(peak_indx))
        self.dset['mrc/peak_indx'][:] = np.array(peak_indx)

        self.dset['mrc/time'].resize(np.shape(time))
        self.dset['mrc/time'][:] = time

        self.dset['mrc/recess'].resize(np.shape(recess))
        self.dset['mrc/recess'][:] = recess

        self.dset['mrc'].attrs['exists'] = 1

        self.dset.file.flush()

        print(peak_indx)

    def mrc_exists(self):
        if 'mrc' not in list(self.dset.keys()):
            mrc = self.dset.create_group('mrc')
            mrc.attrs['exists'] = 0
            mrc.create_dataset('params', data=(0, 0), dtype='float64')
            mrc.create_dataset('peak_indx', data=np.array([]),
                               dtype='int16', maxshape=(None,))
            mrc.create_dataset('recess', data=np.array([]),
                               dtype='float64', maxshape=(None,))
            mrc.create_dataset('time', data=np.array([]),
                               dtype='float64', maxshape=(None,))
        return bool(self.dset['mrc'].attrs['exists'])

    # ---- Barometric response function

    def saved_brf(self):
        grp = self.dset.require_group('brf')
        return list(grp.keys())

    def brf_count(self):
        return len(list(self.dset['brf'].keys()))

    def get_brfAt(self, index):
        if index < self.brf_count():
            names = list(self.dset['brf'].keys())
            names = np.array(names).astype(int)
            names.sort()
            return str(names[index])
        else:
            return None

    def get_brf(self, name):
        grp = self.dset['brf'][name]
        return (grp['lag'].value, grp['A'].value, grp['err'].value,
                grp['date start'].value, grp['date end'].value)

    def save_brf(self, lag, A, err, date_start, date_end):
        if list(self.dset['brf'].keys()):
            idnum = np.array(list(self.dset['brf'].keys())).astype(int)
            idnum = np.max(idnum) + 1
        else:
            idnum = 1
        idnum = str(idnum)

        grp = self.dset['brf'].require_group(idnum)
        grp.create_dataset('lag', data=lag, dtype='float64')
        grp.create_dataset('A', data=A, dtype='float64')
        grp.create_dataset('err', data=err, dtype='float64')
        grp.create_dataset('date start', data=date_start, dtype='int16')
        grp.create_dataset('date end', data=date_end, dtype='int16')
        self.dset.file.flush()
        print('BRF results saved successfully')

    def del_brf(self, name):
        if name in list(self.dset['brf'].keys()):
            del self.dset['brf'][name]
            self.dset.file.flush()
            print('BRF %s deleted successfully' % name)
        else:
            print('BRF does not exist')

    def save_layout(self, layout):
        grp = self.dset['layout']
        for key in list(layout.keys()):
            if key == 'colors':
                grp_colors = grp.require_group(key)
                for color in layout['colors'].keys():
                    grp_colors.attrs[color] = layout['colors'][color]
            else:
                grp.attrs[key] = layout[key]

    def get_layout(self):
        if 'TIMEmin' not in self.dset['layout'].attrs.keys():
            return None

        layout = {}
        for key in list(self.dset['layout'].attrs.keys()):
            if key in ['legend_on', 'title_on', 'trend_line']:
                layout[key] = (self.dset['layout'].attrs[key] == 'True')
            else:
                layout[key] = self.dset['layout'].attrs[key]

        layout['colors'] = {}
        grp_colors = self.dset['layout'].require_group('colors')
        for key in list(grp_colors.attrs.keys()):
            layout['colors'][key] = grp_colors.attrs[key].tolist()

        return layout


class WXDataFrameHDF5(WXDataFrameBase):
    """
    This is a wrapper around the h5py group to read the weather data
    from the project.
    """
    def __init__(self, dataset, *args, **kwargs):
        super(WXDataFrameHDF5, self).__init__(*args, **kwargs)
        self.__load_dataset__(dataset)

    def __getitem__(self, key):
        if key in list(self.store.attrs.keys()):
            return self.store.attrs[key]
        elif key in ['normals', 'yearly', 'monthly']:
            x = {}
            for vrb in self.store[key].keys():
                x[vrb] = self.store[key][vrb].value
            if key == 'normals' and 'Period' not in x.keys():
                # This is needed for backward compatibility with
                # gwhat < 0.2.3 (see PR#142).
                x['Period'] = (np.min(self.store['Year']),
                               np.max(self.store['Year']))
            return x
        elif key == 'daily':
            vrbs = ['Year', 'Month', 'Day', 'Tmin', 'Tavg', 'Tmax',
                    'Rain', 'Snow', 'Ptot', 'PET']
            x = {}
            for vrb in vrbs:
                x[vrb] = self.store[vrb].value
            return x
        else:
            return self.store[key].value

    def __setitem__(self, key, value):
        return NotImplementedError

    def __iter__(self):
        return NotImplementedError

    def __len__(self, key):
        return NotImplementedError

    def __load_dataset__(self, dataset):
        """Saves the h5py dataset to the store."""
        self.store = dataset

    @property
    def name(self):
        return osp.basename(self.store.name)


if __name__ == '__main__':
    f = ("C:/Users/jsgosselin/GWHAT/"
         "gwhat/tests/@ new-prô'jèt!/@ new-prô'jèt!.gwt")
    pr = ProjetReader(f)
