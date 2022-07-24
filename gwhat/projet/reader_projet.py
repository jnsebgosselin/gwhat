# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

from __future__ import division, unicode_literals

# ---- Standard library imports
import csv
import os
import os.path as osp
from shutil import copyfile
from collections import namedtuple

# ---- Third party imports
import h5py
import numpy as np
import pandas as pd
import datetime

# ---- Local library imports
from gwhat.meteo.weather_reader import WXDataFrameBase, METEO_VARIABLES
from gwhat.projet.reader_waterlvl import WLDatasetBase, WLDataFrame
from gwhat.gwrecharge.glue import GLUEDataFrameBase
from gwhat.common.utils import save_content_to_file
from gwhat.utils.math import nan_as_text_tolist, calcul_rmse
from gwhat.utils.dates import xldates_to_datetimeindex, xldates_to_strftimes

INVALID_CHARS = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']


class ProjetReader(object):
    def __init__(self, filename):
        self.__db = None
        self.load_projet(filename)

    def __del__(self):
        self.close()

    @property
    def db(self):  # project data base
        return self.__db

    @property
    def filename(self):
        return self.db.filename

    @property
    def dirname(self):
        return os.path.dirname(self.filename)

    def load_projet(self, filename):
        """Open the hdf5 project file."""
        self.close()
        print("Loading project from '{}'... ".format(osp.basename(filename)),
              end='')
        try:
            if not osp.exists(osp.dirname(filename)):
                os.makedirs(osp.dirname(filename))
            self.__db = h5py.File(filename, mode='a')
            print('done')
        except Exception:
            self.__db = None
            print('failed')
            raise ValueError('Project file is not valid!')

        # For newly created project and backward compatibility.
        for key in ['name', 'author', 'created', 'modified', 'version']:
            if key not in list(self.db.attrs.keys()):
                self.db.attrs[key] = 'None'

        for key in ['latitude', 'longitude']:
            if key not in list(self.db.attrs.keys()):
                self.db.attrs[key] = 0

        for key in ['wldsets', 'wxdsets']:
            if key not in list(self.db.keys()):
                self.db.create_group(key)
            if 'last_opened' not in list(self.db[key].attrs.keys()):
                # Added in version 0.4.0 (see PR #267)
                self.db[key].attrs['last_opened'] = 'None'

    def close(self):
        """Close the project hdf5 file."""
        try:
            self.db.close()
            self.__db = None
        except AttributeError:
            # projet is None or already closed.
            pass

    def check_project_file(self):
        """Check to ensure that the project hdf5 file is not corrupt."""
        item_names = []
        try:
            self.__db.visit(item_names.append)
        except RuntimeError:
            return False
        else:
            return True

    def backup_project_file(self):
        """Copy the project hdf5 file in a file with a .bak extension."""
        if self.db is not None:
            filename = self.filename
            self.db.close()
            print("Creating a backup of the project hdf5 file... ", end='')
            try:
                copyfile(filename, filename + '.bak')
            except (OSError, PermissionError):
                print('failed')
                return False
            else:
                print('done')
                return True
            finally:
                self.load_projet(filename)

        try:
            copyfile(self.filename, bak_filename)
        except (OSError, PermissionError):
            print('failed')
            return False
        else:
            print('done')
            return True

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
        """
        Return a list of the names of all the water level datasets stored in
        the project hdf5 file.
        """
        return list(self.db['wldsets'].keys())

    def get_last_opened_wldset(self):
        """
        Return the name of the last opened water level dataset if any.
        """
        try:
            name = self.db['wldsets'].attrs['last_opened']
        except OSError:
            name = 'None'
        return None if name == 'None' else name

    def set_last_opened_wldset(self, name):
        """
        Set the name of the last opened water level dataset.
        """
        self.db['wldsets'].attrs['last_opened'] = name
        self.db.flush()

    def get_wldset(self, name):
        """
        Return the water level dataset corresponding to the provided name.
        """
        print("Getting wldset {}...".format(name), end=' ')
        if name in self.wldsets:
            self.set_last_opened_wldset(name)
            print('done')
            return WLDatasetHDF5(self.db['wldsets/%s' % name])
        else:
            print('failed')
            return None

    def add_wldset(self, name, df):
        """
        Add the water level dataset to the project hdf5 file.

        A dataset name must be at least one charater long and can't contain
        any of the following special characters: \\ / : * ? " < > |
        """
        if not is_dsetname_valid(name):
            raise ValueError("The name of the dataset is not valid.")

        try:
            grp = self.db['wldsets'].create_group(name)

            # Water level data
            grp.create_dataset(
                'Time',
                data=np.array(df['Time'], dtype=h5py.string_dtype()))
            # See http://docs.h5py.org/en/latest/strings.html as to why this
            # is necessary to do this in order to save a list of strings in
            # a dataset with h5py.

            grp.create_dataset('WL', data=np.copy(df['WL']))
            grp.create_dataset('BP', data=np.copy(df['BP']))
            grp.create_dataset('ET', data=np.copy(df['ET']))

            # Piezometric well info
            grp.attrs['filename'] = df['filename']
            grp.attrs['Well'] = df['Well']
            grp.attrs['Well ID'] = df['Well ID']
            grp.attrs['Latitude'] = df['Latitude']
            grp.attrs['Longitude'] = df['Longitude']
            grp.attrs['Elevation'] = df['Elevation']
            grp.attrs['Municipality'] = df['Municipality']
            grp.attrs['Province'] = df['Province']

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

            print('New dataset created sucessfully')
        except Exception as e:
            print('Unable to save dataset to project db because of the '
                  'following error:')
            print(e)
            del self.db['wldsets'][name]
        finally:
            self.db.flush()

        return WLDatasetHDF5(grp)

    def del_wldset(self, name):
        """Delete the specified water level dataset."""
        del self.db['wldsets/%s' % name]
        self.db.flush()

    # ---- Weather Dataset Handlers
    @property
    def wxdsets(self):
        """
        Return a list of the names of all the weather datasets stored in
        the project hdf5 file.
        """
        return list(self.db['wxdsets'].keys())

    def get_wxdsets_lat(self):
        """
        Return a list with the latitude coordinates of the weather datasets.
        """
        return [self.db['wxdsets/%s' % name].attrs['Latitude'] for
                name in self.wxdsets]

    def get_wxdsets_lon(self):
        """
        Return a list with the longitude coordinates of the weather datasets.
        """
        return [self.db['wxdsets/%s' % name].attrs['Longitude'] for
                name in self.wxdsets]

    def get_last_opened_wxdset(self):
        """
        Return the name of the last opened weather dataset if any.
        """
        try:
            name = self.db['wxdsets'].attrs['last_opened']
        except OSError:
            name = 'None'
        return None if name == 'None' else name

    def set_last_opened_wxdset(self, name):
        """
        Set the name of the last opened weather dataset.
        """
        self.db['wxdsets'].attrs['last_opened'] = name
        self.db.flush()

    def get_wxdset(self, name):
        """
        Return the weather dataset corresponding to the provided name.
        """
        print("Getting wxdset {}...".format(name), end=' ')
        if name in self.wxdsets:
            print('done')
            self.set_last_opened_wxdset(name)
            return WXDataFrameHDF5(self.db['wxdsets/%s' % name])
        else:
            print('failed')
            return None

    def add_wxdset(self, name, wxdset):
        """
        Add the weather dataset to the project hdf5 file.

        A dataset name must be at least one charater long and can't contain
        any of the following special characters: \\ / : * ? " < > |
        """
        if not is_dsetname_valid(name):
            raise ValueError("The name of the dataset is not valid.")
        grp = self.db['wxdsets'].create_group(name)

        # Save the metadata.
        for key, value in wxdset.metadata.items():
            grp.attrs[key] = value

        # Save time.
        strtimes = np.array(
            wxdset.strftime(), dtype=h5py.string_dtype())
        grp.create_dataset('Time', data=strtimes)
        # See http://docs.h5py.org/en/latest/strings.html as to why this
        # is necessary to do this in order to save a list of strings in
        # a dataset with h5py.

        # Save timeseries data
        for variable in METEO_VARIABLES:
            grp.create_dataset(
                variable, data=np.copy(wxdset.data[variable].values))

        # Save times where data was missing.
        for variable in METEO_VARIABLES:
            datetimeindex = wxdset.missing_value_indexes[variable]
            strtimes = np.array(
                datetimeindex.strftime("%Y-%m-%dT%H:%M:%S").values.tolist(),
                dtype=h5py.string_dtype()
                )
            grp.create_dataset(
                'Missing {}'.format(variable), data=strtimes)

        print('Dataset {} created sucessfully.'.format(name))
        self.db.flush()

    def del_wxdset(self, name):
        """Delete the specified weather dataset."""
        del self.db['wxdsets/%s' % name]
        self.db.flush()


