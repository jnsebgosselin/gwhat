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

from PySide import QtGui, QtCore
from PySide.QtGui import QIcon
from PySide.QtCore import QSize

dirname = os.path.dirname(os.path.realpath(__file__))


class IconDB():
    def __init__(self):
        self.iconSize = QSize(32, 32)
        self.iconSize2 = QSize(20, 20)

        self.master = QIcon(os.path.join(dirname, 'Icons', 'WHAT.png'))
        self.calc_brf = QIcon(os.path.join(dirname, 'Icons', 'start.png'))
        self.setup = QIcon(os.path.join(dirname, 'Icons', 'page_setup'))
        self.new_project = QIcon(
                os.path.join(dirname, 'Icons', 'new_project.png'))
        self.openFolder = QIcon(os.path.join(dirname, 'Icons', 'folder'))
        self.openFile = QIcon(os.path.join(dirname + '/Icons/open_file'))
        self.clear = QIcon(os.path.join(dirname, 'Icons', 'clear-search'))
        self.importFile = QIcon(os.path.join(dirname, 'Icons', 'open_project'))


class QToolButtonSmall(QtGui.QToolButton):

    def __init__(self, Qicon, *args, **kargs):
        super(QToolButtonSmall, self).__init__(*args, **kargs)
        self.setIcon(Qicon)
        self.setAutoRaise(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setIconSize(QSize(20, 20))
