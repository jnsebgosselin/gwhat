# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------


# ---- Third party imports
import h5py
import numpy as np
import pandas as pd
import xlrd
from xlrd import xldate_as_tuple
from xlrd.xldate import xldate_as_datetime
from PyQt5.QtCore import QDate, QDateTime


def format_time_data(self, timedata):
    """
    Format a numpy array containing time data, either in a string or Excel
    numeric format, and return a pandas datetime index.
    """
    datetimes = pd.DatetimeIndex([])
    try:
        # We first assume that the dates are stored in the
        # Excel numeric format.
        timedata = timedata.astype('float64', errors='raise')
    except ValueError:
        try:
            # Try converting the strings to datetime objects.
            # The format of the datetime strings must be
            # "%Y-%m-%d %H:%M:%S"
            datetimes = pd.to_datetime(timedata, infer_datetime_format=True)
        except ValueError:
            print('WARNING: the dates are not formatted correctly.')
    else:
        try:
            # Try converting the Excel numeric dates to pandas
            # datetime objects.
            datetimes = pd.to_datetime(datetimes.apply(
                lambda date: xlrd.xldate.xldate_as_datetime(date, 0)))
        except Exception:
            print('Warning: the dates are not formatted correctly.')
    return datetimes


def datetimeindex_to_xldates(datetimeindex):
    """
    Convert a datetime index to a numpy array of Excel numerical date format.
    """
    timedeltas = datetimeindex - xldate_as_datetime(4000, 0)
    xldates = timedeltas.total_seconds() / (3600 * 24) + 4000
    return xldates.values


def xldates_to_datetimeindex(xldates):
    """
    Format a list or numpy array of Excel numeric dates into a
    pandas datetime index.
    """
    return pd.to_datetime(
        [xlrd.xldate.xldate_as_datetime(xldate, 0) for xldate in xldates])


def xldates_to_strftimes(xldates):
    """
    Format a a list or numpy array of Excel numeric dates into a numpy array
    of ISO date strings that can be saved in a hdf5 file.
    """
    dtimeindex = xldates_to_datetimeindex(xldates)
    return np.array(
        dtimeindex.strftime("%Y-%m-%dT%H:%M:%S").values.tolist(),
        dtype=h5py.special_dtype(vlen=str)
        )


def qdate_from_xldate(xldate, datemode=0):
    """
    Conver an numerical Excel date to a QDate object

    A value of 0 is used of the workbook was created in Windows (1900-based),
    while a value of 1 is used if it was created on macOS (1904-based).
    """
    date_tuple = xldate_as_tuple(xldate, datemode)
    return QDate(date_tuple[0], date_tuple[1], date_tuple[2])


def qdatetime_from_xldate(xldate, datemode=0):
    """
    Conver an numerical Excel date to a QDateTime object

    A value of 0 is used of the workbook was created in Windows (1900-based),
    while a value of 1 is used if it was created on macOS (1904-based).
    """
    date_tuple = xldate_as_tuple(xldate, datemode)
    return QDateTime(date_tuple[0], date_tuple[1], date_tuple[2],
                     date_tuple[3], date_tuple[4])