class WLDatasetHDF5(WLDatasetBase):
    """
    This is a wrapper around the h5py group that is used to store
    water level datasets. It mimick the structure of the DataFrame that
    is returned when loading water level dataset from an Excel file in
    reader_waterlvl module.
    """

    def __init__(self, hdf5group, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__load_dataset__(hdf5group)

    def __load_dataset__(self, hdf5group):
        self.dset = hdf5group
        self._undo_stack = []

        # Make older datasets compatible with newer format.
        if isinstance(self.dset['Time'][0], (int, float)):
            # Time needs to be converted from Excel numeric dates
            # to ISO date strings (see PR #276).
            print('Saving time as ISO date strings instead of Excel dates...',
                  end=' ')
            strtimes = xldates_to_strftimes(self.dset['Time'])
            del self.dset['Time']
            self.dset.create_dataset('Time', data=strtimes)
            self.dset.file.flush()
            print('done')

        # Setup the WLDataFrame.
        columns = []
        data = []
        for col_name in ['Time', 'WL', 'BP', 'ET']:
            col_data = self[col_name]
            if len(col_data):
                data.append(col_data)
                columns.append(col_name)

        data = np.vstack(tuple(data)).transpose()
        columns = tuple(columns)
        self._dataf = WLDataFrame(data, columns)

        # Make older datasets compatible with newer format.
        if 'mrc' not in list(self.dset.keys()):
            # Setup the structure for the Master Recession Curve
            mrc = self.dset.create_group('mrc')
            mrc.attrs['exists'] = 0
            mrc.create_dataset('params', data=(np.nan, np.nan),
                               dtype='float64')
            mrc.create_dataset('peak_indx', data=np.array([]),
                               dtype='float64', maxshape=(None,))
            mrc.create_dataset('recess', data=np.array([]),
                               dtype='float64', maxshape=(None,))
            mrc.create_dataset('time', data=np.array([]),
                               dtype='float64', maxshape=(None,))
            self.dset.file.flush()
        if 'Well ID' not in list(self.dset.attrs.keys()):
            # Added in version 0.2.1 (see PR #124).
            self.dset.attrs['Well ID'] = ""
            self.dset.file.flush()
        if 'Province' not in list(self.dset.attrs.keys()):
            # Added in version 0.2.1 (see PR #124).
            self.dset.attrs['Province'] = ""
            self.dset.file.flush()
        if 'glue' not in list(self.dset.keys()):
            # Added in version 0.3.1 (see PR #184)
            self.dset.create_group('glue')
            self.dset.file.flush()
        if self.dset['mrc/peak_indx'].dtype != np.dtype('float64'):
            # We need to convert peak_indx data to the format used in
            # gwhat >= 0.5.1, where we store the mrc periods as a series of
            # xldates instead of time indexes. See jnsebgosselin/gwhat#370.
            print('Convert peak_inx values to the new format '
                  'used in gwhat >= 0.5.1.')

            peak_indx = self.dset['mrc/peak_indx'][...].astype(int)
            peak_indx = self.xldates[peak_indx]

            # The only way to do that in HDF5 is to delete the dataset and
            # create a new one with the right dtype.
            del self.dset['mrc/peak_indx']
            self.dset.file.flush()

            self.dset['mrc'].create_dataset(
                'peak_indx', data=np.array([]),
                dtype='float64', maxshape=(None,))
            self.dset['mrc/peak_indx'].resize(np.shape(peak_indx))
            self.dset['mrc/peak_indx'][:] = np.array(peak_indx)
            self.dset.file.flush()

    def __getitem__(self, key):
        if key in list(self.dset.attrs.keys()):
            return self.dset.attrs[key]
        elif key == 'Time':
            return self.dset['Time'].asstr()[...]
        else:
            return self.dset[key][...]

    @property
    def dirname(self):
        return os.path.dirname(self.dset.file.filename)

    @property
    def name(self):
        return osp.basename(self.dset.name)

    # ---- Water levels
    def commit(self):
        """Commit the changes made to the water level data to the project."""
        if self.has_uncommited_changes:
            self.dset['WL'][:] = np.copy(self.waterlevels)
            self.dset.file.flush()
            self._undo_stack = []
            print('Changes commited successfully.')

    # ---- Manual measurements
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
        return grp['Time'][...], grp['WL'][...]

    # ---- Master Recession Curve
    def set_mrc(self, A, B, periods, time, recess,
                std_err, r_squared, rmse):
        """Save the mrc results to the hdf5 project file."""
        self.dset['mrc/params'][:] = (A, B)

        periods = np.array(periods).flatten()
        self.dset['mrc/peak_indx'].resize(np.shape(periods))
        self.dset['mrc/peak_indx'][:] = np.array(periods)

        self.dset['mrc/time'].resize(np.shape(time))
        self.dset['mrc/time'][:] = time

        self.dset['mrc/recess'].resize(np.shape(recess))
        self.dset['mrc/recess'][:] = recess

        self.dset['mrc'].attrs['exists'] = 1
        self.dset['mrc'].attrs['std_err'] = std_err
        self.dset['mrc'].attrs['r_squared'] = r_squared
        self.dset['mrc'].attrs['rmse'] = rmse

        self.dset.file.flush()

    def get_mrc(self):
        """Return the mrc results stored in the hdf5 project file."""
        peak_indx = self['mrc/peak_indx'].copy()
        m = 2
        n = len(peak_indx) // m
        peak_indx = list(map(
            tuple, peak_indx[:n * m].reshape((n, m))
            ))
        coeffs = self['mrc/params'].tolist()

        mrc_data = {
            'params': namedtuple('Coeffs', ['A', 'B'])(*coeffs),
            'peak_indx': peak_indx,
            'time': self['mrc/time'].copy(),
            'recess': self['mrc/recess'].copy()}
        for key in ['std_err', 'r_squared', 'rmse']:
            try:
                mrc_data[key] = self.dset['mrc'].attrs[key]
            except KeyError:
                mrc_data[key] = None
        return mrc_data

    def mrc_exists(self):
        """Return whether a mrc results is saved in the hdf5 project file."""
        return bool(self.dset['mrc'].attrs['exists'])

    def save_mrc_tofile(self, filename):
        """Save the master recession curve results to a file."""
        if not filename.lower().endswith('.csv'):
            filename += '.csv'

        mrc_data = self.get_mrc()

        # Prepare the file header.
        fheader = []
        keys = ['Well', 'Well ID', 'Province', 'Latitude', 'Longitude',
                'Elevation', 'Municipality']
        for key in keys:
            fheader.append([key, self[key]])

        fheader.extend([
            [],
            ['∂h/∂t = -A * h + B'],
            ['A (1/day)', mrc_data['params'].A],
            ['B (m/day)', mrc_data['params'].B],
            []])

        labels = ['RMSE (m)', 'R-squared', 'S (m)']
        keys = ['rmse', 'r_squared', 'std_err']
        for label, key in zip(labels, keys):
            value = mrc_data[key]
            if value is None:
                fheader.append([label, "N/A"])
            else:
                fheader.append([label, "{:0.5f} m".format(value)])
        fheader.append([])
        fheader.append([['Observed and Predicted Water Level']])

        # Save the observed and simulated data to the CSV file.
        df = pd.DataFrame(
            np.vstack([self['WL'], self['mrc/recess']]).transpose(),
            columns=['h_obs(mbgs)', 'h_sim(mbgs)'],
            index=pd.to_datetime(self['Time']))
        df.index.name = 'Time'
        df.to_csv(filename)

        # Add the header to the CSV file.
        with open(filename, 'r') as csvfile:
            fdata = list(csv.reader(csvfile))
        with open(filename, 'w', encoding='utf8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
            writer.writerows(fheader + fdata)

    # ---- GLUE data
    def glue_idnums(self):
        """Return the id numbers of all the previously saved GLUE results"""
        return list(self.dset['glue'].keys())

    def glue_count(self):
        """Return the number of GLUE results saved in this dataset."""
        return len(self.glue_idnums())

    def save_glue(self, gluedf):
        """Save GLUE results in the project hdf file."""
        if list(self.dset['glue'].keys()):
            idnum = np.array(list(self.dset['glue'].keys())).astype(int)
            idnum = np.max(idnum) + 1
        else:
            idnum = 1
        idnum = str(idnum)

        grp = self.dset['glue'].create_group(idnum)
        save_dict_to_h5grp(grp, gluedf)
        self.dset.file.flush()
        print('GLUE results saved successfully')

    def get_glue(self, idnum):
        """Get GLUE results at idnum."""
        if idnum in self.glue_idnums():
            return GLUEDataFrameHDF5(self.dset['glue'][idnum])

    def get_glue_at(self, idx):
        """Return GLUE results stored at the specified index."""
        try:
            idnum = self.glue_idnums()[idx]
        except IndexError:
            return None
        else:
            return self.get_glue(idnum)

    def del_glue(self, idnum):
        """Delete GLUE results at idnum."""
        if idnum in self.glue_idnums():
            del self.dset['glue'][idnum]
            self.dset.file.flush()
            print('GLUE data %s deleted successfully' % idnum)
        else:
            print('GLUE data %s does not exist' % idnum)

    def clear_glue(self):
        """Delete all GLUE results from the dataset."""
        while self.glue_count():
            self.del_glue(self.glue_idnums()[0])

    # ---- Barometric response function
    def saved_brf(self):
        """
        Return the list of ids referencing to the BRF evaluations saved for
        this dataset.
        """
        grp = self.dset.require_group('brf')
        return list(grp.keys())

    def brf_count(self):
        """Return the number of BRF evaluation saved for this datased."""
        return len(list(self.dset['brf'].keys()))

    def save_brfperiod(self, period):
        """
        Save the specified period as a list containing a start and end date
        in the Excel numerical date format.
        """
        period = [float(val) for val in period]
        if len(period) != 2:
            raise ValueError("The size of the specified 'period' must be 2.")
        grp = self.dset.require_group('brf')
        grp.attrs['period'] = period
        self.dset.file.flush()

    def get_brfperiod(self):
        """
        Return a list with the start and end date of the last period
        saved by the user to evaluate the BRF.
        """
        grp = self.dset.require_group('brf')
        if 'period' not in list(grp.attrs.keys()):
            # Added in version 0.3.4 (see PR #240).
            return [None, None]
        else:
            return list(grp.attrs['period'])

    def get_brfname_at(self, index):
        if index < self.brf_count():
            names = list(self.dset['brf'].keys())
            names = np.array(names).astype(int)
            names.sort()
            return str(names[index])
        else:
            return None

    def get_brf(self, name):
        """
        Get the BRF results for the data stored at the specified name.
        """
        grp = self.dset['brf'][name]

        # Make older datasets compatible with newer format (see PR#).
        flush = False
        if 'err' in grp.keys():
            grp['sdA'] = grp['err']
            del grp['err']
            flush = True
        if 'SumA' not in grp.keys():
            grp['SumA'] = grp['A']
            del grp['A']
            flush = True
        if 'lag' in grp.keys():
            grp['Lag'] = grp['lag']
            del grp['lag']
            flush = True
        for key in ['date start', 'date end']:
            if key in grp.keys():
                grp.attrs[key] = (
                    datetime.datetime(*grp[key][...], 0).isoformat())
                del grp[key]
                flush = True
        if 'detrending' not in grp.attrs.keys():
            grp.attrs['detrending'] = ''
            flush = True
        if flush:
            self.dset.file.flush()

        # Cast the data into a pandas dataframe.
        keys = ['Lag', 'A', 'sdA', 'SumA', 'sdSumA', 'B',
                'sdB', 'SumB', 'sdSumB']
        dataf = pd.DataFrame({key: grp[key][...] for key in keys if
                              key in grp.keys()})

        # TODO: we should use pandas dataframe attrs to stock these values
        # instead, once this become a supported feature.
        # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html
        dataf.date_start = datetime.datetime.strptime(
            grp.attrs['date start'], "%Y-%m-%dT%H:%M:%S")
        dataf.date_end = datetime.datetime.strptime(
            grp.attrs['date end'], "%Y-%m-%dT%H:%M:%S")
        dataf.detrending = grp.attrs['detrending']

        return dataf

    def save_brf(self, dataf, date_start, date_end, detrending=None):
        """
        Save the BRF results.
        """
        print('Saving BRF results...', end=' ')
        # Create a new h5py group to save the data.
        if list(self.dset['brf'].keys()):
            idnum = np.array(list(self.dset['brf'].keys())).astype(int)
            idnum = np.max(idnum) + 1
        else:
            idnum = 1
        idnum = str(idnum)
        grp = self.dset['brf'].require_group(idnum)

        # Save the data in the h5py group.
        for column in dataf.columns:
            grp.create_dataset(
                column, data=dataf[column].values, dtype='float64')
        grp.attrs['date start'] = date_start.isoformat()
        grp.attrs['date end'] = date_end.isoformat()
        grp.attrs['detrending'] = {
            True: 'Yes', False: 'No', None: ''}[detrending]

        self.dset.file.flush()
        print('done')

    def del_brf(self, name):
        """Delete the BRF evaluation saved with the specified name."""
        if name in list(self.dset['brf'].keys()):
            del self.dset['brf'][name]
            self.dset.file.flush()
            print('BRF %s deleted successfully' % name)
        else:
            print('BRF does not exist')

    def export_brf_to_csv(self, filename, index):
        """
        Export the BRF results saved at the specified index in a CSV or
        Excel file.
        """
        databrf = self.get_brf(self.get_brfname_at(index))
        databrf.insert(0, 'LagNo', databrf.index.astype(int))

        brf_date_start = databrf.date_start.strftime(format='%d/%m/%y %H:%M')
        brf_date_end = databrf.date_end.strftime(format='%d/%m/%y %H:%M')

        nbr_bp_lags = len(databrf['SumA'].dropna(inplace=False)) - 1
        nbr_et_lags = ('N/A' if 'SumB' not in databrf.columns else
                       len(databrf['SumB'].dropna(inplace=False)) - 1)

        fcontent = [
            ['Well Name :', self['Well']],
            ['Well ID :', self['Well ID']],
            ['Latitude :', self['Latitude']],
            ['Longitude :', self['Longitude']],
            ['Elevation :', self['Elevation']],
            ['Municipality :', self['Municipality']],
            ['Province :', self['Province']],
            [],
            ['BRF Start Time :', brf_date_start],
            ['BRF End Time :', brf_date_end],
            ['Number of BP Lags :', nbr_bp_lags],
            ['Number of ET Lags :', nbr_et_lags],
            ['Developed with detrending :', databrf.detrending],
            []
            ]
        fcontent.append(list(databrf.columns))
        fcontent.extend(nan_as_text_tolist(databrf.values))

        save_content_to_file(filename, fcontent)

    # ---- Hydrograph layout
    def save_layout(self, layout):
        """Save the layout in the project hdf5 file."""
        grp = self.dset['layout']
        for key in list(layout.keys()):
            if key == 'colors':
                grp_colors = grp.require_group(key)
                for color in layout['colors'].keys():
                    grp_colors.attrs[color] = layout['colors'][color]
            else:
                if isinstance(layout[key], type(None)):
                    grp.attrs[key] = '__None__'
                elif isinstance(layout[key], bool):
                    grp.attrs[key] = '__' + str(layout[key]) + '__'
                else:
                    grp.attrs[key] = layout[key]
        self.dset.file.flush()

    def get_layout(self):
        """Return the layout dict that is saved in the project hdf5 file."""
        if 'TIMEmin' not in self.dset['layout'].attrs.keys():
            return None
        layout = {}
        for key in list(self.dset['layout'].attrs.keys()):
            layout[key] = self.dset['layout'].attrs[key]
            if layout[key] == '__None__':
                layout[key] = None
            elif layout[key] == '__True__':
                layout[key] = True
            elif layout[key] == '__False__':
                layout[key] = False

        layout['colors'] = {}
        grp_colors = self.dset['layout'].require_group('colors')
        for key in list(grp_colors.attrs.keys()):
            layout['colors'][key] = grp_colors.attrs[key].tolist()

        keys = list(layout.keys())
        if 'meteo_on' not in keys:
            # Added in version 0.3.2 (see PR #201)
            layout['meteo_on'] = True
        if 'glue_wl_on' not in keys:
            # Added in version 0.3.2 (see PR #202)
            layout['glue_wl_on'] = False
        if 'mrc_wl_on' not in keys:
            # Added in version 0.3.3 (see PR #225)
            layout['mrc_wl_on'] = False
        if 'figframe_lw' not in keys:
            # Added in version 0.3.3 (see PR #228)
            layout['figframe_lw'] = 0

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
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self, key):
        raise NotImplementedError

    def __load_dataset__(self, dataset: h5py.Group):
        """
        Load and format the data from the h5py group.

        Parameters
        ----------
        dataset : h5py.Group
            The h5py group containing the data and metadata of the weather
            dataset.
        """
        self._dataset = dataset

        # Make older datasets compatible with newer format.
        if isinstance(dataset['Time'][0], (int, float)):
            # Time needs to be converted from Excel numeric dates
            # to ISO date strings (see jnsebgosselin/gwhat#297).
            print('Saving time as ISO date strings instead of Excel dates...',
                  end=' ')
            strtimes = xldates_to_strftimes(dataset['Time'])
            del dataset['Time']
            dataset.create_dataset('Time', data=strtimes)
            dataset.file.flush()
            print('done')
        if 'Location' not in list(dataset.attrs.keys()):
            # Added in version 0.4.0 (see jnsebgosselin/gwhat#297).
            if 'Province' in dataset.attrs.keys():
                dataset.attrs['Location'] = dataset.attrs['Province']
                del dataset.attrs['Province']
            else:
                dataset.attrs['Location'] = ''
            dataset.file.flush()
        if 'Station ID' not in list(dataset.attrs.keys()):
            # Added in version 0.4.0 (see jnsebgosselin/gwhat#297).
            if 'Climate Identifier' in dataset.attrs.keys():
                dataset.attrs['Station ID'] = (
                    dataset.attrs['Climate Identifier'])
                del dataset.attrs['Climate Identifier']
            else:
                dataset.attrs['Station ID'] = ''
            dataset.file.flush()
        for key in ['yearly', 'monthly', 'normals', 'Period']:
            # Removed in version 0.4.0 (see jnsebgosselin/gwhat#297).
            if key in dataset.keys():
                del dataset[key]
                print(("Removing '{}' from project data because it is "
                       "not needed anymore.").format(key))
        for variable in METEO_VARIABLES:
            key = 'Missing {}'.format(variable)
            if (key in dataset.keys() and len(dataset[key]) > 0 and
                    isinstance(dataset[key][0], (int, float))):
                print(("Saving missing {} data time as ISO date strings "
                       "instead of Excel dates...").format(variable),
                      end=' ')
                # The missing data were previously saved as a list
                # of xldate periods separated by a nan value. To convert to
                # the new format, we need to expand the datetimes values
                # within each period and remove the nan values.
                try:
                    missing_idx = dataset[key][:-1]
                    missing_idx = np.reshape(
                        missing_idx, (len(missing_idx) // 3, 3))[:, 1:]

                    restruct_missing_idx = []
                    for period in missing_idx:
                        restruct_missing_idx.extend(np.arange(*period))

                    del dataset[key]
                except ValueError:
                    pass
                else:
                    strtimes = xldates_to_strftimes(restruct_missing_idx)
                    dataset.create_dataset(key, data=strtimes)
                dataset.file.flush()
                print('done')

        # Get the metadata.
        for key in dataset.attrs.keys():
            self.metadata[key] = dataset.attrs[key]

        # Create a pandas dataframe containing all weather variables.
        self.data = pd.DataFrame(
            [],
            columns=METEO_VARIABLES,
            index=pd.to_datetime(
                dataset['Time'].asstr()[...],
                infer_datetime_format=True)
            )
        for variable in METEO_VARIABLES:
            self.data[variable] = np.copy(dataset[variable])

        # Get and format the missing value datetime indexes.
        self.missing_value_indexes = {}
        for variable in METEO_VARIABLES:
            key = 'Missing {}'.format(variable)
            if key in dataset.keys():
                self.missing_value_indexes[variable] = pd.to_datetime(
                    dataset[key].asstr()[...], infer_datetime_format=True)

    @property
    def name(self):
        return osp.basename(self._dataset.name)


class GLUEDataFrameHDF5(GLUEDataFrameBase):
    """
    This is a wrapper around the h5py group to read the GLUE results
    from the project.
    """

    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__load_data__(data)

    def __getitem__(self, key):
        """Return the value saved in the store at key."""
        return self.store[key]

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __load_data__(self, glue_h5grp):
        """Saves the h5py glue data to the store."""
        self.store = load_dict_from_h5grp(glue_h5grp)


def is_dsetname_valid(dsetname):
    """
    Check if the dataset name respect the established guidelines to avoid
    problem with the hdf5 format.
    """
    return (dsetname != '' and
            not any(char in dsetname for char in INVALID_CHARS))


def make_dsetname_valid(dsetname):
    """Replace all invalid characters in the name by an underscore."""
    for char in INVALID_CHARS:
        dsetname = dsetname.replace(char, '_')
    return dsetname


def save_dict_to_h5grp(h5grp, dic):
    """
    Save the content of a dictionay recursively in a hdf5.
    Based on answers provided at
    https://codereview.stackexchange.com/questions/120802
    """
    for key, item in dic.items():
        if isinstance(item, dict):
            save_dict_to_h5grp(h5grp.require_group(key), item)
        else:
            h5grp.create_dataset(key, data=item)


def load_dict_from_h5grp(h5grp):
    """
    Retrieve the content of a hdf5 group and organize it in a dictionary.
    Based on answers provided at
    https://codereview.stackexchange.com/questions/120802
    """
    dic = {}
    for key, item in h5grp.items():
        if isinstance(item, h5py._hl.dataset.Dataset):
            values = item[...]
            try:
                len(values)
            except TypeError:
                values = values.item()
            dic[key] = values
        elif isinstance(item, h5py._hl.group.Group):
            dic[key] = load_dict_from_h5grp(item)
    return dic


if __name__ == '__main__':
    fname = ("C:\\Users\\User\\gwhat\\Projects\\Example\\Example.gwt")
    # fname = ("D:\\Data\\Guidel\\Guidel.gwt")
    project = ProjetReader(fname)
    print(project.wxdsets)

    wxdset = project.get_wxdset('Marieville')
    wldset = project.get_wldset('3040002_15min')
    # missing_idx = wxdset.missing_value_indexes['Tmax']

    project.db.close()
