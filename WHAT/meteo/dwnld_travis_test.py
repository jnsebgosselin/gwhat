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

from urllib.request import URLError, urlopen

import sys
import os
from os import getcwd, path, makedirs
from time import gmtime, sleep
import csv

# Third party imports :

import numpy as np

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QWidget, QMenu,
                             QToolButton, QGridLayout, QLabel, QCheckBox,
                             QFrame, QTextEdit, QPushButton, QFileDialog,
                             QMessageBox, QProgressBar)

# Local imports :
#
#import common.database as db
#from common import IconDB, QToolButtonNormal, QToolButtonSmall
#import common.widgets as myqt
#from meteo.search_weather_data import WeatherStationDisplayTable
#from meteo.search_weather_data import Search4Stations


# =============================================================================


class dwnldWeather(QWidget):
    """
    Test for Travis
    """

    ConsoleSignal = QSignal(str)

    def __init__(self, parent=None):
        super(dwnldWeather, self).__init__(parent)
