# -*- coding: utf-8 -*-
"""
Copyright 2014-2016 Jean-Sebastien Gosselin
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

dirname = os.path.dirname(os.path.realpath(__file__))


class IconDB():
    def __init__(self):
        self.master = QIcon(dirname + '/Icons/WHAT')
        self.calc_brf = QIcon(dirname + '/Icons/start')
        self.setup = QIcon(dirname + '/Icons/page_setup')
