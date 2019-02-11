# -*- coding: utf-8 -*-

# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: third parties
from xlrd import xldate_as_tuple
from PyQt5.QtCore import QDate, QDateTime


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
