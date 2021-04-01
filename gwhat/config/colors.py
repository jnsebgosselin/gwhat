# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard imports
import os
import os.path as osp
import csv
from collections import OrderedDict

# ---- Third party imports
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt, QObject

# ---- Local imports
from gwhat.config.main import CONFIG_DIR
from gwhat.common.utils import save_content_to_csv


class ColorsManager(QObject):
    def __init__(self):
        super().__init__()
        self.reset_defaults()
        self.load_colors()

    @property
    def rgb(self):
        rgb = OrderedDict()
        for key in self.RGB.keys():
            rgb[key] = [x / 255 for x in self.RGB[key]]
        return rgb

    def keys(self):
        return list(self.RGB.keys())

    def reset_defaults(self):
        """Reset the color settings to default values."""
        self.RGB = OrderedDict()
        self.RGB['Tair'] = [255, 212, 212]
        self.RGB['Rain'] = [23, 52, 88]
        self.RGB['Snow'] = [165, 165, 165]
        self.RGB['WL solid'] = [45, 100, 167]
        self.RGB['WL data'] = [204, 204, 204]
        self.RGB['WL obs'] = [255, 0, 0]

        self.labels = OrderedDict()
        self.labels['Tair'] = 'Air Temperature'
        self.labels['Rain'] = 'Rain'
        self.labels['Snow'] = 'Snow'
        self.labels['WL solid'] = 'Water Level (solid line)'
        self.labels['WL data'] = 'Water Level (data dots)'
        self.labels['WL obs'] = 'Water Level (man. obs.)'

    def load_colors(self):
        """Load the color settings."""
        filename = osp.join(CONFIG_DIR, 'colors.txt')
        if not os.path.exists(filename):
            self.save_colors()
        else:
            with open(filename, 'r') as f:
                reader = list(csv.reader(f, delimiter=','))

            for row in reader:
                self.RGB[row[0]] = [int(x) for x in row[1:]]

    def save_colors(self):
        """Save the color settings."""
        filename = osp.join(CONFIG_DIR, 'colors.txt')
        fcontent = []
        for key in self.RGB.keys():
            fcontent.append([key])
            fcontent[-1].extend(self.RGB[key])
        save_content_to_csv(filename, fcontent)
