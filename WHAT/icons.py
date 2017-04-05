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

# STANDARD LIBRARY IMPORTS :

import os

# THIRD PARTY IMPORTS :

from PySide.QtGui import QIcon
from PySide.QtCore import QSize

dirname = os.path.dirname(os.path.realpath(__file__))


class IconDB():
    def __init__(self):
        self.iconSize = QSize(32, 32)
        self.iconSize2 = QSize(20, 20)

        self.master = QIcon(dirname + '/Icons/WHAT')
        self.calc_brf = QIcon(dirname + '/Icons/start')
        self.setup = QIcon(dirname + '/Icons/page_setup')
        self.new_project = QIcon(dirname + '/Icons/new_project.png')
        self.openFolder = QIcon(dirname + '/Icons/folder')
        self.openFile = QIcon(dirname + '/Icons/open_file')
        self.clear = QIcon(dirname + '/Icons/clear-search')
        self.importFile = QIcon(dirname + '/Icons/open_project')

